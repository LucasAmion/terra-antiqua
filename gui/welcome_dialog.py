#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

import os
import json
from appdirs import user_data_dir
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from ..core.utils import center_window

class TaWelcomeDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(TaWelcomeDialog, self).__init__(parent)
        self.setGeometry(200, 200, 700, 300)
        center_window(self)
        
        data_dir = user_data_dir("QGIS3", "QGIS")
        self.settings_path = os.path.join(data_dir, "plugins", "terra_antiqua", 'settings.json')
        
        self.logo = QtGui.QIcon(':/logo.png')
        self.toolButton = QtWidgets.QToolButton(self)
        self.toolButton.setIcon(self.logo)
        self.toolButton.setIconSize(QtCore.QSize(150,150))
        self.toolButton.setAutoRaise(False)
        self.introBrowser = QtWidgets.QTextBrowser(self)
        self.introBrowser.setOpenExternalLinks(True)
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.toolButton, alignment = QtCore.Qt.AlignTop)
        self.layout.addWidget(self.introBrowser)
        self.hlayout = QtWidgets.QHBoxLayout()
        self.doNotShowCheckBox = QtWidgets.QCheckBox("Do not show this again")
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self.hlayout.addStretch()
        self.hlayout.addWidget(self.doNotShowCheckBox)
        self.hlayout.addWidget(self.buttonBox,QtCore.Qt.AlignRight)
        self.vlayout = QtWidgets.QVBoxLayout()
        self.vlayout.addLayout(self.layout)
        self.vlayout.addLayout(self.hlayout)
        self.setLayout(self.vlayout)
        self.setWindowTitle("Welcome to Terra Antiqua!")
        path_to_file = os.path.join(os.path.dirname(__file__),'../help_text/welcome.html')
        with open(path_to_file, 'r', encoding='utf-8') as help_file:
            help_text = help_file.read()
        self.introBrowser.setHtml(help_text)
        self.buttonBox.accepted.connect(self.accept)
        self.showAgain = None
        self.isShowable()

    def accept(self):
        if self.doNotShowCheckBox.isChecked():
            self.setShowable(False)
        self.close()

    def isShowable(self):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
        except Exception:
            settings_dict = {}
            
        if 'WelcomePage' not in settings_dict:
            self.showAgain = True
        else:
            self.showAgain = settings_dict['WelcomePage'].get('showAgain', True)

    def setShowable(self, value):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
        except Exception:
            settings_dict = {}
        
        if 'WelcomePage' not in settings_dict:
            settings_dict['WelcomePage'] = {}
        
        settings_dict['WelcomePage']['showAgain'] = value
        
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=4)


if __name__=='__main__':
    app = QtWidgets.QApplication([])
    dlg = TaWelcomeDialog()
    dlg.show()
    app.exec_()
