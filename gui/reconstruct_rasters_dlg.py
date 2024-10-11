#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from PyQt5.QtWidgets import QComboBox
from qgis.gui import QgsDoubleSpinBox
from .base_dialog import TaBaseDialog
from .widgets import TaSpinBox, TaCheckBox
from plate_model_manager import PlateModelManager

class TaReconstructRastersDlg(TaBaseDialog):
    pm_manager = PlateModelManager()
    model_list = pm_manager.get_available_model_names()[1:]
        
    def __init__(self, parent = None):
        """Constructor."""
        super(TaReconstructRastersDlg, self).__init__(parent)
        self.defineParameters()

    def defineParameters(self):
        """ Adds parameters to a list object that is used by the TaBaseDialog
        class to create widgets and place them parameters tab.
        """
        # Raster Type:
        self.rasterType = self.addMandatoryParameter(QComboBox,
                                                     "Type of raster to reconstruct:")
        self.rasterType.addItems(['Topography', 'Bathymetry'])
        
        # Rotation Model:
        self.modelName = self.addMandatoryParameter(QComboBox,
                                                    "Name of rotation model:")
        self.modelName.addItems(self.model_list)
        self.modelName.setStyleSheet("combobox-popup: 0;")
        
        # Topography specific parameters:
        ## Input raster:
        self.inputRaster = self.addVariantParameter(QComboBox, "Topography",
                                                    "Input raster:",
                                                    mandatory=True)
        self.inputRaster.addItems(['ETOPO Ice surface elevation (60 arc seconds)',
                                   'ETOPO Ice surface elevation (30 arc seconds)',
                                   'ETOPO Bedrock elevation (60 arc seconds)',
                                   'ETOPO Bedrock elevation (30 arc seconds)'])
        self.inputRaster.setMaxVisibleItems(10)
        
        ## Reconstruction time:
        self.reconstruction_time = self.addVariantParameter(TaSpinBox, "Topography",
                                                            "Reconstruction time (in Ma):")
        self.reconstruction_time.setDataType("integer")
        
        ## Resampling:
        self.resampling = self.addVariantParameter(TaCheckBox,
                                                   "Topography",
                                                   "Do resampling:")
        self.resampling.setChecked(True)
         
        ## Resampling Resolution:
        self.resampling_resolution = self.addVariantParameter(QgsDoubleSpinBox,
                                                   "Topography",
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
        self.startTime = self.addVariantParameter(TaSpinBox, "Bathymetry",
                                                       "Start Time (in Ma)",
                                                       mandatory=True)
        self.startTime.setDataType("integer")
        
        ## End time
        self.endTime = self.addVariantParameter(TaSpinBox, "Bathymetry",
                                                     "End Time (in Ma)",
                                                     mandatory=True)
        self.endTime.setDataType("integer")
        
        ## Time Step
        self.timeStep = self.addVariantParameter(TaSpinBox, "Bathymetry",
                                                 "Time step (in Ma)",
                                                 mandatory=True)
        self.timeStep.setDataType("integer")
        
        # Spatial Resolution
        self.resolution = self.addVariantParameter(QgsDoubleSpinBox,
                                                   "Bathymetry",
                                                   "Spacial resolution (in arc degrees):",
                                                   mandatory=True)
        self.resolution.setValue(0.5)
        
        # Extent
        self.minlon = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Minimum longitude (in arc degrees):")
        self.minlon.setMinimum(-180)
        self.minlon.setMaximum(180)
        self.minlon.setValue(-180)
        
        self.maxlon = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Maximum longitude (in arc degrees):")
        self.maxlon.setMinimum(-180)
        self.maxlon.setMaximum(180)
        self.maxlon.setValue(180)
        
        self.minlat = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Minimum latitude (in arc degrees):")
        self.minlat.setMinimum(-90)
        self.minlat.setMaximum(90)
        self.minlat.setValue(-90)
        
        self.maxlat = self.addAdvancedParameter(QgsDoubleSpinBox,
                                                "Maximum latitude (in arc degrees):")
        self.maxlat.setMinimum(-90)
        self.maxlat.setMaximum(90)
        self.maxlat.setValue(90)
        
        # Threads
        self.threads = self.addAdvancedParameter(TaSpinBox,
                                                 "Number of threads to use during reconstruction:")
        self.threads.spinBox.setMinimum(1)
        
        
        # Fill the parameters' tab of the Dialog with the defined parameters
        self.fillDialog()
        self.showVariantWidgets(self.rasterType.currentText())
        self.rasterType.currentTextChanged.connect(self.showVariantWidgets)
