from threading import Timer

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pandas as pd
import sys
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import numpy as np

class Correlogram(QWidget):

    # the annotation window when a point is selected
    annot = None

    def __init__(self, parent, database):
        super(Correlogram, self).__init__()
        self.parent = parent
        self.database = database

        # the Visualization itself with scatterplot as the lower section and
        # kernal density plots as the uper section
        self.figure = sns.PairGrid(self.database, dropna=True)
        self.figure.map_upper(sns.kdeplot)
        self.figure.map_diag(sns.histplot)
        self.figure.map_lower(sns.scatterplot)

        # put the vis on a canvas in order for it to be shown
        self.vis = FigureCanvas(self.figure.fig)
        # on click select a point
        self.vis.mpl_connect('button_press_event', self.onclick)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vis)
        self.setLayout(self.layout)

    # on click select a point
    def onclick(self, event):
        for y in range(len(self.figure.axes)):
            for x in range(len(self.figure.axes[y])):
                # first select the correct plot
                if self.figure.axes[y][x] == event.inaxes:
                    # get all data on that axes
                    data = self.database[[self.figure.axes[len(self.figure.axes)-1][x].get_xlabel(),
                                          self.figure.axes[y][0].get_ylabel()]].values
                    # get the point closesed to the click point
                    idx = np.nanargmin(((data - (event.xdata, event.ydata))**2).sum(axis = -1))
                    point = data[idx]
                    eDatabase = self.parent.getDatabase()
                    fDatabase = eDatabase[ eDatabase[self.figure.axes[len(self.figure.axes)-1][x].get_xlabel()] == point[0] ]
                    fDatabase = fDatabase[ fDatabase[self.figure.axes[y][0].get_ylabel()] == point[1] ]
                    if len(fDatabase) > 0:
                        # get the data of the point
                        dataPoint = fDatabase.iloc[0,:].dropna()
                        # give the parent the highlighted point in order for the connection interaction to work
                        self.parent.setHighlight(dataPoint)
                        dstring = ""
                        # put all the data into a string
                        for col in dataPoint.index:
                            dstring += col + ": " + str(dataPoint[[col]]) + "\n"

                        # make the annotation
                        if self.annot is not None:
                            self.annot.set_visible(False)
                        self.annot = self.figure.axes[y][x].annotate(dstring,xy=point, ha = 'right',
                            xytext = (-20, 20), textcoords = 'offset points', va = 'bottom',
                            bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                            arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0')
                            )
                        self.annot.set_visible(True)
                        # redraw the vis
                        self.vis.draw()

