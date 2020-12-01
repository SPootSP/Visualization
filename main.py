from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg
import pandas as pd

class FileReader(QWidget):

    database = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        self.setStyleSheet("QWidget"
                        "{"
                        "background : white"
                        "}")
        self.UiComponents()

    def UiComponents(self):
        self.openFileBtn = QPushButton('Visualization 1', self)
        self.openFileBtn.setGeometry(10,10,133,30)

        self.openFileBtn = QPushButton('Visualization 2', self)
        self.openFileBtn.setGeometry(200,10,133,30)

        self.openFileBtn = QPushButton('Open file', self)
        self.openFileBtn.setGeometry(10,40,133,30)
        self.openFileBtn.clicked.connect(self.openFile)

        self.loadingLabel = QLabel('Nothing loaded yet', self)
        self.loadingLabel.setGeometry(134,40,133,30)
        self.loadingLabel.setStyleSheet("QWidget"
                        "{"
                        "background : lightblue"
                        "}")

        self.setSelectedBtn = QPushButton('Set selected', self)
        self.setSelectedBtn.setGeometry(267,40,133,30)
        self.setSelectedBtn.clicked.connect(self.on_click)

        self.fileLocation = QTextEdit(r'C:\Users\20191704\Documents\Visualization\week 1\dataset.csv', self)
        self.fileLocation.setLineWrapMode(QTextEdit.WidgetWidth)
        self.fileLocation.setWordWrapMode(QTextOption.WrapAnywhere)
        self.fileLocation.setGeometry(10,70,400,30)

        self.table = QTableWidget(self)
        self.table.setGeometry(10, 100, 400,400)

    def openFile(self):
        self.loadingLabel.setText("Loading")
        self.database = pd.read_csv(self.fileLocation.toPlainText(), sep=";")
        self.table.setRowCount(self.database.shape[0])
        self.table.setColumnCount(self.database.shape[1])
        for x in range(self.database.shape[0]):
            for y in range(self.database.shape[1]):
                column_name = self.database.columns[y]
                self.table.setItem(x,y, QTableWidgetItem(str(self.database.loc[x,column_name])))
        self.table.setHorizontalHeaderLabels(self.database.columns)
        self.loadingLabel.setText("Opened file successfully")

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.table.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())


class Window(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Hello")
        self.showFullScreen();
        self.UiComponents()

        self.show()

    def UiComponents(self):
        widget = QWidget()

        leftWidget = QWidget(widget)
        leftWidget.setGeometry(0,0, 420,1080)
        leftWidget.setStyleSheet("QWidget"
                        "{"
                        "background : lightblue"
                        "}")
        mainWidget = QWidget(widget)
        mainWidget.setGeometry(600, 0, 1080, 1500)

        fileWidget = FileReader(leftWidget)
        fileWidget.setGeometry(0,0, 420,540)
        outputLayout = QWidget(leftWidget)
        outputLayout.setGeometry(0,540, 420,540)

        self.setCentralWidget(widget)

app = QApplication([])
app.setStyle('Fusion')
window = Window()
window.show()
app.exec_()
