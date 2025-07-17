#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

import os
import json
from appdirs import user_data_dir
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5 import uic
from .utils import loadHelp

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../gui/remove_arts_tooltip.ui'))

class TaRemoveArtefactsTooltip(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(TaRemoveArtefactsTooltip, self).__init__(parent)
        self.setupUi(self)
        # enable custom window hint
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)

        # disable (but not hide) close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        #self.setWindowFlags(Qt.CustomizeWindowHint)
        #self.setWindowFlags(Qt.WindowCloseButtonHint, False)

        # List comparison operators.TypeBox
        
        data_dir = user_data_dir("QGIS3", "QGIS")
        self.settings_path = os.path.join(data_dir, "plugins", "terra_antiqua", 'settings.json')

        self.showAgain = None
        self.isShowable()

        loadHelp(self)

    def isShowable(self):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
        except Exception:
            settings_dict = {}

        if 'RemoveArtefactsTooltip' not in settings_dict:
            self.showAgain = True
        else:
            self.showAgain = settings_dict['RemoveArtefactsTooltip'].get('showAgain', True)

    def setShowable(self, value):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
        except Exception:
            settings_dict = {}

        if 'RemoveArtefactsTooltip' not in settings_dict:
            settings_dict['RemoveArtefactsTooltip'] = {}

        settings_dict['RemoveArtefactsTooltip']['showAgain'] = value

        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=4, ensure_ascii=False)
