#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

import os
from PyQt5 import QtWidgets, QtGui, QtCore
from qgis.gui import QgsCollapsibleGroupBox

from ..core.utils import center_window
from ..core.cache_manager import cache_manager

class TaManageInputFilesDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(TaManageInputFilesDlg, self).__init__(parent)
        self.setWindowTitle("Terra Antiqua - Manage Input Files")
        self.setGeometry(200, 200, 900, 600)
        center_window(self)
        
        # Base Layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        # Vertical splitter
        vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        vertical_splitter.setChildrenCollapsible(False)
        self.layout().addWidget(vertical_splitter)
        
        # Models section
        models_groupbox = QgsCollapsibleGroupBox("Tectonic models", vertical_splitter)
        models_groupbox.setLayout(QtWidgets.QHBoxLayout())
        horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        horizontal_splitter.setChildrenCollapsible(False)
        models_groupbox.layout().addWidget(horizontal_splitter)
        
        # Left side of the models section
        left_side = QtWidgets.QWidget(horizontal_splitter)
        left_side.setLayout(QtWidgets.QVBoxLayout())
        left_side.layout().setContentsMargins(0, 0, 0, 0)
        
        # Model list
        model_list = QtCore.QStringListModel(cache_manager.get_available_models())
        model_list_view = QtWidgets.QListView()
        model_list_view.setModel(model_list)
        model_list_view.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        left_side.layout().addWidget(model_list_view)
        
        # Add button to add models
        add_button = QtWidgets.QPushButton(" Add model")
        add_button.setIcon(QtGui.QIcon(":/addButton.png"))
        add_button.setToolTip("Add a new tectonic model")
        left_side.layout().addWidget(add_button)
        
        # Right side of the models section
        model_details = QtWidgets.QGroupBox("Select a model", horizontal_splitter)
        model_details.setLayout(QtWidgets.QVBoxLayout())
        model_details.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        def on_selection_changed(selected, deselected):
            if selected.indexes():
                index = selected.indexes()[0]
                model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                model_details.setTitle(" " + model_name)
                model_dict = cache_manager.get_model(model_name).model
                
                description_text.setPlainText(model_dict.get('Description', ''))
                url_edit.setText(str(model_dict.get('URL', '')))
                version_edit.setText(str(model_dict.get('Version', '')))
                smalltime_edit.setText(str(model_dict.get('SmallTime', '')))
                bigtime_edit.setText(str(model_dict.get('BigTime', '')))
                
                if 'Layers' in model_dict:
                    topologies_checkbox.setEnabled(True)
                    coastlines_checkbox.setEnabled(True)
                    cobs_checkbox.setEnabled(True)
                    static_polygons_checkbox.setEnabled(True)
                    continental_polygons_checkbox.setEnabled(True)
                    topologies_checkbox.setChecked('Topologies' in model_dict['Layers'])
                    continental_polygons_checkbox.setChecked('ContinentalPolygons' in model_dict['Layers'])
                    cobs_checkbox.setChecked('COBs' in model_dict['Layers'])
                    static_polygons_checkbox.setChecked('StaticPolygons' in model_dict['Layers'])
                    coastlines_checkbox.setChecked('Coastlines' in model_dict['Layers'])
                else:
                    topologies_checkbox.setChecked(False)
                    coastlines_checkbox.setChecked(False)
                    cobs_checkbox.setChecked(False)
                    static_polygons_checkbox.setChecked(False)
                    continental_polygons_checkbox.setChecked(False)
                    topologies_checkbox.setEnabled(False)
                    continental_polygons_checkbox.setEnabled(False)
                    cobs_checkbox.setEnabled(False)
                    static_polygons_checkbox.setEnabled(False)
                    coastlines_checkbox.setEnabled(False)
                
        selection_model = model_list_view.selectionModel()
        selection_model.selectionChanged.connect(on_selection_changed)
        
        model_details.layout().addWidget(QtWidgets.QLabel("Description:"))
        description_text = QtWidgets.QTextEdit(model_details)
        description_text.setReadOnly(True)
        model_details.layout().addWidget(description_text)
        
        # Add grid layout for additional fields
        details_grid = QtWidgets.QGridLayout()
        model_details.layout().addLayout(details_grid)

        # Labels and line edits for each field
        url_label = QtWidgets.QLabel("URL:")
        url_edit = QtWidgets.QLineEdit()
        url_edit.setReadOnly(True)
        details_grid.addWidget(url_label, 0, 0)
        details_grid.addWidget(url_edit, 0, 1)
        
        version_label = QtWidgets.QLabel("Version:")
        version_edit = QtWidgets.QLineEdit()
        version_edit.setReadOnly(True)
        details_grid.addWidget(version_label, 0, 2)
        details_grid.addWidget(version_edit, 0, 3)

        smalltime_label = QtWidgets.QLabel("SmallTime:")
        smalltime_edit = QtWidgets.QLineEdit()
        smalltime_edit.setReadOnly(True)
        details_grid.addWidget(smalltime_label, 2, 0)
        details_grid.addWidget(smalltime_edit, 2, 1)

        bigtime_label = QtWidgets.QLabel("BigTime:")
        bigtime_edit = QtWidgets.QLineEdit()
        bigtime_edit.setReadOnly(True)
        details_grid.addWidget(bigtime_label, 2, 2)
        details_grid.addWidget(bigtime_edit, 2, 3)
        
        details_grid.addWidget(QtWidgets.QLabel("Available layers:"), 3, 0)
        
        class NoToggleEventFilter(QtCore.QObject):
            def eventFilter(self, obj, event):
                if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseButtonDblClick, QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
                    return True  # Block the event
                return super().eventFilter(obj, event)
        
        topologies_checkbox = QtWidgets.QCheckBox("Topologies")
        topologies_checkbox.setEnabled(False)
        details_grid.addWidget(topologies_checkbox, 3, 1)
        
        coastlines_checkbox = QtWidgets.QCheckBox("Coastlines")
        coastlines_checkbox.setEnabled(False)
        details_grid.addWidget(coastlines_checkbox, 3, 2)
        
        cobs_checkbox = QtWidgets.QCheckBox("COBs")
        cobs_checkbox.setEnabled(False)
        details_grid.addWidget(cobs_checkbox, 3, 3)
        
        static_polygons_checkbox = QtWidgets.QCheckBox("Static polygons")
        static_polygons_checkbox.setEnabled(False)
        details_grid.addWidget(static_polygons_checkbox, 4, 1)
        
        continental_polygons_checkbox = QtWidgets.QCheckBox("Continental polygons")
        continental_polygons_checkbox.setEnabled(False)
        details_grid.addWidget(continental_polygons_checkbox, 4, 2)
        
        self.no_toggle_filter = NoToggleEventFilter(self)
        topologies_checkbox.installEventFilter(self.no_toggle_filter)
        coastlines_checkbox.installEventFilter(self.no_toggle_filter)
        cobs_checkbox.installEventFilter(self.no_toggle_filter)
        static_polygons_checkbox.installEventFilter(self.no_toggle_filter)
        continental_polygons_checkbox.installEventFilter(self.no_toggle_filter)
        
        # Rasters section
        rasters_groupbox = QgsCollapsibleGroupBox("Present day raster files", vertical_splitter)
        rasters_groupbox.setLayout(QtWidgets.QHBoxLayout())
        
        raster_list = QtCore.QStringListModel(['ETOPO Bedrock (60 arc seconds)',
                                              'ETOPO Bedrock (30 arc seconds)',
                                              'ETOPO Ice (60 arc seconds)',
                                              'ETOPO Ice (30 arc seconds)'])
        raster_list_view = QtWidgets.QListView()
        raster_list_view.setModel(raster_list)
        raster_list_view.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        rasters_groupbox.layout().addWidget(raster_list_view)
        
        vertical_splitter.setSizes([400, 200])
        
