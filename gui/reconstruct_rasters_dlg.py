#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from PyQt5.QtWidgets import QComboBox
from .base_dialog import TaBaseDialog
from qgis.gui import QgsDoubleSpinBox
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
        
        # Years ago:
        self.years = self.addMandatoryParameter(TaSpinBox, "Years ago (Ma):")
        self.years.setDataType("integer")
        self.years.initOverrideButton("Years", "Time to go back in millions of years.")
        
        # Topography specific parameters:
        ## Starting raster:
        self.startingRaster = self.addVariantParameter(QComboBox,
                                                  "Topography",
                                                  "Starting raster:")
        self.startingRaster.setMaxVisibleItems(10)
        self.startingRaster.addItems(['ETOPO Ice surface elevation (60 arc seconds)',
                                      'ETOPO Ice surface elevation (30 arc seconds)',
                                      'ETOPO Bedrock elevation (60 arc seconds)',
                                      'ETOPO Bedrock elevation (30 arc seconds)'])
        
        ## Resampling:
        self.resampling = self.addVariantParameter(TaCheckBox,
                                                   "Topography",
                                                   "Do resampling:")
        self.resampling.setChecked(True)
         
        ## Resampling Resolution:
        self.resolution = self.addVariantParameter(QgsDoubleSpinBox,
                                                   "Topography",
                                                   "Resampling resolution (in arc degrees):")
        self.resolution.setValue(0.5)
                
        ## Interpolation method:
        self.interpolationMethod = self.addAdvancedParameter(QComboBox, 
                                                             variant_index="Topography",
                                                             label="Interpolation method:")
        self.interpolationMethod.addItems(['linear',
                                           'square',
                                           'cubic',
                                           '4th degree',
                                           '5th degree'])
        self.resampling.registerEnabledWidgets([self.resolution, self.interpolationMethod])
        
        # Fill the parameters' tab of the Dialog with the defined parameters
        self.fillDialog()
        self.showVariantWidgets(self.rasterType.currentText())
        self.rasterType.currentTextChanged.connect(self.showVariantWidgets)
