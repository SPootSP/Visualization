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

    annot = None

    def __init__(self, parent, database):
        super(Correlogram, self).__init__()
        self.parent = parent
        self.database = database

        sns.scatterplot( )
        self.figure = sns.PairGrid(self.database, dropna=True)
        self.figure.map_upper(sns.kdeplot)
        self.figure.map_diag(sns.histplot)
        self.figure.map_lower(sns.scatterplot)

        self.vis = FigureCanvas(self.figure.fig)
        self.vis.mpl_connect('button_press_event', self.onclick)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vis)
        self.setLayout(self.layout)

    def onclick(self, event):
        for y in range(len(self.figure.axes)):
            for x in range(len(self.figure.axes[y])):
                if self.figure.axes[y][x] == event.inaxes:
                    data = self.database[[self.figure.axes[len(self.figure.axes)-1][x].get_xlabel(),
                                          self.figure.axes[y][0].get_ylabel()]].values
                    idx = np.nanargmin(((data - (event.xdata, event.ydata))**2).sum(axis = -1))
                    point = data[idx]
                    eDatabase = self.parent.getDatabase()
                    fDatabase = eDatabase[ eDatabase[self.figure.axes[len(self.figure.axes)-1][x].get_xlabel()] == point[0] ]
                    fDatabase = fDatabase[ fDatabase[self.figure.axes[y][0].get_ylabel()] == point[1] ]
                    if len(fDatabase) > 0:
                        dataPoint = fDatabase.iloc[0,:].dropna()
                        dstring = ""
                        for col in dataPoint.index:
                            dstring += col + ": " + str(dataPoint[[col]]) + "\n"
                        if self.annot is not None:
                            self.annot.set_visible(False)
                        self.annot = self.figure.axes[y][x].annotate(dstring,xy=point, ha = 'right',
                            xytext = (-20, 20), textcoords = 'offset points', va = 'bottom',
                            bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
                            arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0')
                            )
                        self.annot.set_visible(True)
                        self.vis.draw()

