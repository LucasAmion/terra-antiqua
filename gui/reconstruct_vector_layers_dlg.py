#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from PyQt5.QtWidgets import QComboBox
from .base_dialog import TaBaseDialog
from .widgets import TaSpinBox
from ..core.cache_manager import cache_manager
import tempfile
import os

class TaReconstructVectorLayersDlg(TaBaseDialog):
    
    def __init__(self, parent = None):
        """Constructor."""
        super(TaReconstructVectorLayersDlg, self).__init__(parent)
        self.defineParameters()

    def defineParameters(self):
        """ Adds parameters to a list object that is used by the TaBaseDialog
        class to create widgets and place them parameters tab.
        """
        # Layer Type:
        self.layerType = self.addMandatoryParameter(QComboBox,
                                                    "Layer to reconstruct:")
        self.layerType.addItems(['Static Polygons', 'Continental Polygons',
                                 'Coastlines', 'COBs', 'Cratons', 'Terranes'])
        
        # Rotation Model:
        self.modelName = self.addMandatoryParameter(QComboBox,
                                                    "Name of rotation model:")
        self.modelName.setStyleSheet("combobox-popup: 0;")
        def set_available_models():
            layer_type = self.layerType.currentText().replace(' ', '')
            self.modelName.clear()
            self.modelName.addItems(cache_manager.get_available_models(required_layers=[layer_type]))
        self.layerType.currentTextChanged.connect(set_available_models)
        set_available_models()
        
        # Reconstruction time:
        self.reconstruction_time = self.addMandatoryParameter(TaSpinBox, "Reconstruction time (in Ma):")
        self.reconstruction_time.setDataType("integer")
        def set_maximum_reconstruction_time():
            model_bigtime = cache_manager.get_model_bigtime(self.modelName.currentText())
            self.reconstruction_time.spinBox.setMaximum(model_bigtime)
        set_maximum_reconstruction_time()
        self.modelName.currentIndexChanged.connect(set_maximum_reconstruction_time)
        
        # Fill the parameters' tab of the Dialog with the defined parameters
        self.fillDialog()
        
        # Update output path when parameters change
        def update_output_path(_):
            layer_type = self.layerType.currentText().replace(' ', '')
            reconstruction_time = self.reconstruction_time.spinBox.value()
            model_name = self.modelName.currentText()
            
            path = os.path.join(tempfile.gettempdir(),
                                f"{layer_type}_{reconstruction_time}.0_{model_name}.shp")
            self.outputPath.lineEdit().setPlaceholderText(path)
        
        self.layerType.currentTextChanged.connect(update_output_path)
        self.modelName.currentTextChanged.connect(update_output_path)
        self.reconstruction_time.spinBox.valueChanged.connect(update_output_path)
        self.setDefaultOutFilePath = update_output_path
