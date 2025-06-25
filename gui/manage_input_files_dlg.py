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
        
        # Custom delegate to display model name with icons
        class IconItemDelegate(QtWidgets.QStyledItemDelegate):
            def paint(self, painter, option, index):
                model_name = index.data(QtCore.Qt.DisplayRole)
                symbol, _ = cache_manager.get_icon_and_tooltip(model_name)
                text = f"{model_name} {symbol}"
                
                # Draw background if selected
                if option.state & QtWidgets.QStyle.State_Selected:
                    painter.fillRect(option.rect, option.palette.highlight())
        
                # Draw text with margin
                margin = 5
                text_rect = option.rect.adjusted(margin, 0, -margin, 0)
                painter.setPen(option.palette.highlightedText().color() if option.state & QtWidgets.QStyle.State_Selected else option.palette.text().color())
                painter.drawText(text_rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, text)
        
                # Draw separator line at the bottom
                line_y = option.rect.bottom()
                painter.setPen(QtGui.QPen(option.palette.mid().color(), 1))
                painter.drawLine(option.rect.left(), line_y, option.rect.right(), line_y)
        
                painter.restore()
        
            def sizeHint(self, option, index):
                # Increase item height for bigger font and margin
                base_size = super().sizeHint(option, index)
                return QtCore.QSize(base_size.width(), base_size.height() + 8)
        
            def helpEvent(self, event, view, option, index):
                if event.type() == QtCore.QEvent.ToolTip:
                    model_name = index.data(QtCore.Qt.DisplayRole)
                    _, tip = cache_manager.get_icon_and_tooltip(model_name)
                    QtWidgets.QToolTip.showText(event.globalPos(), tip)
                    return True
                return super().helpEvent(event, view, option, index)

        model_list = QtCore.QStringListModel(cache_manager.get_available_models())
        model_list_view = QtWidgets.QListView()
        model_list_view.setModel(model_list)
        model_list_view.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        model_list_view.setItemDelegate(IconItemDelegate(model_list_view))
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
        right_side = QtWidgets.QFrame(horizontal_splitter)
        right_side.setFrameShape(QtWidgets.QFrame.StyledPanel)
        right_side.setFrameShadow(QtWidgets.QFrame.Raised)
        right_side.setLayout(QtWidgets.QVBoxLayout())
        
        # Title for model details
        details_title = QtWidgets.QLabel("Select a model to see its details")
        details_title.setStyleSheet("font-weight: bold;")
        
        # Create a horizontal layout for the title and buttons
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(details_title)
        title_layout.addStretch()
        
        download_button = QtWidgets.QPushButton()
        download_button.setToolTip("Download model")
        download_button.setIcon(QtGui.QIcon(":/download.svg"))
        download_button.hide()
        edit_button = QtWidgets.QPushButton()
        edit_button.setIcon(QtGui.QIcon(":/pencil.svg"))
        edit_button.setToolTip("Edit model information")
        edit_button.hide()
        delete_button = QtWidgets.QPushButton()
        delete_button.setToolTip("Delete model")
        delete_button.setIcon(QtGui.QIcon(":/trash.svg"))
        delete_button.hide()
        open_button = QtWidgets.QPushButton()
        open_button.setToolTip("Open in file explorer")
        open_button.setIcon(QtGui.QIcon(":/open.svg"))
        open_button.hide()
        
        title_layout.addWidget(download_button)
        title_layout.addWidget(edit_button)
        title_layout.addWidget(delete_button)
        title_layout.addWidget(open_button)

        right_side.layout().addLayout(title_layout)
        
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        right_side.layout().addWidget(separator)
        
        # Scroll area for model details
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        model_details = QtWidgets.QWidget()
        model_details.setLayout(QtWidgets.QVBoxLayout())
        model_details.layout().setContentsMargins(QtCore.QMargins(0, 0, 5, 0))
        scroll_area.setWidget(model_details)
        right_side.layout().addWidget(scroll_area)
        
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
        rotations_edit.setFilter(';;'.join(cache_manager.rotations_allowed_extensions))
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Rotations:"), 0, 0)
        layer_filewidgets.layout().addWidget(rotations_edit, 0, 1, 1, 2)
        
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Vector layers:"), 1, 0)

        topologies_edit = QgsFileWidget()
        topologies_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        topologies_edit.setFilter(';;'.join(cache_manager.layers_allowed_extensions))
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Topologies:"), 2, 1)
        layer_filewidgets.layout().addWidget(topologies_edit, 2, 2)      
        
        coastlines_edit = QgsFileWidget()
        coastlines_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        coastlines_edit.setFilter(';;'.join(cache_manager.layers_allowed_extensions))
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Coastlines:"), 3, 1)
        layer_filewidgets.layout().addWidget(coastlines_edit, 3, 2)      
        
        cobs_edit = QgsFileWidget()
        cobs_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        cobs_edit.setFilter(';;'.join(cache_manager.layers_allowed_extensions))
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("COBs:"), 4, 1)
        layer_filewidgets.layout().addWidget(cobs_edit, 4, 2)      
        
        static_polygons_edit = QgsFileWidget()
        static_polygons_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        static_polygons_edit.setFilter(';;'.join(cache_manager.layers_allowed_extensions))
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Static Polygons:"), 5, 1)
        layer_filewidgets.layout().addWidget(static_polygons_edit, 5, 2)      
        
        continental_polygons_edit = QgsFileWidget()
        continental_polygons_edit.setStorageMode(QgsFileWidget.StorageMode.GetMultipleFiles)
        continental_polygons_edit.setFilter(';;'.join(cache_manager.layers_allowed_extensions))
        layer_filewidgets.layout().addWidget(QtWidgets.QLabel("Continental Polygons:"), 6, 1)
        layer_filewidgets.layout().addWidget(continental_polygons_edit, 6, 2)      

        layer_filewidgets.hide()
        
        # Save and cancel buttons
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setText("Save changes")
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).setToolTip("Save changes to the selected model")
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setToolTip("Cancel changes and close the dialog")
        button_box.hide()
        right_side.layout().addWidget(button_box)
        
        # Function to update the model details when a model is selected
        def on_selection_changed(selected, deselected):
            name_field.hide()
            description_text.setReadOnly(True)
            
            url_edit.show()
            version_edit.show()
            
            smalltime_spinbox.hide()
            smalltime_edit.show()
            
            bigtime_spinbox.hide()
            bigtime_edit.show()
            
            layer_filewidgets.hide()
            layer_checkboxes.show()
            
            button_box.hide()
            
            if selected.indexes():
                index = selected.indexes()[0]
                model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                details_title.setText(model_name)
                
                if cache_manager.is_model_custom(model_name):
                    download_button.hide()
                    edit_button.show()
                    delete_button.show()
                    open_button.show()
                elif cache_manager.is_model_available_locally(model_name):
                    download_button.hide()
                    edit_button.hide()
                    delete_button.show()
                    open_button.show()
                else:
                    download_button.show()
                    edit_button.hide()
                    delete_button.hide()
                    open_button.hide()
                
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
                
                smalltime_edit.setEnabled(True)
                smalltime_edit.setText(str(model_dict['SmallTime']) + " Ma")
                
                bigtime_edit.setEnabled(True)
                bigtime_edit.setText(str(model_dict['BigTime']) + " Ma")
                
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
            else:
                details_title.setText("Select a model to see its details")
                
                download_button.hide()
                edit_button.hide()
                delete_button.hide()
                open_button.hide()
                
                description_text.setEnabled(False)
                description_text.setPlainText("")
                
                url_label.show()
                url_edit.show()
                url_edit.setEnabled(False)
                url_edit.setText("")
                
                version_label.show()
                version_edit.show()
                version_edit.setEnabled(False)
                version_edit.setText("")
                
                smalltime_edit.setEnabled(False)
                smalltime_edit.setText("")
                
                bigtime_edit.setEnabled(False)
                bigtime_edit.setText("")
                
                topologies_checkbox.setChecked(False)
                topologies_checkbox.setEnabled(False)
                coastlines_checkbox.setChecked(False)
                coastlines_checkbox.setEnabled(False)
                cobs_checkbox.setChecked(False)
                cobs_checkbox.setEnabled(False)
                static_polygons_checkbox.setChecked(False)
                static_polygons_checkbox.setEnabled(False)
                continental_polygons_checkbox.setChecked(False)
                continental_polygons_checkbox.setEnabled(False)

        selection_model = model_list_view.selectionModel()
        selection_model.selectionChanged.connect(on_selection_changed)
        
        # Function to handle the "Add model" button click
        def on_add_model_button_pressed():
            download_button.hide()
            edit_button.hide()
            delete_button.hide()
            open_button.hide()
            
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
            def set_minimum_bigtime():
                smalltime = smalltime_spinbox.value()
                bigtime_spinbox.setMinimum(smalltime)
            smalltime_spinbox.valueChanged.connect(set_minimum_bigtime)
                
            layer_checkboxes.hide()
            layer_filewidgets.show()
            
            topologies_edit.setFilePath("")
            coastlines_edit.setFilePath("")
            cobs_edit.setFilePath("")
            static_polygons_edit.setFilePath("")
            continental_polygons_edit.setFilePath("")
            
            button_box.show()
            button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).clicked.disconnect()
            button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).clicked.connect(on_save_button_pressed)
        add_button.clicked.connect(on_add_model_button_pressed)
        
        def on_edit_button_pressed():
            on_add_model_button_pressed()
            
            index = selection_model.currentIndex()
            model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            model_dict = cache_manager.get_model(model_name).model
            
            details_title.setText(f"Edit model: {model_name}")
            name_edit.setText(model_dict['Name'])
            description_text.setPlainText(model_dict['Description'])
            smalltime_spinbox.setValue(model_dict['SmallTime'])
            bigtime_spinbox.setValue(model_dict['BigTime'])
            
            rotations_edit.setFilePath(model_dict['Rotations'])
            
            if 'Topologies' in model_dict['Layers']:
                topologies_edit.setFilePaths(model_dict['Layers']['Topologies'])
            if 'Coastlines' in model_dict['Layers']:
                coastlines_edit.setFilePaths(model_dict['Layers']['Coastlines'])
            if 'COBs' in model_dict['Layers']:
                cobs_edit.setFilePaths(model_dict['Layers']['COBs'])
            if 'StaticPolygons' in model_dict['Layers']:
                static_polygons_edit.setFilePaths(model_dict['Layers']['StaticPolygons'])
            if 'ContinentalPolygons' in model_dict['Layers']:
                continental_polygons_edit.setFilePaths(model_dict['Layers']['ContinentalPolygons'])
            button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).clicked.disconnect()
            button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Save).clicked.connect(lambda: on_save_button_pressed(edit=True))
        edit_button.clicked.connect(on_edit_button_pressed)
        
        def on_save_button_pressed(edit=False):
            if edit:
                index = selection_model.currentIndex()
                model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                old_model_info = cache_manager.get_model(model_name).model
            
            model_info = {}
            
            if name_edit.text() == "":
                QtWidgets.QMessageBox.critical(self, "Error", "Model name cannot be empty.")
                return
            invalid_names = model_list.stringList() + cache_manager.model_list
            if edit:
                invalid_names.remove(old_model_info["Name"])
            if name_edit.text() in invalid_names:
                QtWidgets.QMessageBox.critical(self, "Error", "Model name already exists.")
                return
            
            model_info["Name"] = name_edit.text()
            
            model_info["Description"] = description_text.toPlainText()
            model_info["SmallTime"] = smalltime_spinbox.value()
            model_info["BigTime"] = bigtime_spinbox.value()
            
            model_path = os.path.join(cache_manager.model_data_dir, model_info["Name"])
            os.makedirs(model_path, exist_ok=True)
            
            rotations_src = rotations_edit.filePath()
            if rotations_src and cache_manager.is_valid_rotations_file(rotations_src):
                rotations_dir = os.path.join(model_path, "Rotations")
                os.makedirs(rotations_dir, exist_ok=True)
                rotations_dst = os.path.join(rotations_dir, os.path.basename(rotations_src))
                if os.path.abspath(rotations_src) != os.path.abspath(rotations_dst):
                    shutil.copy(rotations_src, rotations_dst)
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "Please select a valid rotations file.")
                return
            model_info["Rotations"] = rotations_dst
            
            model_info["Layers"] = {}
            
            # Copy the vector layers files into the model directory
            for layer_type, file_widget in zip(["Topologies", "Coastlines", "COBs", "StaticPolygons", "ContinentalPolygons"],
                                               [topologies_edit, coastlines_edit, cobs_edit, static_polygons_edit, continental_polygons_edit]):
                layer_files = file_widget.splitFilePaths(file_widget.filePath())
                if edit:
                    for file in old_model_info["Layers"].get(layer_type, []):
                        if file in layer_files:
                            layer_files.remove(file)
                        else:
                            os.remove(file)
                            
                layer_files_dst = []
                for layer_file in layer_files:
                    if cache_manager.is_valid_layers_file(layer_file):
                        layer_dir = os.path.join(model_path, layer_type)
                        os.makedirs(layer_dir, exist_ok=True)
                        layer_file_dst = os.path.join(layer_dir, os.path.basename(layer_file))
                        shutil.copy(layer_file, layer_file_dst)
                        layer_files_dst.append(layer_file_dst)
                    else:
                        QtWidgets.QMessageBox.critical(self, "Error", f"Please select valid {layer_type} files.")
                        return
                if layer_files_dst != []:
                    model_info["Layers"][layer_type] = layer_files_dst
                
            metadata_file_path = os.path.join(model_path, ".metadata.json")
            json.dump(model_info, open(metadata_file_path, 'w'))
            
            if edit and model_info["Name"] != old_model_info["Name"]:
                shutil.rmtree(os.path.join(cache_manager.model_data_dir, old_model_info["Name"]))
            
            model_list.setStringList(cache_manager.get_available_models())
            row = model_list.stringList().index(model_info["Name"])
            index = model_list.index(row)
            model_list_view.setCurrentIndex(index)
            
            if edit:
                QtWidgets.QMessageBox.information(self, "Success", f"Model '{model_info['Name']}' updated successfully.")
            else:
                QtWidgets.QMessageBox.information(self, "Success", f"Model '{model_info['Name']}' added successfully.")
        
        def on_cancel_button_pressed():
            on_selection_changed(selection_model.selection(), QtCore.QItemSelection())
        button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).clicked.connect(on_cancel_button_pressed)
        
        def on_download_button_pressed():
            index = model_list_view.currentIndex()
            model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            
            progress = QtWidgets.QProgressDialog("Downloading model...", "Cancel", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()

            class DownloadThread(QtCore.QThread):
                error = QtCore.pyqtSignal(str)
                def __init__(self):
                    super().__init__()
                    self.has_error = False
                    
                def run(self):
                    try:
                        cache_manager.download_model(model_name)
                        cache_manager.download_all_layers(model_name)
                    except Exception as e:
                        self.has_error = True
                        self.error.emit(str(e))
            self.download_thread = DownloadThread()

            def on_finished():
                progress.close()
                if not self.download_thread.has_error:
                    QtWidgets.QMessageBox.information(self, "Success", f"Model '{model_name}' downloaded successfully.")
                    on_selection_changed(selection_model.selection(), QtCore.QItemSelection())
                
            def on_error(error_msg):
                progress.close()
                QtWidgets.QMessageBox.critical(self, "Error", error_msg)

            progress.canceled.connect(self.download_thread.terminate)
            self.download_thread.finished.connect(on_finished)
            self.download_thread.error.connect(on_error)
            self.download_thread.start()
            
        download_button.clicked.connect(on_download_button_pressed)
        
        def on_delete_button_pressed():
            index = model_list_view.currentIndex()
            model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            reply = QtWidgets.QMessageBox.question(self, "Delete Model", f"Are you sure you want to delete the model '{model_name}'?",
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                try:
                    cache_manager.delete_model(model_name)
                    model_list.setStringList(cache_manager.get_available_models())
                    on_selection_changed(QtCore.QItemSelection(), selection_model.selection())
                    QtWidgets.QMessageBox.information(self, "Success", f"Model '{model_name}' deleted successfully.")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", str(e))
        delete_button.clicked.connect(on_delete_button_pressed)
        
        def on_open_button_pressed():
            index = model_list_view.currentIndex()
            model_name = model_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            try:
                model_path = cache_manager.get_model(model_name).get_model_dir()
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(model_path))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
        open_button.clicked.connect(on_open_button_pressed)
        
        # Rasters section
        rasters_groupbox = QgsCollapsibleGroupBox("Present day raster files", vertical_splitter)
        rasters_groupbox.setLayout(QtWidgets.QVBoxLayout())
        
        raster_list = QtCore.QStringListModel(cache_manager.get_available_rasters())
        raster_list_view = QtWidgets.QListView()
        raster_list_view.setModel(raster_list)
        raster_list_view.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        raster_list_view.setItemDelegate(IconItemDelegate(raster_list_view))
        rasters_groupbox.layout().addWidget(raster_list_view)
        
        download_raster_button = QtWidgets.QPushButton("Download raster")
        download_raster_button.setIcon(QtGui.QIcon(":/download.svg"))
        download_raster_button.setEnabled(False)
        delete_raster_button = QtWidgets.QPushButton("Delete raster")
        delete_raster_button.setIcon(QtGui.QIcon(":/trash.svg"))
        delete_raster_button.setEnabled(False)
        open_raster_button = QtWidgets.QPushButton("Open folder")
        open_raster_button.setIcon(QtGui.QIcon(":/open.svg"))
        open_raster_button.setEnabled(False)
        
        raster_buttons_layout = QtWidgets.QHBoxLayout()
        raster_buttons_layout.addStretch()
        raster_buttons_layout.addWidget(download_raster_button)
        raster_buttons_layout.addWidget(delete_raster_button)
        raster_buttons_layout.addWidget(open_raster_button)
        rasters_groupbox.layout().addLayout(raster_buttons_layout)
        
        def on_raster_selection_changed(selected, deselected):
            if selected.indexes():
                index = selected.indexes()[0]
                raster_name = raster_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                if cache_manager.is_raster_available_locally(raster_name):
                    download_raster_button.setEnabled(False)
                    delete_raster_button.setEnabled(True)
                    open_raster_button.setEnabled(True)
                else:
                    download_raster_button.setEnabled(True)
                    delete_raster_button.setEnabled(False)
                    open_raster_button.setEnabled(False)
            else:
                download_raster_button.setEnabled(False)
                delete_raster_button.setEnabled(False)
                open_raster_button.setEnabled(False)
        raster_selection_model = raster_list_view.selectionModel()
        raster_selection_model.selectionChanged.connect(on_raster_selection_changed)
        
        def on_download_raster_button_pressed():
            index = raster_list_view.currentIndex()
            raster_name = raster_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            
            progress = QtWidgets.QProgressDialog("Downloading raster...", "Cancel", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()

            class DownloadRasterThread(QtCore.QThread):
                error = QtCore.pyqtSignal(str)
                def __init__(self):
                    super().__init__()
                    self.has_error = False
                    
                def run(self):
                    try:
                        cache_manager.download_raster(raster_name)
                    except Exception as e:
                        self.has_error = True
                        self.error.emit(str(e))
            self.download_raster_thread = DownloadRasterThread()

            def on_finished():
                progress.close()
                if not self.download_raster_thread.has_error:
                    QtWidgets.QMessageBox.information(self, "Success", f"Raster '{raster_name}' downloaded successfully.")
                    on_raster_selection_changed(raster_selection_model.selection(), QtCore.QItemSelection())
                
            def on_error(error_msg):
                progress.close()
                self.download_raster_thread.terminate()
                QtWidgets.QMessageBox.critical(self, "Error", error_msg)

            progress.canceled.connect(self.download_raster_thread.terminate)
            self.download_raster_thread.finished.connect(on_finished)
            self.download_raster_thread.error.connect(on_error)
            self.download_raster_thread.start()
        download_raster_button.clicked.connect(on_download_raster_button_pressed)
        
        def on_delete_raster_button_pressed():
            index = raster_list_view.currentIndex()
            raster_name = raster_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            reply = QtWidgets.QMessageBox.question(self, "Delete Raster", f"Are you sure you want to delete the raster '{raster_name}'?",
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                try:
                    cache_manager.delete_raster(raster_name)
                    raster_list.setStringList(cache_manager.get_available_rasters())
                    on_raster_selection_changed(QtCore.QItemSelection(), raster_selection_model.selection())
                    QtWidgets.QMessageBox.information(self, "Success", f"Raster '{raster_name}' deleted successfully.")
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, "Error", str(e))
        delete_raster_button.clicked.connect(on_delete_raster_button_pressed)
        
        def on_open_raster_button_pressed():
            index = raster_list_view.currentIndex()
            raster_name = raster_list.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
            try:
                raster_path = cache_manager.get_raster_path(raster_name)
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(raster_path))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
        open_raster_button.clicked.connect(on_open_raster_button_pressed)
        
        if cache_manager.get_available_rasters() == []:
            rasters_groupbox.hide()
        
        vertical_splitter.setSizes([400, 200])
        