class Barchart(QWidget):
    rowList = []
    colList = []
    highlight = None
    xAxesValue = None
    yAxesValue = None
    minY = 0
    maxY = 0
    cValue = "deep"
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    colorSchemes = ["deep", "muted", "bright", "pastel", "dark", "colorblind"]

    def __init__(self, parent, database):
        super(Barchart, self).__init__()
        self.parent = parent
        self.database = database

        for col in database.columns:
            self.rowList.append(col)

        newdf = database.select_dtypes(include=self.numerics)
        for col in newdf.columns:
            self.colList.append(col)

        self.minY = self.database[self.colList[0]].min()
        self.maxY = self.database[self.colList[0]].max()

        self.minYLabel = QLabel("Set the minimum Y value")

        self.minYslider = QSlider(Qt.Horizontal)
        self.minYslider.valueChanged[int].connect(self.setMinYValue)
        self.minYslider.sliderReleased.connect(self.changeYRange)
        self.minYslider.setMinimum(self.minY)
        self.minYslider.setMaximum(self.maxY)
        self.minYslider.setValue(self.minY)

        self.maxYLabel = QLabel("Set the maximum Y value")

        self.maxYslider = QSlider(Qt.Horizontal)
        self.maxYslider.valueChanged[int].connect(self.setMaxYValue)
        self.maxYslider.sliderReleased.connect(self.changeYRange)
        self.maxYslider.setMinimum(self.minY)
        self.maxYslider.setMaximum(self.maxY)
        self.maxYslider.setValue(self.maxY)

        self.orderLabel = QLabel("Change the order of the bars.")

        self.comboBoxO = QComboBox()
        self.comboBoxO.addItems(["default","ascending","descending"])
        self.comboBoxO.currentIndexChanged.connect(self.setOValue)

        self.colorEncodingLabel = QLabel("Change the color encoding.")

        self.comboBoxC = QComboBox()
        self.comboBoxC.addItems(self.colorSchemes)
        self.comboBoxC.currentIndexChanged.connect(self.setCValue)

        self.boxLabelX = QLabel("Change the x-Axis.")

        self.comboBoxX = QComboBox()
        self.comboBoxX.addItems(self.rowList)
        self.comboBoxX.currentIndexChanged.connect(self.setXValue)

        self.boxLabelY = QLabel("Change the y-Axis.")

        self.comboBoxY = QComboBox()
        self.comboBoxY.addItems(self.colList)
        self.comboBoxY.currentIndexChanged.connect(self.setYValue)

        self.parent.addOptions([self.minYLabel, self.minYslider,
                                self.maxYLabel, self.maxYslider,
                                self.orderLabel, self.comboBoxO,
                                self.colorEncodingLabel, self.comboBoxC,
                                self.boxLabelX, self.comboBoxX,
                                self.boxLabelY, self.comboBoxY])

        self.xAxesValue = self.comboBoxX.currentText()
        self.yAxesValue = self.comboBoxY.currentText()

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(1,1,1)
        # the rotation of the labels came from https://stackabuse.com/rotate-axis-labels-in-matplotlib/
        for tick in self.ax.get_xticklabels():
            tick.set_rotation(90)
        for tick in self.ax.get_yticklabels():
            tick.set_rotation(90)
        try:
            sns.barplot(data=self.database, x=self.xAxesValue, y=self.yAxesValue, palette=self.cValue, ax=self.ax)
        except ValueError:
            print("Contains no valid data")
        self.vis = FigureCanvas(self.fig)
        self.vis.mpl_connect('button_press_event', self.onclick)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vis)
        self.setLayout(self.layout)

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
        self.database = self.parent.getFilteredDatabase()
        self.database = self.database[self.database[self.yAxesValue] >= self.minY]
        self.database = self.database[self.database[self.yAxesValue] <= self.maxY]
        self.update()

    def setOValue(self, state=None):
        oValue = self.comboBoxO.currentText()
        if oValue == "default":
            self.database = self.parent.getFilteredDatabase()
        elif oValue == "ascending":
            self.database.sort_values(by=self.yAxesValue, inplace=True)
        elif oValue == "descending":
            self.database.sort_values(by=self.yAxesValue, ascending=False,inplace=True)
        self.update()

    def setCValue(self, state=None):
        self.cValue = self.comboBoxC.currentText()
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
                print("normal")
                sns.barplot(data=self.database, x=self.xAxesValue, y=self.yAxesValue, palette=self.cValue, ax=self.ax)
            else:
                print("inbetween")
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
        for tick in self.ax.get_yticklabels():
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

    def __init__(self, parent, database):
        super(Table, self).__init__()
        self.parent = parent
        self.database = database
        self.vis = QTableWidget(self)
        self.vis.setRowCount(self.database.shape[0])
        self.vis.setColumnCount(self.database.shape[1])
        for x in range(self.database.shape[0]):
            for y in range(self.database.shape[1]):
                column_name = self.database.columns[y]
                self.vis.setItem(x,y, QTableWidgetItem(str(self.database.loc[x,column_name])))
        self.vis.setHorizontalHeaderLabels(self.database.columns)
        self.vis.itemSelectionChanged.connect(lambda: self.on_table_click())
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
        self.parent.setFilteredData(self.database.iloc[selectedRows, selectedColumns])

class Window(QMainWindow):

    vis = None
    database = None
    filteredData = None
    selectedData = None
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
                self.vis = Barchart(self, self.filteredData.copy())
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
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","CSV Files (*.csv)", options=options)
        if fileName:
            self.database = pd.read_csv(fileName, sep=";")
            for col in self.database.columns:
                self.database[col] = self.database[col].replace(float('nan'), np.nan)
            self.filteredData = self.database.copy()
            self.setWidget("Table")

    def setFilteredData(self, database):
        self.filteredData = database

    def addOptions(self, options):
        for option in options:
            self.leftWidget.layout().addWidget(option)

    def removeOptions(self, options=None):
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
        return self.database.copy()

    def getFilteredDatabase(self):
        return self.filteredData.copy()

    def setHighlight(self, highlight):
        self.highlightedIdxs = highlight

    def getHighlight(self):
        return self.highlightedIdxs

app = QApplication([])
app.setStyle('Fusion')
window = Window()
window.show()
app.exec_()