class Barchart(QWidget):
    highlight = None
    xAxesValue = None
    yAxesValue = None
    minY = 0
    maxY = 0
    cValue = "deep"
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    colorSchemes = ["deep", "muted", "bright", "pastel", "dark", "colorblind"]

    def __init__(self, parent, database, highlight):
        super(Barchart, self).__init__()
        self.parent = parent
        self.database = database

        # get all possible attributes for the x axis
        rowList = []
        for col in database.columns:
            rowList.append(col)

        # get all possible attributes for the y axis
        newdf = database.select_dtypes(include=self.numerics)
        colList = []
        for col in newdf.columns:
            colList.append(col)

        # get min and max value of the y axis
        self.minY = self.database[colList[0]].min()
        self.maxY = self.database[colList[0]].max()

        self.minYLabel = QLabel("Set the minimum Y value")

        self.minYslider = QSlider(Qt.Horizontal)
        self.minYslider.valueChanged[int].connect(self.setMinYValue)
        self.minYslider.sliderReleased.connect(self.changeYRange)
        self.minYslider.setMinimum(int(self.minY))
        self.minYslider.setMaximum(int(self.maxY))
        self.minYslider.setValue(self.minY)

        self.maxYLabel = QLabel("Set the maximum Y value")

        self.maxYslider = QSlider(Qt.Horizontal)
        self.maxYslider.valueChanged[int].connect(self.setMaxYValue)
        self.maxYslider.sliderReleased.connect(self.changeYRange)
        self.maxYslider.setMinimum(self.minY)
        self.maxYslider.setMaximum(self.maxY)
        self.maxYslider.setValue(self.maxY)

        self.orderLabel = QLabel("Change the order of the bars.")

        self.comboBoxArrangement = QComboBox()
        self.comboBoxArrangement.addItems(["default","ascending","descending"])
        self.comboBoxArrangement.currentIndexChanged.connect(self.setOValue)

        self.colorEncodingLabel = QLabel("Change the color encoding.")

        self.comboBoxColor = QComboBox()
        self.comboBoxColor.addItems(self.colorSchemes)
        self.comboBoxColor.currentIndexChanged.connect(self.setCValue)

        self.boxLabelX = QLabel("Change the x-Axis.")

        self.comboBoxX = QComboBox()
        self.comboBoxX.addItems(rowList)
        self.comboBoxX.currentIndexChanged.connect(self.setXValue)

        self.boxLabelY = QLabel("Change the y-Axis.")

        self.comboBoxY = QComboBox()
        self.comboBoxY.addItems(colList)
        self.comboBoxY.currentIndexChanged.connect(self.setYValue)

        # setup all vis that should go on the blue screen
        self.parent.addOptions([self.minYLabel, self.minYslider,
                                self.maxYLabel, self.maxYslider,
                                self.orderLabel, self.comboBoxArrangement,
                                self.colorEncodingLabel, self.comboBoxColor,
                                self.boxLabelX, self.comboBoxX,
                                self.boxLabelY, self.comboBoxY])

        self.xAxesValue = self.comboBoxX.currentText()
        self.yAxesValue = self.comboBoxY.currentText()

        # if something is highlighted take it over
        if not highlight is None:
            self.highlight = highlight[self.xAxesValue]

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(1,1,1)
        # the rotation of the labels came from https://stackabuse.com/rotate-axis-labels-in-matplotlib/
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(90)
        # make the vis
        try:
            sns.barplot(data=self.database, x=self.xAxesValue, y=self.yAxesValue, palette=self.cValue, ax=self.ax)
        except ValueError:
            print("Contains no valid data")
        self.vis = FigureCanvas(self.fig)
        self.vis.mpl_connect('button_press_event', self.onclick)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vis)
        self.setLayout(self.layout)
        self.update()

    def setMinYValue(self, value):
        self.minY = value
        if self.minY > self.maxY:
            self.minY = self.maxY
            self.minYslider.setValue(self.minY)

    def setMaxYValue(self, value):
        self.maxY = value
        if self.minY > self.maxY:
            self.maxY = self.minY
            self.maxYslider.setValue(self.maxY)

    def changeYRange(self):
        # updates the vis based on the new y range
        self.database = self.parent.getFilteredDatabase()
        self.database = self.database[self.database[self.yAxesValue] >= self.minY]
        self.database = self.database[self.database[self.yAxesValue] <= self.maxY]
        self.update()

    def setOValue(self, state=None):
        # change the arrangement of the data
        oValue = self.comboBoxArrangement.currentText()
        if oValue == "default":
            self.database = self.parent.getFilteredDatabase()
        elif oValue == "ascending":
            self.database.sort_values(by=self.yAxesValue, inplace=True)
        elif oValue == "descending":
            self.database.sort_values(by=self.yAxesValue, ascending=False,inplace=True)
        self.update()

    def setCValue(self, state=None):
        # set the color palette
        self.cValue = self.comboBoxColor.currentText()
        self.update()

    def setXValue(self, state=None):
        self.xAxesValue = self.comboBoxX.currentText()
        self.update()

    def setYValue(self, state=None):
        self.yAxesValue = self.comboBoxY.currentText()
        self.update()

    def update(self):
        self.ax.clear()
        self.ax.set_ylim(self.minY, self.maxY)
        color_map = ['grey' if value != self.highlight else 'red' for index, value in self.database[self.xAxesValue].items()]
        try:
            if self.highlight is None:
                sns.barplot(data=self.database, x=self.xAxesValue, y=self.yAxesValue, palette=self.cValue, ax=self.ax)
            else:
                sns.barplot(data=self.database, x=self.xAxesValue, y=self.yAxesValue, palette=color_map,ax=self.ax)
        except ValueError:
            print("Contains no valid data")
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(90)
        self.vis.draw()

    def onclick(self, event):
        if event is not None:
            idx = round(event.xdata)
            hl = self.database[self.xAxesValue].dropna().unique()
            if not hl is None:
                hl = hl[idx]
                if self.highlight == hl:
                    self.highlight = None
                else:
                    self.highlight = hl
                    self.parent.setHighlight(self.highlight)
                self.update()

