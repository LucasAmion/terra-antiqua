#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

import os
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from qgis.gui import QgsCollapsibleGroupBox, QgsFileWidget

from ..core.utils import center_window
from ..core.cache_manager import cache_manager
import shutil

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
        add_button.setAutoDefault(False)
        add_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        
        # Align the button to the right
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(add_button)
        left_side.layout().addLayout(button_layout)
        
        # Right side of the models section
        scroll_area = QtWidgets.QScrollArea(horizontal_splitter)
        scroll_area.setWidgetResizable(True)
        model_details = QtWidgets.QWidget()
        model_details.setLayout(QtWidgets.QVBoxLayout())
        model_details.layout().setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(model_details)
        
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
        urlfield = QtWidgets.QWidget()
        urlfield.setLayout(QtWidgets.QHBoxLayout())
        urlfield.layout().setContentsMargins(0, 0, 0, 0)
        url_label = QtWidgets.QLabel("URL:")
        url_edit = QtWidgets.QLineEdit()
        url_edit.setReadOnly(True)
        url_edit.setEnabled(False)
        urlfield.layout().addWidget(url_label)
        urlfield.layout().addWidget(url_edit)
        fields_grid.addWidget(urlfield, 0, 0, 1, 2)
        
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
        smalltime_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
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
        bigtime_spinbox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
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
        
        # Layers file widgets
        layer_filewidgets = QtWidgets.QWidget()
        layer_filewidgets.setLayout(QtWidgets.QGridLayout())
        layer_filewidgets.layout().setContentsMargins(0, 0, 0, 5)
        model_details.layout().addWidget(layer_filewidgets)
        
        rotations_edit = QgsFileWidget()
        rotations_edit.setFilter("*.rot;;*.grot")
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Rotations:"), 0, 0)
        layer_filewidgets.layout().addWidget(rotations_edit, 0, 1, 1, 2)
        
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Vector layers:"), 1, 0)

        topologies_edit = QgsFileWidget()
        topologies_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        topologies_edit.setFilter(cache_manager.allowe_file_extensions)
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Topologies:"), 2, 1)
        layer_filewidgets.layout().addWidget(topologies_edit, 2, 2)      
        
        coastlines_edit = QgsFileWidget()
        coastlines_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        coastlines_edit.setFilter(cache_manager.allowe_file_extensions)
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Coastlines:"), 3, 1)
        layer_filewidgets.layout().addWidget(coastlines_edit, 3, 2)      
        
        cobs_edit = QgsFileWidget()
        cobs_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        cobs_edit.setFilter(cache_manager.allowe_file_extensions)
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("COBs:"), 4, 1)
        layer_filewidgets.layout().addWidget(cobs_edit, 4, 2)      
        
        static_polygons_edit = QgsFileWidget()
        static_polygons_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        static_polygons_edit.setFilter(cache_manager.allowe_file_extensions)
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Static Polygons:"), 5, 1)
        layer_filewidgets.layout().addWidget(static_polygons_edit, 5, 2)      
        
        continental_polygons_edit = QgsFileWidget()
        continental_polygons_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        continental_polygons_edit.setFilter(cache_manager.allowe_file_extensions)       
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Continental Polygons:"), 6, 1)
        layer_filewidgets.layout().addWidget(continental_polygons_edit, 6, 2)      

        layer_filewidgets.hide()
        
        # Save and cancel buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setText("Save changes")
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setToolTip("Save changes to the selected model")
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setToolTip("Cancel changes and close the dialog")
        model_details.layout().addWidget(button_box)
        
        # Function to update the model details when a model is selected
        def on_selection_changed(selected, deselected):
            if selected.indexes():
                index = selected.indexes()[0]
                
                name_field.hide()
                model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                details_title.setText(model_name)
                
                model_dict = cache_manager.get_model(model_name).model
                
                description_text.setEnabled(True)
                description_text.setPlainText(model_dict['Description'])
                
                if 'URL' in model_dict:
                    url = model_dict['URL']
                    url_label.show()
                    url_edit.show()
                    url_edit.setEnabled(True)
                    url_edit.setText(url)
                    url_edit.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                    url_edit.setStyleSheet("color: blue; text-decoration: underline;")
                    def open_url():
                        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
                    url_edit.mousePressEvent = lambda event: open_url()
                else:
                    url_label.hide()
                    url_edit.hide()
                
                if 'Version' in model_dict:
                    version_label.show()
                    version_edit.show()
                    version_edit.setEnabled(True)
                    version_edit.setText(model_dict['Version'])
                else:
                    version_label.hide()
                    version_edit.hide()
                
                smalltime_spinbox.hide()
                smalltime_edit.show()
                smalltime_edit.setEnabled(True)
                smalltime_edit.setText(str(model_dict['SmallTime']) + " Ma")
                
                bigtime_spinbox.hide()
                bigtime_edit.show()
                bigtime_edit.setEnabled(True)
                bigtime_edit.setText(str(model_dict['BigTime']) + " Ma")
                
                layer_filewidgets.hide()
                layer_checkboxes.show()
                
                topologies_checkbox.setEnabled(True)
                coastlines_checkbox.setEnabled(True)
                cobs_checkbox.setEnabled(True)
                static_polygons_checkbox.setEnabled(True)
                continental_polygons_checkbox.setEnabled(True)
                
                topologies_checkbox.setChecked('Topologies' in model_dict['Layers'])
                coastlines_checkbox.setChecked('Coastlines' in model_dict['Layers'])
                cobs_checkbox.setChecked('COBs' in model_dict['Layers'])
                static_polygons_checkbox.setChecked('StaticPolygons' in model_dict['Layers'])
                continental_polygons_checkbox.setChecked('ContinentalPolygons' in model_dict['Layers'])

        selection_model = model_list_view.selectionModel()
        selection_model.selectionChanged.connect(on_selection_changed)
        
        # Function to handle the "Add model" button click
        def on_add_model_click():
            details_title.setText("Add a new model")
            name_field.show()
            name_edit.setText("")
            
            description_text.setReadOnly(False)
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
            
            layer_checkboxes.hide()
            layer_filewidgets.show()
            
            topologies_edit.setFilePath("")
            coastlines_edit.setFilePath("")
            cobs_edit.setFilePath("")
            static_polygons_edit.setFilePath("")
            continental_polygons_edit.setFilePath("")
        add_button.clicked.connect(on_add_model_click)
        
        def on_save_button_pressed():
            model_info = {}
            model_info["Name"] = name_edit.text()
            model_info["Description"] = description_text.toPlainText()
            model_info["SmallTime"] = smalltime_spinbox.value()
            model_info["BigTime"] = bigtime_spinbox.value()
            model_info["Rotations"] = rotations_edit.filePath()
            
            model_info["Layers"] = {}
            
            data_dir = cache_manager.model_data_dir
            os.makedirs(data_dir, exist_ok=True)
            model_path = os.path.join(data_dir, model_info["Name"])
            os.makedirs(model_path, exist_ok=True)
            
            rotations_src = rotations_edit.filePath()
            if rotations_src and os.path.isfile(rotations_src):
                rotations_dir =  os.path.join(model_path, "Rotations")
                os.makedirs(rotations_dir, exist_ok=True)
                rotations_dst = os.path.join(rotations_dir, os.path.basename(rotations_src))
                shutil.copy(rotations_src, rotations_dst)
                
            else:
                rotations_dst = ""
            model_info["Rotations"] = rotations_dst
            # Copy the vector layers files into the model directory
            for layer_type, file_widget in zip(["Topologies", "Coastlines", "COBs", "StaticPolygons", "ContinentalPolygons"],
                                               [topologies_edit, coastlines_edit, cobs_edit, static_polygons_edit, continental_polygons_edit]):
                layer_files = file_widget.filePath().split(' ')
                layer_files = [path.strip('"') for path in layer_files if path.strip('"')]
                layer_files_dst = []
                for layer_file in layer_files:
                    if os.path.isfile(layer_file):
                        layer_dir = os.path.join(model_path, layer_type)
                        os.makedirs(layer_dir, exist_ok=True)
                        layer_file_dst = os.path.join(layer_dir, os.path.basename(layer_file))
                        shutil.copy(layer_file, layer_file_dst)
                        layer_files_dst.append(layer_file_dst)
                if layer_files_dst != []:
                    model_info["Layers"][layer_type] = layer_files_dst
                
            metadata_file_path = os.path.join(model_path, ".metadata.json")
            json.dump(model_info, open(metadata_file_path, 'w'))
            model_list.setStringList(cache_manager.get_available_models())
            
            row = model_list.stringList().index(model_info["Name"])
            index = model_list.index(row)
            model_list_view.setCurrentIndex(index)
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).clicked.connect(on_save_button_pressed)
        
        def on_cancel_button_pressed():
            on_selection_changed(selection_model.selection(), QtCore.QItemSelection())
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).clicked.connect(on_cancel_button_pressed)
        
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
        
