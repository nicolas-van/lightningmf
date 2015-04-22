#!/usr/bin/python

#    Lightning MAME Frontend
#    Copyright (C) 2012 Nicolas Vanhoren
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PySide import QtGui  
from PySide import QtCore
from PySide import QtUiTools
import sys
import os
import tempfile
import subprocess
import sqlalchemy
import os.path
import os
import sqlalchemy.orm
import sqlalchemy.ext.declarative
from sqlalchemy import Column, Integer, String, Sequence, Boolean
from sqlalchemy.orm import relationship
import threading
import json
import shlex
import StringIO
import contextlib
from sqlalchemy.pool import SingletonThreadPool

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

data_directory = os.path.expanduser("~/.lightningmf")
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

confFile = os.path.join(data_directory, "conf.json")

cstring = "sqlite:///" + os.path.join(data_directory, "db.sqlite")
engine = sqlalchemy.create_engine(cstring, poolclass=SingletonThreadPool)

# Some helpers to help use SqlAlchemy
class Base(object):
    @sqlalchemy.ext.declarative.declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @sqlalchemy.ext.declarative.declared_attr
    def id(cls):
        return Column(Integer, Sequence(cls.__name__.lower() + "_id_seq"), primary_key=True)

Base = sqlalchemy.ext.declarative.declarative_base(cls=Base)

def Many2One(class_name, **kwargs):
    return Column(Integer, sqlalchemy.ForeignKey(class_name.lower() + ".id"), **kwargs)

# models

class Game(Base):
    name = Column(String(50), nullable=False, index=True)
    description = Column(String(200), nullable=False, index=True)
    year = Column(String(10), nullable=False)
    manufacturer = Column(String(70), nullable=False)
    status = Column(String(50), nullable=False)
    cloneof = Column(String(50))

# session

Session = sqlalchemy.orm.sessionmaker(bind=engine, autocommit=True)

session = None

# database initialisation

def init_db():
    if len(Base.metadata.tables.keys()) == 0:
        return
    tname = Base.metadata.tables.keys()[0]
    if not engine.dialect.has_table(engine, tname):
        Base.metadata.create_all(engine)

def drop_db():
    Base.metadata.drop_all(engine)

