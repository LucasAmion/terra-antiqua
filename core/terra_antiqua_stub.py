# Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
# Full copyright notice in file: terra_antiqua.py

"""
Lightweight stub that registers the Terra Antiqua toolbar and menu entries
using only PyQt5 / QGIS imports (no third-party dependencies).

On first button click it checks whether the plugin's pip dependencies are
installed.  If they are missing it shows an install dialog; once they are
present it lazily loads the real TerraAntiqua class and delegates to it.
"""

import os

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QToolBar

from .dependency_checker import check_dependencies
from ..resources import *


class TerraAntiquaStub:

    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TerraAntiqua_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Terra Antiqua')

        self.ta_toolBar = iface.mainWindow().findChild(QToolBar, u'Terra Antiqua')
        if not self.ta_toolBar:
            self.ta_toolBar = iface.addToolBar(u'Terra Antiqua')
            self.ta_toolBar.setObjectName(u'Terra Antiqua')

        # Will hold the real TerraAntiqua instance once deps are installed
        self._real_plugin = None

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------
    def tr(self, message):
        return QCoreApplication.translate('TerraAntiqua', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None,
            checkable=False):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.ta_toolBar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        if checkable:
            action.setCheckable(True)
        self.actions.append(action)
        return action

    # -----------------------------------------------------------------
    # GUI registration  (mirrors TerraAntiqua.initGui)
    # -----------------------------------------------------------------
    def initGui(self):
        compile_tb_icon = ':/compile_tb_icon.png'
        prepare_masks_icon = ':/prepare_masks_icon.png'
        modify_tb_icon = ':/modify_tb_icon.png'
        set_pls_icon = ':/set_pls_icon.png'
        std_proc_icon = ':/std_proc_icon.png'
        feat_create_icon = ':/feat_create_icon.png'
        remove_arts_icon = ':/remove_arts_icon.png'
        raster_layers_icon = ':/raster_layers_icon.png'
        vector_layers_icon = ':/vector_layers_icon.svg'
        manage_input_files_icon = ':/download.svg'

        self.add_action(
            manage_input_files_icon,
            text=self.tr(u'Manage Input Files'),
            callback=lambda: self._ensure_deps_and_run('initManageInputFiles'),
            parent=self.iface.mainWindow())

        self.add_action(
            raster_layers_icon,
            text=self.tr(u'Reconstruct Raster Layers'),
            callback=lambda: self._ensure_deps_and_run('initReconstructRasters'),
            parent=self.iface.mainWindow())

        self.add_action(
            vector_layers_icon,
            text=self.tr(u'Reconstruct Vector Layers'),
            callback=lambda: self._ensure_deps_and_run('initReconstructVectorLayers'),
            parent=self.iface.mainWindow())

        self.add_action(
            compile_tb_icon,
            text=self.tr(u'Compile Topo/Bathymetry'),
            callback=lambda: self._ensure_deps_and_run('initCompileTopoBathy'),
            parent=self.iface.mainWindow())

        self.add_action(
            set_pls_icon,
            text=self.tr(u'Set Paleoshorelines'),
            callback=lambda: self._ensure_deps_and_run('initSetPaleoShorelines'),
            parent=self.iface.mainWindow())

        self.add_action(
            modify_tb_icon,
            text=self.tr(u'Modify Topo/Bathymetry'),
            callback=lambda: self._ensure_deps_and_run('initModifyTopoBathy'),
            parent=self.iface.mainWindow())

        self.add_action(
            feat_create_icon,
            text=self.tr(u'Create Topo/Bathymetry'),
            callback=lambda: self._ensure_deps_and_run('initCreateTopoBathy'),
            parent=self.iface.mainWindow())

        self.add_action(
            remove_arts_icon,
            text=self.tr(u'Remove Artefacts'),
            callback=lambda: self._ensure_deps_and_run('initRemoveArtefacts'),
            parent=self.iface.mainWindow(),
            checkable=True)

        self.add_action(
            prepare_masks_icon,
            text=self.tr(u'Prepare masks'),
            callback=lambda: self._ensure_deps_and_run('initPrepareMasks'),
            parent=self.iface.mainWindow())

        self.add_action(
            std_proc_icon,
            text=self.tr(u'Standard Processing'),
            callback=lambda: self._ensure_deps_and_run('initStandardProcessing'),
            parent=self.iface.mainWindow())

    # -----------------------------------------------------------------
    # Dependency gate
    # -----------------------------------------------------------------
    def _ensure_deps_and_run(self, method_name):
        """Check deps, prompt install if missing, then forward to the real plugin."""
        if self._real_plugin is not None:
            getattr(self._real_plugin, method_name)()
            return

        if check_dependencies():
            self._load_real_plugin()
            getattr(self._real_plugin, method_name)()
            return

        # Dependencies missing — show install dialog
        from ..gui.install_dependencies_dlg import TaInstallDependenciesDialog

        dlg = TaInstallDependenciesDialog(self.iface.mainWindow())
        result = dlg.exec_()

        if result == TaInstallDependenciesDialog.Accepted and dlg.was_successful():
            self._load_real_plugin()
            getattr(self._real_plugin, method_name)()

    def _load_real_plugin(self):
        """Import and initialise the real TerraAntiqua, reusing our toolbar."""
        from .terra_antiqua import TerraAntiqua

        self._real_plugin = TerraAntiqua(self.iface)
        # The real plugin must not create duplicate toolbar entries — we pass
        # our already-registered actions and toolbar so it can reuse them.
        self._real_plugin.actions = self.actions
        self._real_plugin.ta_toolBar = self.ta_toolBar
        self._real_plugin.menu = self.menu
        # Run its init logic that doesn't touch the GUI (settings, first_start, etc.)
        self._real_plugin.first_start = True
        self._real_plugin.settings.setTempValue("first_start", True)

    # -----------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------
    def unload(self):
        if self._real_plugin is not None:
            self._real_plugin.unload()
        else:
            for action in self.actions:
                self.iface.removePluginMenu(
                    self.tr(u'&Terra Antiqua'),
                    action)
                self.iface.removeToolBarIcon(action)
                self.ta_toolBar.removeAction(action)
