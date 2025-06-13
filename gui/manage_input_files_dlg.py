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
        
        # Button to add models
        add_button = QtWidgets.QPushButton(" Add model")
        add_button.setIcon(QtGui.QIcon(":/addButton.png"))
        add_button.setToolTip("Add a new tectonic model")
        add_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        add_button.setAutoDefault(False)
        left_side.layout().addWidget(add_button)
        
        # Right side of the models section
        model_details = QtWidgets.QWidget(horizontal_splitter)
        model_details.setLayout(QtWidgets.QVBoxLayout())
        model_details.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        # Title for model details
        details_title = QtWidgets.QLabel("Select a model to see its details")
        details_title.setStyleSheet("font-weight: bold;")
        model_details.layout().addWidget(details_title)
        
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        model_details.layout().addWidget(separator)
        
        # Name field
        name_field = QtWidgets.QWidget()
        name_field.setLayout(QtWidgets.QVBoxLayout())
        name_field.layout().setContentsMargins(0, 0, 0, 0)
        model_details.layout().addWidget(name_field)
        
        name_field.layout().addWidget(QtWidgets.QLabel("Model name:"))
        name_edit = QtWidgets.QLineEdit()
        name_field.layout().addWidget(name_edit)
        name_field.hide()
               
        # Description field
        model_details.layout().addWidget(QtWidgets.QLabel("Description:"))
        description_text = QtWidgets.QTextEdit(model_details)
        description_text.setReadOnly(True)
        description_text.setEnabled(False)
        model_details.layout().addWidget(description_text)
        
        # Grid layout for the other fields
        fields_grid = QtWidgets.QGridLayout()
        model_details.layout().addLayout(fields_grid)

        # URL field
        url_label = QtWidgets.QLabel("URL:")
        url_edit = QtWidgets.QLineEdit()
        url_edit.setReadOnly(True)
        url_edit.setEnabled(False)
        fields_grid.addWidget(url_label, 0, 0)
        fields_grid.addWidget(url_edit, 0, 1)
        
        # Version field
        version_label = QtWidgets.QLabel("Version:")
        version_edit = QtWidgets.QLineEdit()
        version_edit.setReadOnly(True)
        version_edit.setEnabled(False)
        fields_grid.addWidget(version_label, 0, 2)
        fields_grid.addWidget(version_edit, 0, 3)

        # SmallTime field
        smalltime_edit = QtWidgets.QLineEdit()
        smalltime_edit.setReadOnly(True)
        smalltime_edit.setEnabled(False)
        fields_grid.addWidget(QtWidgets.QLabel("SmallTime:"), 1, 0)
        fields_grid.addWidget(smalltime_edit, 1, 1)
        
        smalltime_spinbox = QtWidgets.QSpinBox()
        smalltime_spinbox.setRange(0, 1000000)
        smalltime_spinbox.setSuffix(" Ma")
        smalltime_spinbox.hide()
        fields_grid.addWidget(smalltime_spinbox, 1, 1)
        
        # BigTime field
        bigtime_edit = QtWidgets.QLineEdit()
        bigtime_edit.setReadOnly(True)
        bigtime_edit.setEnabled(False)
        fields_grid.addWidget(QtWidgets.QLabel("BigTime:"), 1, 2)
        fields_grid.addWidget(bigtime_edit, 1, 3)
        
        bigtime_spinbox = QtWidgets.QSpinBox()
        bigtime_spinbox.setRange(0, 1000000)
        bigtime_spinbox.setSuffix(" Ma")
        bigtime_spinbox.hide()
        fields_grid.addWidget(bigtime_spinbox, 1, 3)
        
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        model_details.layout().addWidget(separator)
        
        # Layers checkboxes
        layer_checkboxes = QtWidgets.QWidget()
        layer_checkboxes.setLayout(QtWidgets.QGridLayout())
        layer_checkboxes.layout().setContentsMargins(0, 0, 0, 0)
        model_details.layout().addWidget(layer_checkboxes)
        
        layer_checkboxes.layout().addWidget(QtWidgets.QLabel("Available layers:"), 0, 0)
        
        # Custom event filter to prevent the checkboxes from being toggled by the user
        class NoToggleEventFilter(QtCore.QObject):
            def eventFilter(self, obj, event):
                if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseButtonDblClick, QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
                    return True
                return super().eventFilter(obj, event)
        self.no_toggle_filter = NoToggleEventFilter(self)
        
        topologies_checkbox = QtWidgets.QCheckBox("Topologies")
        topologies_checkbox.setEnabled(False)
        topologies_checkbox.installEventFilter(self.no_toggle_filter)
        layer_checkboxes.layout().addWidget(topologies_checkbox, 0, 1)
        
        coastlines_checkbox = QtWidgets.QCheckBox("Coastlines")
        coastlines_checkbox.setEnabled(False)
        coastlines_checkbox.installEventFilter(self.no_toggle_filter)
        layer_checkboxes.layout().addWidget(coastlines_checkbox, 0, 2)
        
        cobs_checkbox = QtWidgets.QCheckBox("COBs")
        cobs_checkbox.setEnabled(False)
        cobs_checkbox.installEventFilter(self.no_toggle_filter)
        layer_checkboxes.layout().addWidget(cobs_checkbox, 0, 3)
        
        static_polygons_checkbox = QtWidgets.QCheckBox("Static polygons")
        static_polygons_checkbox.setEnabled(False)
        static_polygons_checkbox.installEventFilter(self.no_toggle_filter)
        layer_checkboxes.layout().addWidget(static_polygons_checkbox, 1, 1)
        
        continental_polygons_checkbox = QtWidgets.QCheckBox("Continental polygons")
        continental_polygons_checkbox.setEnabled(False)
        continental_polygons_checkbox.installEventFilter(self.no_toggle_filter)
        layer_checkboxes.layout().addWidget(continental_polygons_checkbox, 1, 2)
        
        # Function to update the model details when a model is selected
        def on_selection_changed(selected, deselected):
            if selected.indexes():
                index = selected.indexes()[0]
                
                name_field.hide()
                model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                details_title.setText(model_name)
                
                model_dict = cache_manager.get_model(model_name).model
                
                description_text.setEnabled(True)
                description_text.setPlainText(model_dict.get('Description', ''))
                
                url_label.show()
                url_edit.show()
                url_edit.setEnabled(True)
                url_edit.setText(str(model_dict.get('URL', '')))
                
                version_label.show()
                version_edit.show()
                version_edit.setEnabled(True)
                version_edit.setText(str(model_dict.get('Version', '')))
                
                smalltime_spinbox.hide()
                smalltime_edit.show()
                smalltime_edit.setEnabled(True)
                smalltime_edit.setText(str(model_dict.get('SmallTime', '')))
                
                bigtime_spinbox.hide()
                bigtime_edit.show()
                bigtime_edit.setEnabled(True)
                bigtime_edit.setText(str(model_dict.get('BigTime', '')))
                
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
        selection_model = model_list_view.selectionModel()
        selection_model.selectionChanged.connect(on_selection_changed)
        
        # Function to handle the "Add model" button click
        def on_add_model_click():
            details_title.setText("Add a new model")
            name_field.show()
            name_edit.setText("")
            
            description_text.setEnabled(True)
            description_text.setPlainText("")
            
            url_label.hide()
            url_edit.hide()
            version_label.hide()
            version_edit.hide()
            
            smalltime_edit.hide()
            smalltime_spinbox.show()
            smalltime_spinbox.setValue(0)
            
            bigtime_edit.hide()
            bigtime_spinbox.show()
            bigtime_spinbox.setValue(0)
        add_button.clicked.connect(on_add_model_click)
        
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
        
