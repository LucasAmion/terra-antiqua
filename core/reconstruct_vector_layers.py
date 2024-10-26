#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from qgis.core import QgsVectorLayer
from .base_algorithm import TaBaseAlgorithm
from .cache_manager import cache_manager
import pygplates
import os
import glob

class TaReconstructVectorLayers(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)

    def run(self):
        # Obtaining input from dialog
        model_name = self.dlg.modelName.currentText()
        layer_type = self.dlg.layerType.currentText().replace(' ', '')
        reconstruction_time = self.dlg.reconstruction_time.spinBox.value()
        output_path = self.dlg.outputPath.filePath()
        if not output_path:
            output_path = self.dlg.outputPath.lineEdit().placeholderText()
        
        self.feedback.info(f"Downloading {model_name} model...")
        rotation_model = cache_manager.download_model(model_name, self.feedback)
        layer = cache_manager.download_layer(model_name, layer_type, self.feedback)
        
        # Deleting old files with the same name
        files = glob.glob(os.path.splitext(output_path)[0] + '*')
        for file in files:
            try:
                os.unlink(file)
            except:
                self.feedback.error(f'Cannot save output file {output_path}. There is a file with the same name which is currently being used. Check if the layer has already been added to the project.')
                self.kill()
                break
        
        if not self.killed:
            # Reconstructing raster to desired age
            self.feedback.info("Starting reconstruction...")
            pygplates.reconstruct(layer, rotation_model, output_path, reconstruction_time)
            self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
                
            vlayer = QgsVectorLayer(output_path, "Temp layer", "ogr")

            if not vlayer.isValid():
                self.feedback.error("Layer failed to load!")
                self.kill()
                self.finished.emit(False, "")
            else:
                self.finished.emit(True, output_path)
                self.feedback.progress = 100
        else:
            self.finished.emit(False, "")