# gui
class FrontendApplication:
    def launch(self):
        self.configuration = {
            "mameExecutable": "",
            "commandLineArguments": "",
            "snapsFolder": "",
            "romsFolder": "",
        }
        self.loadConfigFile()

        self.app = QtGui.QApplication(sys.argv)  

        loader = QtUiTools.QUiLoader()
        loader.setWorkingDirectory(QtCore.QDir(SCRIPT_ROOT))
        file = QtCore.QFile(os.path.join(SCRIPT_ROOT, "view.ui"))
        try:
            file.open(QtCore.QFile.ReadOnly)
            self.win = loader.load(file)
        finally:
            file.close()

        self.win.move(QtGui.QDesktopWidget().availableGeometry().center() - self.win.geometry().center());
        self.settings = QtCore.QSettings("qsdoiuhvap", "xpoihybao");
        self.win.restoreGeometry(self.settings.value("geometry"));
        self.win.show()
        
        self.model = MyModel()
        self.win.itemsView.setModel(self.model)
        self.win.itemsView.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.win.itemsView.doubleClicked.connect(self.launchGame)
        x = self.win.itemsView.selectionModel()
        x.selectionChanged.connect(self.selectionChanged)
        def set_number():
            num = self.model.rowCount()
            self.win.romsNumberLabel.setText("%d roms" % num)
        self.model.modelReset.connect(set_number)
        set_number()


        self.win.actionRoms.triggered.connect(self.loadRoms)
        self.win.actionMame.triggered.connect(self.configure)

        self.win.searchInput.textEdited.connect(self.searchChanged)

        self.win.launchButton.clicked.connect(self.launchGame)

        def starting():
            if self.configuration["mameExecutable"] == "":
                ret = QtGui.QMessageBox.question(self.win, "Configuration Missing", "Lightning MAME Frontend is not configured, do you " \
                        + "want to configure it now?",
                        buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, defaultButton=QtGui.QMessageBox.Yes)
                if ret == QtGui.QMessageBox.Yes:
                    try:
                        subprocess.check_call(['mame', "-help"])
                        self.configuration["mameExecutable"] = "mame"
                        self.configuration["romsFolder"] = os.path.expanduser("~/.mame/roms")
                        self.configuration["snapsFolder"] = os.path.expanduser("~/.mame/snaps")
                    except:
                        pass # do nothing
                    self.configure()

        QtCore.QTimer.singleShot(0, starting)

        self.app.exec_()
        
        self.settings.setValue("geometry", self.win.saveGeometry())
    
    def loadRoms(self):
        self.win.statusBar().showMessage("Updating roms, please wait...", 2000)
        QtCore.QTimer.singleShot(0, self.trueLoadRoms)

    def trueLoadRoms(self):
        filename = tempfile.mktemp()
        try:
            with open(filename, "w") as tmpfile:
                subprocess.check_call([self.configuration["mameExecutable"], "-listxml"], stdout=tmpfile)
        except Exception as e:
            QtGui.QMessageBox.critical(self.win, "Error", "An error occured while listing the roms")
            self.win.statusBar().showMessage("Rom update failed", 2000)
            return

        def parse_elements():
            session.begin()
            try:
                session.query(Game).delete()
                import xml.etree.ElementTree as etree
                with open(filename) as tmpfile:
                    doc = etree.iterparse(tmpfile, events=("start", "end"))
                    doc = iter(doc)
                    event, root = doc.next()
                    num = 0
                    for event, elem in doc:
                        if event == "end" and elem.tag == "game":
                            name = elem.get("name")
                            if not os.path.exists(os.path.join(self.configuration["romsFolder"], name + ".zip")):
                                root.clear()
                                continue
                            desc = elem.findtext("description") or ""
                            year = elem.findtext("year") or ""
                            manu = elem.findtext("manufacturer") or ""
                            clone = elem.get("cloneof") or None
                            status = ""
                            driver = elem.find("driver")
                            if driver is not None:
                                status = driver.get("status") or ""
                            game = Game(name=name, description=desc, year=year, manufacturer=manu, status=status,
                                    cloneof=clone)
                            session.add(game)
                            if num >= 200:
                                session.commit()
                                num = 0
                            root.clear()
                session.commit()
            except:
                session.rollback()
                raise

        parse_elements()

        self.model.modelReset.emit()
        self.win.statusBar().showMessage("Rom update succeeded", 2000)

    def searchChanged(self, text):
        self.model.searchString = text
        self.model.modelReset.emit()

    def _getSelected(self):
        selected = self.win.itemsView.selectedIndexes()
        if len(selected) == 0:
            return
        selected = selected[0].row()
        return self.model._getRow(selected)

    def launchGame(self):
        game = self._getSelected()
        try:
            subprocess.check_call([self.configuration["mameExecutable"], game["game_name"]] \
                + shlex.split(self.configuration["commandLineArguments"]))
        except Exception as e:
            QtGui.QMessageBox.critical(self.win, "Error", "An error occured while launching this game")

    def selectionChanged(self, *args):
        game = self._getSelected()
        self.setGameImage(game)

    def setGameImage(self, game):
        path = os.path.join(self.configuration["snapsFolder"], game["game_name"] + ".png")
        if not os.path.exists(path):
            pix = None
            clone = game["game_cloneof"]
            if clone is not None:
                result = session.execute(session.query(Game).filter(Game.name == clone))
                result = [dict(x) for x in result]
                parent = result[0] if len(result) >= 1 else None
                if parent is not None:
                    return self.setGameImage(parent)
        else:
            img = QtGui.QImage()
            img.load(path)
            size = QtCore.QSize(self.win.imageLabel.width(), self.win.imageLabel.height())
            img = img.scaled(size, QtCore.Qt.KeepAspectRatio)
            pix = QtGui.QPixmap.fromImage(img)
        self.win.imageLabel.setPixmap(pix)

    def configure(self):
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(os.path.join(SCRIPT_ROOT, "config.ui"))
        try:
            file.open(QtCore.QFile.ReadOnly)
            self.confDial = loader.load(file)
        finally:
            file.close()

        self.confDial.mameExecInput.setText(self.configuration["mameExecutable"])
        self.confDial.cmdInput.setText(self.configuration["commandLineArguments"])
        self.confDial.snapsInput.setText(self.configuration["snapsFolder"])
        self.confDial.romsInput.setText(self.configuration["romsFolder"])

        def browse():
            name = QtGui.QFileDialog.getOpenFileName(self.confDial, "Choose MAME Executable")
            if len(name[0]) > 0:
                self.confDial.mameExecInput.setText(name[0])
        self.confDial.browseButton.clicked.connect(browse)
        def snapsBrowse():
            name = QtGui.QFileDialog.getExistingDirectory(self.confDial, "Choose Snapshots Folder")
            if len(name) > 0:
                self.confDial.snapsInput.setText(name)
        self.confDial.snapsButton.clicked.connect(snapsBrowse)
        def romsBrowse():
            name = QtGui.QFileDialog.getExistingDirectory(self.confDial, "Choose Roms Folder")
            if len(name) > 0:
                self.confDial.romsInput.setText(name)
        self.confDial.romsButton.clicked.connect(romsBrowse)

        def save():
            params = {
                "mameExecutable": self.confDial.mameExecInput.text(),
                "commandLineArguments": self.confDial.cmdInput.text(),
                "snapsFolder": self.confDial.snapsInput.text(),
                "romsFolder": self.confDial.romsInput.text(),
            }
            dump = json.dumps(params)
            with open(confFile, "w") as file:
                file.write(dump)
            self.loadConfigFile()
            if self.model.rowCount() == 0:
                ret = QtGui.QMessageBox.question(self.confDial, "Roms Loading", "Do you want to load the roms now?",
                    buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, defaultButton=QtGui.QMessageBox.Yes)
                if ret == QtGui.QMessageBox.Yes:
                    QtCore.QTimer.singleShot(0, self.loadRoms)

        self.confDial.buttonBox.accepted.connect(save)

        self.confDial.show()

    def loadConfigFile(self):
        if not os.path.exists(confFile):
            return
        with open(confFile) as file:
            tmp = file.read()
        self.configuration = json.loads(tmp)

