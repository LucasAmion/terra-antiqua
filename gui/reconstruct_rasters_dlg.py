#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from PyQt5 import QtWidgets
from .base_dialog import TaBaseDialog
from .widgets import TaSpinBox
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
        self.modelName = self.addMandatoryParameter(
            QtWidgets.QComboBox,
            "Name of rotation model:")
        self.modelName.addItems(self.model_list)
        self.rasterType = self.addMandatoryParameter(
            QtWidgets.QComboBox,
            "Type of raster to reconstruct:")
        self.rasterType.addItems(['Topography', 'Bathymetry'])
        self.years = self.addMandatoryParameter(
            TaSpinBox,
            "Years ago (Ma):")
        self.years.setDataType("integer")
        self.years.initOverrideButton("Years", "Time to go back in millions of years.")

        # Fill the parameters' tab of the Dialog with the defined parameters
        self.fillDialog()