class Heatmap(QWidget):

    def __init__(self, parent, database, highlight=None):
        super(Heatmap, self).__init__()
        self.parent = parent
        self.database = database.select_dtypes([np.number])
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(1,1,1)
        # the rotation of the labels came from https://stackabuse.com/rotate-axis-labels-in-matplotlib/
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(90)
        sns.heatmap(data=self.database, ax=self.ax, annot=True)
        for lab, annot in zip(self.ax.get_yticklabels(), self.ax.texts):
            text =  lab.get_text()
            if highlight is not None and text in highlight: # lets highlight row 2
                # set the properties of the ticklabel
                lab.set_weight('bold')
                lab.set_size(20)
                lab.set_color('purple')
                # set the properties of the heatmap annot
                annot.set_weight('bold')
                annot.set_color('purple')
                annot.set_size(20)
        self.vis = FigureCanvas(self.fig)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vis)
        self.setLayout(self.layout)

class Table(QWidget):

    timer = None
    prevSelected = None

    def __init__(self, parent, database):
        super(Table, self).__init__()
        self.parent = parent
        self.database = database
        # setup vis
        self.vis = QTableWidget(self)
        self.vis.setRowCount(self.database.shape[0])
        self.vis.setColumnCount(self.database.shape[1])
        for x in range(self.database.shape[0]):
            for y in range(self.database.shape[1]):
                column_name = self.database.columns[y]
                self.vis.setItem(x,y, QTableWidgetItem(str(self.database.loc[x,column_name])))
        self.vis.setHorizontalHeaderLabels(self.database.columns)
        self.vis.itemSelectionChanged.connect(lambda: self.on_table_click())

        # the data will be filtered everytime you select something so this resets
        # everything
        self.resetBtn = QPushButton("Reset the selected data")
        self.resetBtn.clicked.connect(self.reset)

        # the thing to select which attribute to filter
        self.comboBox = QComboBox()
        self.comboBox.setStyleSheet("QListWidget {background : white}")
        self.comboBox.currentIndexChanged.connect(self.setOValue)

        # the widget that contains all possible values on which you can filter out
        # these values are the unique values of the selected attribute
        self.listwidget = QListWidget()
        for attr in self.database.columns:
            if self.prevSelected is None:
                self.prevSelected = attr
            self.comboBox.addItem(attr)

        # code from https://stackoverflow.com/questions/54119933/pyqt5-list-widget-programmatically-select-all-items helped with the multiple selection
        self.listwidget.setStyleSheet("QListWidget {background : white}")
        self.listwidget.setSelectionMode(QAbstractItemView.MultiSelection)
        for uni in self.database[self.prevSelected].unique():
            self.listwidget.addItem(uni)

        # update blue screen
        self.parent.addOptions([self.resetBtn, self.comboBox, self.listwidget])

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vis)
        self.setLayout(self.layout)

    def on_table_click(self):
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(0.5, self.select, [])
        self.timer.start()

    def select(self):
        selectedRows = []
        selectedColumns=[]
        for index in self.vis.selectedIndexes():
            if not index.row() in selectedRows:
                selectedRows.append(index.row())
            if not index.column() in selectedColumns:
                selectedColumns.append(index.column())
        self.reset()
        self.parent.setFilteredData(self.database.iloc[selectedRows, selectedColumns])

    def setOValue(self, state=None):
        #filters based on selection
        selectedList = []
        for item in self.listwidget.selectedItems():
            selectedList.append(item.text())
        database = self.database[self.database[self.prevSelected].isin(selectedList)].dropna()
        database = database[database[self.prevSelected].notna()]
        #self.parent.setFilteredData(self.database)
        self.listwidget.clear()
        database = self.parent.getDatabase()
        for uni in database[self.comboBox.currentText()].unique():
            self.listwidget.addItem(str(uni))
        self.prevSelected = self.comboBox.currentText()

    def reset(self, state=None):
        self.database = self.parent.getDatabase()

