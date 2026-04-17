# Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
# Full copyright notice in file: terra_antiqua.py


from PyQt5 import QtCore, QtWidgets

import os
import shutil
from PyQt5.QtWidgets import (
    QComboBox,
    QPushButton,
    QFileDialog
)

from qgis.gui import QgsSpinBox, QgsDoubleSpinBox
from qgis.core import QgsMapLayerProxyModel
from .base_dialog import TaBaseDialog
from .widgets import (
    TaRasterLayerComboBox,
    TaMapLayerComboBox,
    TaCheckBox,
    TaSpinBox,
    TaVectorLayerComboBox,
    TaColorSchemeWidget
)
from ..core.cache_manager import cache_manager


class TaStandardProcessingDlg(TaBaseDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(TaStandardProcessingDlg, self).__init__(parent)
        self.defineParameters()
        self.processingTypeBox.currentTextChanged.connect(self.reloadHelp)
        self.reloadHelp()

    def defineParameters(self):
        self.processingTypeBox = self.addParameter(
            QComboBox, "How would you like to process the input layer?")
        self.processingTypeBox.addItems(["Fill gaps",
                                         "Copy/Paste raster",
                                         "Smooth raster",
                                         "Isostatic compensation",
                                         "Set new sea level",
                                         "Calculate bathymetry",
                                         "Change map symbology",
                                         "Assign plate IDs"])
        self.baseTopoBox = self.addMandatoryParameter(TaMapLayerComboBox,
                                                      "Input layer:",
                                                      "TaMapLayerComboBox")
        self._rasterProcessingTypes = ["Fill gaps", "Copy/Paste raster",
                                        "Smooth raster", "Isostatic compensation",
                                        "Set new sea level", "Calculate bathymetry",
                                        "Change map symbology"]
        # Parameters for filling the gaps
        self.fillingTypeBox = self.addVariantParameter(QComboBox,
                                                       "Fill gaps",
                                                       "Filling type:")
        self.fillingTypeBox.addItems(["Interpolation",
                                      "Fixed value"])
        self.fillingValueSpinBox = self.addVariantParameter(QgsDoubleSpinBox,
                                                            "Fill gaps",
                                                            "Filling value:")
        self.fillingValueSpinBox.setMaximum(99999)
        self.fillingValueSpinBox.setMinimum(-99999)
        self.fillingValueSpinBox.setValue(9999)
        self.interpInsidePolygonCheckBox = self.addVariantParameter(TaCheckBox,
                                                                    "Fill gaps",
                                                                    "Fill inside polygon(s) only.")
        self.masksBox = self.addVariantParameter(TaVectorLayerComboBox,
                                                 "Fill gaps",
                                                 "Mask layer:",
                                                 "TaMapLayerComboBox")
        self.interpInsidePolygonCheckBox.registerEnabledWidgets([
                                                                self.masksBox])
        self.smoothingBox = self.addVariantParameter(TaCheckBox, "Fill gaps",
                                                     "Smooth the resulting raster")
        self.smoothingTypeBox = self.addVariantParameter(QtWidgets.QComboBox,
                                                         "Fill gaps",
                                                         "Smoothing type:")
        self.smoothingTypeBox.addItems(["Gaussian filter",
                                        "Uniform filter"])
        self.smFactorSpinBox = self.addVariantParameter(QgsSpinBox,
                                                        "Fill gaps",
                                                        "Smoothing factor (in grid cells):")
        self.smFactorSpinBox.setMinimum(1)
        self.smFactorSpinBox.setMaximum(5)

        self.smoothingBox.registerEnabledWidgets([self.smoothingTypeBox,
                                                  self.smFactorSpinBox])

        # Parameters for Copying and pasting raster data
        self.copyFromRasterBox = self.addVariantParameter(TaRasterLayerComboBox,
                                                          "Copy/Paste raster",
                                                          "Raster to copy values from:",
                                                          "TaMapLayerComboBox",
                                                          mandatory=True)
        self.copyFromMaskBox = self.addVariantParameter(TaVectorLayerComboBox,
                                                        "Copy/Paste raster",
                                                        "Mask layer:",
                                                        "TaMapLayerComboBox",
                                                        mandatory=True)
        self.copyPasteSelectedFeaturesOnlyCheckBox = self.addVariantParameter(TaCheckBox,
                                                                              "Copy/Paste raster",
                                                                              "Selected features only")
        self.copyPasteSelectedFeaturesOnlyCheckBox.registerLinkedWidget(
            self.copyFromMaskBox)

        # Parameters for smothing rasters
        self.smoothInPolygonCheckBox = self.addVariantParameter(TaCheckBox,
                                                                "Smooth raster",
                                                                "Smooth inside polygon(s) only.")
        self.smoothInPolygonCheckBox.stateChanged.connect(
            self.onSmoothInPolygonCheckBoxStateChange)
        self.smoothingMaskBox = self.addVariantParameter(TaVectorLayerComboBox,
                                                         "Smooth raster",
                                                         "Mask layer:",
                                                         "TaMapLayerComboBox")
        self.smoothingMaskBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.smoothingMaskBox.layerChanged.connect(self.setFieldsInLayer)
        self.smoothInPolygonCheckBox.registerEnabledWidgets(
            [self.smoothingMaskBox])
        self.smoothInSelectedFeaturesOnlyCheckBox = self.addVariantParameter(TaCheckBox,
                                                                             "Smooth raster",
                                                                             "Selected features only.")
        self.smoothInSelectedFeaturesOnlyCheckBox.registerLinkedWidget(
            self.smoothingMaskBox)

        self.smoothingTypeBox2 = self.addVariantParameter(QtWidgets.QComboBox,
                                                          "Smooth raster",
                                                          "Smoothing type:")
        self.smFactorSpinBox2 = self.addVariantParameter(TaSpinBox,
                                                         "Smooth raster",
                                                         "Smoothing factor (in grid cells):")
        self.smoothingTypeBox2.addItems(["Gaussian filter",
                                         "Uniform filter"])
        self.smFactorSpinBox2.setAllowedValueRange(1, 5)
        self.fixedPaleoShorelinesCheckBox = self.addAdvancedParameter(TaCheckBox,
                                                                      label="Set paleoshorelines fixed.",
                                                                      variant_index="Smooth raster")
        self.fixedPaleoShorelinesCheckBox.stateChanged.connect(
            self.onFixedPaleoshorelinesCheckBoxStateChange)
        self.paleoshorelinesMask = self.addAdvancedParameter(TaVectorLayerComboBox,
                                                             label="Rotated paleoshorelines:",
                                                             widget_type="TaMapLayerComboBox",
                                                             variant_index="Smooth raster")
        self.paleoshorelinesMask.setLayerType("Polygon")
        self.fixedPaleoShorelinesCheckBox.registerEnabledWidgets(
            [self.paleoshorelinesMask])

        # Parameters for Isostatic compensation
        self.selectIceTopoBox = self.addVariantParameter(TaRasterLayerComboBox,
                                                         "Isostatic compensation",
                                                         "Ice topography raster:",
                                                         mandatory=True)
        self.isostatMaskBox = self.addAdvancedParameter(TaVectorLayerComboBox,
                                                        label="Mask layer:",
                                                        widget_type="TaMapLayerComboBox",
                                                        variant_index="Isostatic compensation")
        self.isostatMaskSelectedFeaturesCheckBox = self.addAdvancedParameter(TaCheckBox,
                                                                             label="Selected features only",
                                                                             variant_index="Isostatic compensation")
        self.isostatMaskSelectedFeaturesCheckBox.registerLinkedWidget(
            self.isostatMaskBox)

        self.masksFromCoastCheckBox = self.addAdvancedParameter(
            TaCheckBox,
            label="Get polar regions automatically.",
            variant_index="Isostatic compensation")
        self.isostatMaskSelectedFeaturesCheckBox.registerEnabledWidgets(
            [self.masksFromCoastCheckBox], natural=True)

        self.iceAmountSpinBox = self.addVariantParameter(
            QgsSpinBox,
            "Isostatic compensation",
            "Amount of the ice to be removed (in %)"
        )
        self.iceAmountSpinBox.setMinimum(0)
        self.iceAmountSpinBox.setMaximum(100)
        self.iceAmountSpinBox.setValue(30)

        # Parameters for Setting sea level
        self.seaLevelShiftBox = self.addVariantParameter(QgsSpinBox,
                                                         "Set new sea level",
                                                         "Amount of sea level shift (m):")
        self.seaLevelShiftBox.setMinimum(-1000)
        self.seaLevelShiftBox.setMaximum(1000)
        self.seaLevelShiftBox.setValue(100)

        # Parameters for calculating bathymetry from ocean age
        self.ageRasterTime = self.addVariantParameter(QgsSpinBox,
                                                      "Calculate bathymetry",
                                                      "Time of the age raster:")
        self.ageRasterTime.setValue(0)
        self.ageRasterTime.setMaximum(20000)
        self.reconstructionTime = self.addVariantParameter(QgsSpinBox,
                                                           "Calculate bathymetry",
                                                           "Reconstruction time:")
        self.reconstructionTime.setMaximum(20000)

        # Parameters for changing map symbology
        self.colorPalette = self.addVariantParameter(
            TaColorSchemeWidget, "Change map symbology", "Color palette:")
        self.addColorPaletteButton = self.addVariantParameter(QPushButton,
                                                              "Change map symbology",
                                                              "Add custom color palette")
        self.addColorPaletteButton.pressed.connect(self.addColorPalette)

        # Parameters for Assign plate IDs
        self.assignPlateIDsModelName = self.addVariantParameter(
            QComboBox, "Assign plate IDs", "Name of rotation model:")
        self.assignPlateIDsModelName.setStyleSheet("combobox-popup: 0;")
        model_list = cache_manager.get_available_models(
            required_layers=["Static Polygons"])
        for model in model_list:
            self.assignPlateIDsModelName.addItem(model)
            symbol, tooltip = cache_manager.get_icon_and_tooltip(model)
            display_text = f"{model} {symbol}"
            index = self.assignPlateIDsModelName.count() - 1
            self.assignPlateIDsModelName.setItemData(
                index, display_text, QtCore.Qt.DisplayRole)
            self.assignPlateIDsModelName.setItemData(
                index, tooltip, QtCore.Qt.ToolTipRole)
            self.assignPlateIDsModelName.setItemData(
                index, model, QtCore.Qt.UserRole)

        self.assignPlateIDsTime = self.addVariantParameter(
            TaSpinBox, "Assign plate IDs", "Time of the input layer (in Ma):")
        self.assignPlateIDsTime.setDataType("integer")
        self.assignPlateIDsTime.spinBox.setMinimum(0)
        self.assignPlateIDsTime.spinBox.setMaximum(20000)

        self.assignPlateIDsMethodBox = self.addVariantParameter(
            QComboBox, "Assign plate IDs", "Partition method:")
        self.assignPlateIDsMethodBox.addItems(
            ["Split into plates", "Most overlapping plate"])

        self.fillDialog()
        self.showVariantWidgets(self.processingTypeBox.currentText())
        self.processingTypeBox.currentTextChanged.connect(
            self.showVariantWidgets)
        self.processingTypeBox.currentTextChanged.connect(
            self.configureInputLayer)
        self.configureInputLayer(self.processingTypeBox.currentText())
        self.group_box.collapsedStateChanged.connect(
            lambda: self.showAdvancedWidgets(self.processingTypeBox.currentText()))

    def configureInputLayer(self, processing_type):
        """Reconfigures baseTopoBox filter, label, open button and output file filter
        based on the selected processing type."""
        # baseTopoBox is the inner cmb; its parent() is the TaMapLayerComboBox widget
        container = self.baseTopoBox.parent()
        # Disconnect previous open button connections
        try:
            container.openButton.pressed.disconnect()
        except (TypeError, RuntimeError):
            pass
        if processing_type == "Assign plate IDs":
            self.baseTopoBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
            if hasattr(container, 'setLabel'):
                container.setLabel("Input layer: *")
            container.openButton.pressed.connect(self._openVectorFromDisk)
            try:
                self.outputPath.setFilter('*.shp')
            except Exception:
                pass
        else:
            self.baseTopoBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
            if hasattr(container, 'setLabel'):
                container.setLabel("Raster to be modified: *")
            container.openButton.pressed.connect(self._openRasterFromDisk)
            try:
                self.outputPath.setFilter('*.tif;;*.tiff')
            except Exception:
                pass

    def _openRasterFromDisk(self):
        """Opens a file dialog to select a raster layer from disk."""
        from qgis.core import QgsRasterLayer, QgsProject
        fd = QFileDialog()
        filt = "Raster files (*.jpg *.tif *.grd *.nc *.png *.tiff)"
        fname, _ = fd.getOpenFileName(
            caption='Select a raster layer', directory=None, filter=filt)
        if fname:
            name, _ = os.path.splitext(os.path.basename(fname))
            rlayer = QgsRasterLayer(fname, name, 'gdal')
            QgsProject.instance().addMapLayer(rlayer)
            self.baseTopoBox.setLayer(rlayer)

    def _openVectorFromDisk(self):
        """Opens a file dialog to select a vector layer from disk."""
        from qgis.core import QgsVectorLayer, QgsProject
        fd = QFileDialog()
        filt = "Vector files (*.shp *.gpml *.gpmlz *.geojson *.json *.gpkg *.gmt)"
        fname, _ = fd.getOpenFileName(
            caption='Select a vector layer', directory=None, filter=filt)
        if fname:
            name, _ = os.path.splitext(os.path.basename(fname))
            vlayer = QgsVectorLayer(fname, name, 'ogr')
            QgsProject.instance().addMapLayer(vlayer)
            self.baseTopoBox.setLayer(vlayer)

    def setFieldsInLayer(self):
        self.smFactorSpinBox2.initOverrideButton("Smoothing factor", "Smoothing factor for each mask",
                                                 self.smoothingMaskBox.currentLayer())

    def onSmoothInPolygonCheckBoxStateChange(self, state):
        if state == QtCore.Qt.Checked:
            self.smoothingMaskBox.setLayer(self.smoothingMaskBox.layer(1))
        else:
            self.smoothingMaskBox.setLayer(self.smoothingMaskBox.layer(0))

    def onFixedPaleoshorelinesCheckBoxStateChange(self, state):
        if state == QtCore.Qt.Checked:
            self.paleoshorelinesMask.setLayer(self.smoothingMaskBox.layer(1))
        else:
            self.paleoshorelinesMask.setLayer(self.smoothingMaskBox.layer(0))

    def addColorPalette(self) -> bool:
        """Adds a custom color palette to TA resources folder and to displays its name in the color palettes' combobox.

        :return: True if added successfully, otherwise False.
        :rtype: bool.
        """
        fd = QFileDialog()
        filter = "Color palette files (*.cpt)"
        fname, _ = fd.getOpenFileName(
            caption='Select color palette', directory=None, filter=filter)
        if fname:
            ext = os.path.splitext(fname)[1]
        else:
            return False
        if ext != '.cpt':
            return False

        color_lines = []
        comment_lines = []
        bottom_lines = []
        color_model = None
        with open(fname) as file:
            lines = file.readlines()
            color_scheme_name = lines[0].strip()
            color_scheme_name = color_scheme_name.replace("#", "")
            for line_no, line in enumerate(lines):
                new_line = line.strip()
                if new_line and not any([new_line[0] == '#',
                                         new_line[0] == 'B',
                                         new_line[0] == 'F',
                                         new_line[0] == 'N']):
                    new_line = new_line.split()
                    new_line = [i for i in new_line if i]
                    color_lines.append(new_line)
                elif new_line and new_line[0] == '#':
                    if "COLOR_MODEL" in new_line:
                        color_model = new_line.split('=')[1].strip()
                    comment_lines.append(new_line)
                elif new_line and any([
                        new_line[0] == 'B',
                        new_line[0] == 'F',
                        new_line[0] == 'N']):
                    bottom_lines.append(new_line)
        if color_model == 'HSV':
            self.msgBar.pushWarning("Warning:",
                                    "The selected color palette has an HSV color model, which is currently not supported.")
            return False

        if len(color_lines[0]) > 4:
            new_color_lines = []
            for line in color_lines:
                new_line = []
                new_line.append(line[0])
                new_line.append(str(line[1])+'/'+str(line[2])+'/'+str(line[3]))
                new_line.append(line[4])
                new_line.append(str(line[5])+'/'+str(line[6])+'/'+str(line[7]))
                new_color_lines.append(new_line)
            color_lines = new_color_lines

            new_file_name = os.path.join(self.colorPalette.path_to_color_schemes,
                                         os.path.basename(fname))
            with open(new_file_name, mode='w') as f:
                for line in comment_lines:
                    f.write(line)
                    f.write("\n")
                for line in color_lines:
                    for no, i in enumerate(line):
                        f.write(i)
                        if not no == len(line):
                            f.write("\t")
                    f.write("\n")
                for no, line in enumerate(bottom_lines):
                    f.write(line)
                    if not no == len(bottom_lines):
                        f.write("\n")

        else:
            try:
                shutil.copy(fname, self.colorPalette.path_to_color_schemes)
            except Exception as e:
                return False

        if self.colorPalette.findText(color_scheme_name) == -1:
            self.colorPalette.addItem(color_scheme_name)
        else:
            self.msgBar.pushWarning("Warning:",
                                    "A color palette with this name is already added.")
        self.colorPalette.setCurrentText(color_scheme_name)
        return True

    def reloadHelp(self):
        """
        Sets the name of the chosen processing algorithm (e.g. Smooth raster) to the dialog so that it can load the help
        file properly."""
        processing_alg_names = [("Fill gaps", "TaFillGaps"),
                                ("Copy/Paste raster", "TaCopyPasteRaster"),
                                ("Smooth raster", "TaSmoothRaster"),
                                ("Isostatic compensation",
                                 "TaIsostaticCompensation"),
                                ("Set new sea level", "TaSetSeaLevel"),
                                ("Calculate bathymetry", "TaCalculateBathymetry"),
                                ("Change map symbology", "TaChangeMapSymbology"),
                                ("Assign plate IDs", "TaAssignPlateIDs")]
        for alg, name in processing_alg_names:
            if self.processingTypeBox.currentText() == alg:
                self.setDialogName(name)
        if self.processingTypeBox.currentText() == "Change map symbology":
            self.outputPath.hide()
            self.outputPathLabel.hide()
        else:
            self.outputPath.show()
            self.outputPathLabel.show()
        self.loadHelp()
