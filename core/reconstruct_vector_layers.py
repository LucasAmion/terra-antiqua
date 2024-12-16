#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from qgis.core import QgsVectorLayer
from .base_algorithm import TaBaseAlgorithm
from .cache_manager import cache_manager
import pygplates
import os

class TaReconstructVectorLayers(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)

    def run(self):
        # Obtaining input from dialog
        model_name = self.dlg.modelName.currentText()
        layer_type = self.dlg.layerType.currentText()
        if layer_type == "Local Layer":
            local_layer = self.dlg.localLayer.currentLayer()
            if not local_layer:
                self.feedback.error(f"No input layer selected.")
                self.kill()
        reconstruction_time = self.dlg.reconstruction_time.spinBox.value()
        output_path = self.dlg.outputPath.filePath()
        if not output_path:
            output_path = self.dlg.outputPath.lineEdit().placeholderText()
        
        # Downloading rotation model and input layer if needed
        if not self.killed:
            try:
                self.feedback.info(f"Downloading {model_name} rotation model...")
                rotation_model = cache_manager.download_model(model_name, self.feedback)
                if layer_type == "Local Layer":
                    layer = local_layer.dataProvider().dataSourceUri()
                else:
                    self.feedback.info(f"Downloading {model_name} {layer_type} input layer...")
                    layer = cache_manager.download_layer(model_name, layer_type.replace(' ', ''), self.feedback)
            except:
                self.feedback.error(f"There was an error while downloading the {model_name} model files.")
                self.kill()
        
        # Deleting old file with the same name if it exists
        if not self.killed:
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except:
                    self.feedback.error(f"Cannot save output file {output_path}. There is a file with the same name which is currently being used. Check if the layer has already been added to the project.")
                    self.kill()
        
        # Reconstructing vector layer to desired age
        if not self.killed:
            try:
                self.feedback.info("Starting reconstruction...")
                pygplates.reconstruct(layer, rotation_model, output_path, reconstruction_time)
                self.feedback.info("Reconstruction finished.")
                self.feedback.progress += 30
            except:
                self.feedback.error(f"There was an error while reconstructing layer to the desired age.")
                self.kill()
        
        # Saving the result
        vlayer = QgsVectorLayer(output_path, "Temp layer", "ogr")

        if self.killed:
            self.finished.emit(False, "")
        elif not vlayer.isValid():
            self.feedback.error("Layer failed to load!")
            self.kill()
            self.finished.emit(False, "")
        else:
            self.finished.emit(True, output_path)
            self.feedback.progress = 100
        
