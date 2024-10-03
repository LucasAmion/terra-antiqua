#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from qgis.core import (
    QgsRasterLayer,
    QgsProject
)
from .base_algorithm import TaBaseAlgorithm

from agegrid.run_paleo_age_grids import run_paleo_age_grids

from plate_model_manager import PlateModelManager, PresentDayRasterManager
import gplately
import logging
import os

class TaReconstructRasters(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)
        self.remove_overlap = None

    def run(self):
        pm_manager = PlateModelManager()
        raster_manager = PresentDayRasterManager()
        project_path = QgsProject.instance().readPath("./")
        raster_manager.set_data_dir(os.path.join(project_path, "data"))
        
        # Obtaining input from dialog
        model_name = self.dlg.modelName.currentText()
        raster_type = self.dlg.rasterType.currentText()
        years = self.dlg.years.spinBox.value()
        
        # Forwarding logs from pmm
        pmm_logger = logging.getLogger('pmm')
        pmm_logger.setLevel(logging.DEBUG)
        pmm_logger.addHandler(self.feedback.log_handler)

        self.feedback.info(f"Downloading {model_name} model...")
        model = pm_manager.get_model(model_name)
        model.set_data_dir(os.path.join(project_path, "data"))

        rotation_model = model.get_rotation_model()
        self.feedback.progress += 10
        topology_features = model.get_topologies()
        self.feedback.progress += 10
        static_polygons = model.get_static_polygons()
        self.feedback.progress += 10
        if raster_type == 'Bathymetry':
            static_polygons = model.get_COBs()
            self.feedback.progress += 10
        
        model = gplately.PlateReconstruction(rotation_model, topology_features, static_polygons)
        
        if raster_type == 'Topography':
            self.feedback.info("Downloading present day topography raster...")
            data = raster_manager.get_raster("topography")
            etopo_nc = gplately.Raster(data=data, plate_reconstruction=model)
            self.feedback.progress += 10
            
            # Remove pmm logs
            pmm_logger.removeHandler(self.feedback.log_handler)

            # Resampling to a more manageable size
            self.feedback.info("Resampling...")
            etopo_nc._data = etopo_nc._data.astype(float)
            etopo_nc.resample(0.5, 0.5, inplace=True)
            self.feedback.progress += 20

            # Reconstructing raster to desired age
            self.feedback.info("Starting reconstruction...")
            etopo_nc.plate_reconstruction = model
            reconstructed = etopo_nc.reconstruct(years, threads=4)
            self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
            
            # Saving result
            path = os.path.join(self.temp_dir, f"ETOPO_{model_name}_{years}Ma.nc")
            reconstructed.save_to_netcdf4(path)
            
        elif raster_type == 'Bathymetry':
            path = os.path.join(project_path, "data", "grid_files", "masked", f"{model_name}_seafloor_age_mask_{years}.0Ma.nc")
            self.feedback.info("Starting reconstruction...")
            run_paleo_age_grids(model_name, years, project_path)
            self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
            
        rlayer = QgsRasterLayer(path, "Temp layer", "gdal")

        if not rlayer.isValid():
            self.feedback.error("Layer failed to load!")
            self.kill()
            self.finished.emit(False)
        else:
            self.finished.emit(True, path)
            self.feedback.progress = 100
