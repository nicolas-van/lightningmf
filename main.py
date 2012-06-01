#!/usr/bin/python
from PySide import QtGui  
from PySide import QtCore
from PySide import QtUiTools
import sys  
import os

if __name__ == '__main__':  

    app = QtGui.QApplication(sys.argv)  

    loader = QtUiTools.QUiLoader()
    file = QtCore.QFile("view.ui")
    file.open(QtCore.QFile.ReadOnly)
    win = loader.load(file)
    file.close()

    win.move(QtGui.QDesktopWidget().availableGeometry().center() - win.geometry().center());
    setting = QtCore.QSettings("qsdoiuhvap", "xpoihybao");
    win.restoreGeometry(setting.value("geometry"));
    win.show()
    def hello():
        print "hello"
    win.launchButton.clicked.connect(hello)

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



    win.itemsView.setModel(MyModel())

    app.exec_()

    setting.setValue("geometry", win.saveGeometry())


