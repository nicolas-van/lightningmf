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

    app.exec_()

    setting.setValue("geometry", win.saveGeometry())