class Window(QMainWindow):

    # current displayed vis
    vis = None

    # entire loaded database
    database = None

    # database filtered by the selection of table vis
    filteredData = None

    # highlighted point
    highlightedIdxs = None

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Hello")
        self.showFullScreen();

        self.UiComponents()

        self.show()

    def UiComponents(self):
        self.leftWidget = QWidget()
        self.leftWidget.setStyleSheet("QWidget {background : lightblue}")
        p0 = self.leftWidget.sizePolicy()
        p0.setHorizontalStretch(1)
        self.leftWidget.setSizePolicy(p0)

        leftLayout = QVBoxLayout()
        self.leftWidget.setLayout(leftLayout)

        self.rightWidget = QWidget()
        self.rightWidget.setGeometry(420, 0, 1500, 1080)
        p1 = self.rightWidget.sizePolicy()
        p1.setHorizontalStretch(4)
        self.rightWidget.setSizePolicy(p1)

        rightLayout = QVBoxLayout()
        self.rightWidget.setLayout(rightLayout)

        openAction = QAction('&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.openFileNameDialog)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        vis1Action = QAction('Correlogram', self)
        vis1Action.triggered.connect(lambda: self.setWidget("Correlogram"))

        vis2Action = QAction('Barchart', self)
        vis2Action.triggered.connect(lambda: self.setWidget("Barchart"))

        vis3Action = QAction('Heatmap', self)
        vis3Action.triggered.connect(lambda: self.setWidget("Heatmap"))

        vis4Action = QAction('Table', self)
        vis4Action.triggered.connect(lambda: self.setWidget("Table"))

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        visMenu = menubar.addMenu('&Visualization')
        visMenu.addAction(vis1Action)
        visMenu.addAction(vis2Action)
        visMenu.addAction(vis3Action)
        visMenu.addAction(vis4Action)

        layout = QHBoxLayout()
        layout.addWidget(self.leftWidget)
        layout.addWidget(self.rightWidget)
        main = QWidget()
        main.setLayout(layout)
        self.setCentralWidget(main)

    def setWidget(self, widget):
        # here you can change between vis
        # for every vis first remove the old vis then add the new
        if self.database is not None:
            if widget == "Correlogram":
                self.removeOptions()
                if self.vis:
                    self.rightWidget.layout().removeWidget(self.vis)
                    self.vis.deleteLater()
                self.vis = Correlogram(self, self.filteredData.copy())
                self.rightWidget.layout().addWidget(self.vis)
            elif widget == "Barchart":
                self.removeOptions()
                if self.vis:
                    self.rightWidget.layout().removeWidget(self.vis)
                    self.vis.deleteLater()
                self.vis = Barchart(self, self.filteredData.copy(), self.highlightedIdxs)
                self.rightWidget.layout().addWidget(self.vis)
            elif widget == "Heatmap":
                self.removeOptions()
                if self.vis:
                    self.rightWidget.layout().removeWidget(self.vis)
                    self.vis.deleteLater()
                self.vis = Heatmap(self, self.filteredData.copy())
                self.rightWidget.layout().addWidget(self.vis)
            elif widget == "Table":
                self.removeOptions()
                if self.vis:
                    self.rightWidget.layout().removeWidget(self.vis)
                    self.vis.deleteLater()
                self.vis = Table(self, self.database.copy())
                self.rightWidget.layout().addWidget(self.vis)

    def openFileNameDialog(self):
        # opens and loads the .csv file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","CSV Files (*.csv)", options=options)
        if fileName:
            self.database = pd.read_csv(fileName, sep=",")
            for col in self.database.columns:
                self.database[col] = self.database[col].replace(float('nan'), np.nan)
            self.filteredData = self.database.copy()
            self.setWidget("Table")

    def setFilteredData(self, database):
        # used by vises to filter the database
        self.filteredData = database

    def addOptions(self, options):
        # used by vises to add their filter settings on the bluescreen
        for option in options:
            self.leftWidget.layout().addWidget(option)

    def removeOptions(self, options=None):
        # removes all bluescreen filter settings or only the selected ones
        if options is None:
            for i in reversed(range(self.leftWidget.layout().count())):
                widgetToRemove = self.leftWidget.layout().itemAt( i ).widget()
                # remove it from the layout list
                self.leftWidget.layout().removeWidget( widgetToRemove )
                # remove it from the gui
                widgetToRemove.setParent( None )
                widgetToRemove.deleteLater()
        else:
            for option in options:
                option.hide()
                self.leftWidget.layout().removeWidget(option)

    def getDatabase(self):
        # sometimes the vis need all data back not the filtered
        return self.database.copy()

    def getFilteredDatabase(self):
        # when a vis filtered their own database to much
        return self.filteredData.copy()

    def setHighlight(self, highlight):
        # used to propegate highlight
        self.highlightedIdxs = highlight

    def getHighlight(self):
        # used to propegate highlight
        return self.highlightedIdxs

app = QApplication([])
app.setStyle('Fusion')
window = Window()
window.show()
app.exec_()
