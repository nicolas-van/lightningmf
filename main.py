#!/usr/bin/python
from PySide import QtGui  
from PySide import QtCore
from PySide import QtUiTools
import sys  
import os

class FrontendApplication:
    def launch(self):
        self.app = QtGui.QApplication(sys.argv)  

        self.loader = QtUiTools.QUiLoader()
        file = QtCore.QFile("view.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.win = self.loader.load(file)
        file.close()

        self.win.move(QtGui.QDesktopWidget().availableGeometry().center() - self.win.geometry().center());
        self.settings = QtCore.QSettings("qsdoiuhvap", "xpoihybao");
        self.win.restoreGeometry(self.settings.value("geometry"));
        self.win.show()
        def hello():
            print "hello"
        self.win.launchButton.clicked.connect(hello)

        self.win.itemsView.setModel(MyModel())
        self.win.itemsView.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.win.itemsView.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)

        self.app.exec_()
        
        self.settings.setValue("geometry", self.win.saveGeometry())

class MyModel(QtCore.QAbstractTableModel):
    def rowCount(self, *args):
        return 3
    def columnCount(self, *args):
        return 3
    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if index.column() <= 2 and index.row() <= 2:
            return "yop"

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Something"
            elif section == 2:
                return "Else"
            else:
                return



if __name__ == '__main__':  
    FrontendApplication().launch()

