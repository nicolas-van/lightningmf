#!/usr/bin/python
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

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

data_directory = os.path.expanduser("~/.lightningmf")
if not os.path.exists(data_directory):
    os.makedirs(data_directory)

confFile = os.path.join(data_directory, "conf.json")

cstring = "sqlite:///" + os.path.join(data_directory, "db.sqlite")
engine = sqlalchemy.create_engine(cstring, echo=False)

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
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    year = Column(String(10), nullable=False)
    manufacturer = Column(String(70), nullable=False)
    status = Column(String(50), nullable=False)
    cloneof = Column(String(50))

# session

class ThreadSession:
    def __init__(self, session_class):
        self._session_class = sqlalchemy.orm.scoped_session(session_class)
    def __getattr__(self, name):
        return getattr(self._session_class(), name)
    def ensure_inited(self):
        return self._session_class()
    def remove(self):
        try:
            self._session_class.remove()
        except:
            pass

session = ThreadSession(sqlalchemy.orm.sessionmaker(bind=engine))

_local_test = threading.local()

def transactionnal(fct):
    def wrapping(*args, **kwargs):
        if getattr(_local_test, "test", 0) != 0:
            raise Exception("Multiple usages of @transactionnal")
        _local_test.test = 1
        session.ensure_inited()
        try:
            val = fct(*args, **kwargs)
            session.commit()
            return val
        finally:
            _local_test.test = 0
            session.remove()
    return wrapping

# database initialisation

def init_db():
    if len(Base.metadata.tables.keys()) == 0:
        return
    tname = Base.metadata.tables.keys()[0]
    if not engine.dialect.has_table(engine, tname):
        Base.metadata.create_all(engine) 
        @transactionnal
        def create_data():
            pass
        create_data()

def drop_db():
    Base.metadata.drop_all(engine)

# gui
class FrontendApplication:
    def launch(self):
        self.configuration = {
            "mameExecutable": "",
            "commandLineArguments": "",
        }

        self.loadConfigFile()

        self.app = QtGui.QApplication(sys.argv)  

        loader = QtUiTools.QUiLoader()
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

        self.win.actionRoms.triggered.connect(self.loadRoms)
        self.win.actionMame.triggered.connect(self.configure)

        self.win.searchInput.textEdited.connect(self.searchChanged)

        self.win.launchButton.clicked.connect(self.launchGame)

        self.app.exec_()
        
        self.settings.setValue("geometry", self.win.saveGeometry())
    
    def loadRoms(*args):
        filename = tempfile.mktemp()
        try:
            with open(filename, "w") as tmpfile:
                subprocess.check_call([self.configuration["mameExecutable"], "-listxml"], stdout=tmpfile)
        except Exception as e:
            QtGui.QMessageBox.critical(self.win, "Error", "An error occured while listing the roms")
            return
        @transactionnal
        def parse_elements():
            import xml.etree.ElementTree as etree
            with open(filename) as tmpfile:
                doc = etree.iterparse(tmpfile)
                for event, elem in doc:
                    if elem.tag == "game":
                        name = elem.get("name")
                        desc = elem.findtext("description") or ""
                        year = elem.findtext("year") or ""
                        manu = elem.findtext("manufacturer") or ""
                        game = Game(name=name, description=desc, year=year, manufacturer=manu, status="")
                        session.add(game)

        parse_elements()

    def searchChanged(self, text):
        self.model.searchString = text
        self.model.modelReset.emit()

    def launchGame(self):
        selected = self.win.itemsView.selectedIndexes()
        if len(selected) == 0:
            return
        selected = selected[0].row()
        game = self.model.getRow(selected)
        errors = StringIO.StringIO()
        try:
            subprocess.check_call([self.configuration["mameExecutable"], game["game_name"]] \
                + shlex.split(self.configuration["commandLineArguments"]))
        except Exception as e:
            QtGui.QMessageBox.critical(self.win, "Error", "An error occured while launching this game")

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

        def browse():
            name = QtGui.QFileDialog.getOpenFileName(self.confDial, "Choose MAME executable")
            self.confDial.mameExecInput.setText(name[0])

        self.confDial.browseButton.clicked.connect(browse)

        def save():
            params = {
                "mameExecutable": self.confDial.mameExecInput.text(),
                "commandLineArguments": self.confDial.cmdInput.text(),
            }
            dump = json.dumps(params)
            with open(confFile, "w") as file:
                file.write(dump)
            self.loadConfigFile()

        self.confDial.buttonBox.accepted.connect(save)

        self.confDial.show()

    def loadConfigFile(self):
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
    @transactionnal
    def rowCount(self, *args):
        if self.count is None:
            self.count = self._buildQuery().count()
        return self.count
    def _buildQuery(self):
        return session.query(Game).order_by(Game.description).filter( \
                sqlalchemy.or_(Game.description.like("%" + self.searchString + "%"), \
                Game.name.like("%" + self.searchString + "%")))
    def columnCount(self, *args):
        return len(MyModel.headers)
    @transactionnal
    def data(self, index, role):
        if role != QtCore.Qt.DisplayRole:
            return
        game = self.getRow(index.row())
        col = MyModel.headers[index.column()][1]
        return game.get("game_" + col, "")
    def getRow(self, row):
        page = row / MyModel.items_per_page
        if not page in self.cache:
            if len(self.cache) >= MyModel.max_pages:
                del self.cache[self.cache.keys()[0]]
            result = session.execute(self._buildQuery() \
                    .offset(page * MyModel.items_per_page).limit(MyModel.items_per_page))
            dicts = [dict(x) for x in result]
            self.cache[page] = dicts
        return self.cache[page][row % MyModel.items_per_page]
    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return
        if orientation == QtCore.Qt.Horizontal:
            return MyModel.headers[section][0]

if __name__ == '__main__':  
    if len(sys.argv) >= 2 and sys.argv[1] == "-flush":
        print "flush db"
        drop_db()
    init_db()
    FrontendApplication().launch()