class MyModel(QtCore.QAbstractTableModel):
    headers = {
        0: ("Title", "description"),
        1: ("Name", "name"),
        2: ("Year", "year"),
        3: ("Manufacturer", "manufacturer"),
        4: ("Status", "status"),
        5: ("Clone of", "cloneof"),
    }
    items_per_page = 50
    max_pages = 5
    def __init__(self):
        super(MyModel, self).__init__()
        self.cache = {}
        self.count = None
        self.searchString = ""
        def reset():
            self.cache = {}
            self.count = None
        self.modelReset.connect(reset)
    def rowCount(self, *args):
        if self.count is None:
            self.count = self._buildQuery(session).count()
        return self.count
    def _buildQuery(self, session):
        return session.query(Game).order_by(Game.description).filter( \
                sqlalchemy.or_(Game.description.like("%" + self.searchString + "%"), \
                Game.name.like("%" + self.searchString + "%")))
    def columnCount(self, *args):
        return len(MyModel.headers)
    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return
        game = self._getRow(index.row())
        col = MyModel.headers[index.column()][1]
        return game.get("game_" + col, "")
    def _getRow(self, row):
        page = row / MyModel.items_per_page
        if not page in self.cache:
            if len(self.cache) >= MyModel.max_pages:
                del self.cache[self.cache.keys()[0]]
            result = session.execute(self._buildQuery(session) \
                    .offset(page * MyModel.items_per_page).limit(MyModel.items_per_page))
            dicts = [dict(x) for x in result]
            self.cache[page] = dicts
        return self.cache[page][row % MyModel.items_per_page]
    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return MyModel.headers[section][0]

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "-flush":
        print "flush db"
        drop_db()
    init_db()
    global session
    session = Session()
    FrontendApplication().launch()
    print "End of application"
    engine.dispose()

if __name__ == '__main__':
    main()

