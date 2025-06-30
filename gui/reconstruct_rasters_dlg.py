#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from PyQt5.QtWidgets import QComboBox
from PyQt5 import QtCore
from qgis.gui import QgsDoubleSpinBox
from .base_dialog import TaBaseDialog
from .widgets import TaSpinBox, TaCheckBox,TaRasterLayerComboBox
from ..core.cache_manager import cache_manager
import tempfile
import os

class TaReconstructRastersDlg(TaBaseDialog):
    
    def __init__(self, parent = None):
        """Constructor."""
        super(TaReconstructRastersDlg, self).__init__(parent)
        self.defineParameters()
        
    def reloadHelp(self):
        """
        Sets the name of the chosen processing algorithm to the dialog so that it can load the help
        file properly.
        """
        processing_alg_names = [("Topography", "TaReconstructTopography"),
                                ("Agegrid", "TaReconstructAgegrid")]
        for alg, name in processing_alg_names:
            if self.rasterType.currentText() == alg:
                self.setDialogName(name)
        self.loadHelp()

    def defineParameters(self):
        """ Adds parameters to a list object that is used by the TaBaseDialog
        class to create widgets and place them parameters tab.
        """
        # Raster Type:
        self.rasterType = self.addMandatoryParameter(QComboBox,
                                                     "Type of raster to reconstruct:")
        self.rasterType.addItems(['Topography', 'Agegrid'])
        self.rasterType.currentTextChanged.connect(self.reloadHelp)
        
        # Rotation Model:
        self.modelName = self.addMandatoryParameter(QComboBox,
                                                    "Name of rotation model:")
        self.modelName.setStyleSheet("combobox-popup: 0;")
        def set_available_models(raster_type):
            if raster_type == "Topography":
                self.modelName.clear()
                model_list = cache_manager.get_available_models(
                    required_layers=["Topologies", "StaticPolygons"])
                
            elif raster_type == "Agegrid":
                self.modelName.clear()
                model_list = cache_manager.get_available_models(
                    required_layers=["Topologies", "StaticPolygons", "COBs"])
                
            for model in model_list:
                self.modelName.addItem(model)
                
                symbol, tooltip = cache_manager.get_icon_and_tooltip(model)
                
                display_text = f"{model} {symbol}"
                
                index = self.modelName.count() - 1
                self.modelName.setItemData(index, display_text, QtCore.Qt.DisplayRole)
                self.modelName.setItemData(index, tooltip, QtCore.Qt.ToolTipRole)
                self.modelName.setItemData(index, model, QtCore.Qt.UserRole)
        self.rasterType.currentTextChanged.connect(set_available_models)
        set_available_models("Topography")
        
        # Topography specific parameters:
        ## Input raster:
        self.inputRaster = self.addVariantParameter(QComboBox, "Topography",
                                                    "Input raster:")
        raster_list = cache_manager.get_available_rasters()
        for raster in raster_list:
            self.inputRaster.addItem(raster)
            symbol, tooltip = cache_manager.get_icon_and_tooltip(raster)
            display_text = f"{raster} {symbol}"
            index = self.inputRaster.count() - 1
            self.inputRaster.setItemData(index, display_text, QtCore.Qt.DisplayRole)
            self.inputRaster.setItemData(index, tooltip, QtCore.Qt.ToolTipRole)
            self.inputRaster.setItemData(index, raster, QtCore.Qt.UserRole)
        self.inputRaster.addItem('Local')
        index = self.inputRaster.count() - 1
        self.inputRaster.setItemData(index, 'Local', QtCore.Qt.UserRole)
        
        self.localLayer = self.addVariantParameter(TaRasterLayerComboBox, "Topography",
                                                   "Select a local raster layer:")
        
        ## Reconstruction time:
        self.reconstruction_time = self.addVariantParameter(TaSpinBox, "Topography",
                                                            "Reconstruction time (in Ma):")
        self.reconstruction_time.setDataType("integer")
        def set_minimum_reconstruction_time():
            model_smalltime = cache_manager.get_model_smalltime(self.modelName.currentData(QtCore.Qt.UserRole))
            self.reconstruction_time.spinBox.setMinimum(model_smalltime)
        set_minimum_reconstruction_time()
        self.modelName.currentIndexChanged.connect(set_minimum_reconstruction_time)
        self.reconstruction_time.spinBox.setMinimum(0)
        def set_maximum_reconstruction_time():
            model_bigtime = cache_manager.get_model_bigtime(self.modelName.currentData(QtCore.Qt.UserRole))
            self.reconstruction_time.spinBox.setMaximum(model_bigtime)
        set_maximum_reconstruction_time()
        self.modelName.currentIndexChanged.connect(set_maximum_reconstruction_time)
        
        ## Resampling:
        self.resampling = self.addVariantParameter(TaCheckBox,
                                                   "Topography",
                                                   "Do resampling:")
        self.resampling.setChecked(True)
         
        ## Resampling Resolution:
        self.resampling_resolution = self.addVariantParameter(QgsDoubleSpinBox, "Topography",
                                                             "Resampling resolution (in arc degrees):")
        self.resampling_resolution.setValue(0.5)
                
        ## Interpolation method:
        self.interpolationMethod = self.addAdvancedParameter(QComboBox,
                                                             "Interpolation method:",
                                                             variant_index="Topography")
        self.interpolationMethod.addItems(['linear',
                                           'square',
                                           'cubic',
                                           '4th degree',
                                           '5th degree'])
        self.resampling.registerEnabledWidgets([self.resampling_resolution, self.interpolationMethod])
        
        # Bathymetry specific parameters:
        ## Starting time:
        self.startTime = self.addVariantParameter(TaSpinBox, "Agegrid",
                                                  "Start Time (in Ma)")
        self.startTime.setDataType("integer")        
        def set_maximum_start_time():
            model_bigtime = cache_manager.get_model_bigtime(self.modelName.currentData(QtCore.Qt.UserRole))
            self.startTime.spinBox.setMaximum(model_bigtime)
        set_maximum_start_time()
        self.modelName.currentIndexChanged.connect(set_maximum_start_time)
        
        ## End time
        self.endTime = self.addVariantParameter(TaSpinBox, "Agegrid",
                                                "End Time (in Ma)")
        self.endTime.setDataType("integer")
        self.endTime.spinBox.setMinimum(0)
        def set_maximum_end_time():
            model_bigtime = cache_manager.get_model_bigtime(self.modelName.currentData(QtCore.Qt.UserRole))
            self.endTime.spinBox.setMaximum(model_bigtime - 1)
        set_maximum_end_time()
        self.modelName.currentIndexChanged.connect(set_maximum_end_time)
        
        def set_minimum_start_time():
            self.startTime.spinBox.setMinimum(self.endTime.spinBox.value() + 1)
        set_minimum_start_time()
        self.endTime.spinBox.valueChanged.connect(set_minimum_start_time)
        
        ## Time Step
        self.timeStep = self.addVariantParameter(TaSpinBox, "Agegrid",
                                                 "Time step (in Ma)")
        self.timeStep.setDataType("integer")
        self.timeStep.spinBox.setMinimum(1)
        
        ## Spatial Resolution
        self.resolution = self.addVariantParameter(QgsDoubleSpinBox,
                                                   "Agegrid",
                                                   "Spacial resolution (in arc degrees):")
        self.resolution.setValue(0.5)
        
        ## Convert to Bathymetry
        self.convertToBathymetry = self.addVariantParameter(TaCheckBox,
                                                            "Agegrid",
                                                            "Automatically convert to bathymetry:")
        self.convertToBathymetry.setChecked(True)
        
        # Advanced Parameters
        ## Extent
        self.minlon = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Minimum longitude (in arc degrees):")
        self.minlon.setMinimum(-180)
        self.minlon.setMaximum(179)
        self.minlon.setValue(-180)
        
        self.maxlon = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Maximum longitude (in arc degrees):")
        def set_minimum_maxlon():
            self.maxlon.setMinimum(int(self.minlon.value()) + 1)
        set_minimum_maxlon()
        self.minlon.valueChanged.connect(set_minimum_maxlon)
        self.maxlon.setMaximum(180)
        self.maxlon.setValue(180)
        
        self.minlat = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Minimum latitude (in arc degrees):")
        self.minlat.setMinimum(-90)
        self.minlat.setMaximum(89)
        self.minlat.setValue(-90)
        
        self.maxlat = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Maximum latitude (in arc degrees):")
        def set_minimum_maxlat():
            self.maxlat.setMinimum(int(self.minlat.value()) + 1)
        set_minimum_maxlat()
        self.minlat.valueChanged.connect(set_minimum_maxlat)
        self.maxlat.setMaximum(90)
        self.maxlat.setValue(90)
        
        ## Threads
        self.threads = self.addAdvancedParameter(TaSpinBox,
                                                 "Number of threads to use during reconstruction:")
        self.threads.spinBox.setMinimum(1)
        
        ## Spreading rate
        self.spreading_rate = self.addAdvancedParameter(
            QgsDoubleSpinBox, "Initial ocean spreading rate (mm/yr):",
            variant_index="Agegrid")
        self.spreading_rate.setMinimum(0)
        self.spreading_rate.setMaximum(1000)
        self.spreading_rate.setValue(75.)
        
        # Fill the parameters' tab of the Dialog with the defined parameters
        self.fillDialog()
        self.showVariantWidgets(self.rasterType.currentText())
        self.rasterType.currentTextChanged.connect(self.showVariantWidgets)
        
        # Hide local raster widget if it is not selected
        def input_raster_changed():
            if self.inputRaster.currentText() == "Local":
                self.localLayer.show()
            else:
                self.localLayer.hide()
        self.inputRaster.currentTextChanged.connect(input_raster_changed)
        self.rasterType.currentTextChanged.connect(input_raster_changed)
        input_raster_changed()
        
        # Update output path when parameters change
        def update_output_path(_):
            raster_type = self.rasterType.currentText()
            if raster_type == "Topography":
                reconstruction_time = self.reconstruction_time.spinBox.value()
            elif raster_type == "Agegrid":
                reconstruction_time = self.endTime.spinBox.value()
                if self.convertToBathymetry.isChecked():
                    raster_type = "Bathymetry"
            model_name = self.modelName.currentData(QtCore.Qt.UserRole)
            path = os.path.join(tempfile.gettempdir(),
                                f"{raster_type}_{reconstruction_time}.0_{model_name}.nc")
            self.outputPath.lineEdit().setPlaceholderText(path)
            self.outputPath.setFilter('*.nc')
        
        self.rasterType.currentTextChanged.connect(update_output_path)
        self.modelName.currentTextChanged.connect(update_output_path)
        self.reconstruction_time.spinBox.valueChanged.connect(update_output_path)
        self.endTime.spinBox.valueChanged.connect(update_output_path)
        self.convertToBathymetry.stateChanged.connect(update_output_path)
        self.setDefaultOutFilePath = update_output_path
