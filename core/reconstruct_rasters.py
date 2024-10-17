#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from qgis.core import (
    QgsRasterLayer,
)
from .base_algorithm import TaBaseAlgorithm
from .utils import exportArrayToGeoTIFF

from agegrid.run_paleo_age_grids import run_paleo_age_grids

from appdirs import user_data_dir
from plate_model_manager import PlateModelManager, PresentDayRasterManager
import numpy as np
import gplately
import logging
import os

class TaReconstructRasters(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)
        self.remove_overlap = None
        self.available_rasters = {
            0: "etopo_ice_60",
            1: "etopo_ice_30",
            2: "etopo_bed_60",
            3: "etopo_bed_30"
        } 

    def run(self):
        data_dir = user_data_dir("QGIS3", "QGIS")
        model_data_dir = os.path.join(data_dir, "plugins", "terra_antiqua", "models")
        raster_data_dir = os.path.join(data_dir, "plugins", "terra_antiqua", "rasters")
        pm_manager = PlateModelManager()
        raster_manager = PresentDayRasterManager(os.path.join(os.path.dirname(__file__), "../resources/present_day_rasters.json"))
        raster_manager.set_data_dir(raster_data_dir)
        
        # Obtaining input from dialog
        model_name = self.dlg.modelName.currentText()
        raster_type = self.dlg.rasterType.currentText()
        if raster_type == "Topography":
            reconstruction_time = self.dlg.reconstruction_time.spinBox.value()
            rasterIdx = self.dlg.inputRaster.currentIndex()
            resampling = self.dlg.resampling.isChecked()
            resampling_resolution = self.dlg.resampling_resolution.value()
            interpolationMethod = self.dlg.interpolationMethod.currentIndex()
        if raster_type == "Bathymetry":
            start_time = self.dlg.startTime.spinBox.value()
            end_time = self.dlg.endTime.spinBox.value()
            time_step = self.dlg.timeStep.spinBox.value()
            resolution = self.dlg.resolution.value()
        minlon = self.dlg.minlon.value()
        maxlon = self.dlg.maxlon.value()
        minlat = self.dlg.minlat.value()
        maxlat = self.dlg.maxlat.value()
        threads = self.dlg.threads.spinBox.value()
        
        # Forwarding logs from pmm
        pmm_logger = logging.getLogger('pmm')
        pmm_logger.setLevel(logging.DEBUG)
        pmm_logger.addHandler(self.feedback.log_handler)

        self.feedback.info(f"Downloading {model_name} model...")
        model = pm_manager.get_model(model_name)
        model.set_data_dir(model_data_dir)

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
            data = raster_manager.get_raster(self.available_rasters[rasterIdx])
            etopo_nc = gplately.Raster(data=data, plate_reconstruction=model)
            self.feedback.progress += 10
            
            # Remove pmm logs
            pmm_logger.removeHandler(self.feedback.log_handler)

            # Resampling to desired resolution
            etopo_nc._data = etopo_nc._data.astype(float)
            if resampling == True:
                self.feedback.info("Resampling...")
                etopo_nc.resample(resampling_resolution, resampling_resolution, method=interpolationMethod, inplace=True)
            self.feedback.progress += 20
            
            # Reconstructing raster to desired age
            if reconstruction_time > 0:
                self.feedback.info("Starting reconstruction...")
                etopo_nc.plate_reconstruction = model
                etopo_nc.reconstruct(reconstruction_time, threads=4, inplace=True)
                self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
            
            # Clip the raster according to the defined extent
            lon_indices = np.where((etopo_nc.lons >= minlon) & (etopo_nc.lons <= maxlon))[0]
            lat_indices = np.where((etopo_nc.lats >= minlat) & (etopo_nc.lats <= maxlat))[0]
            etopo_nc._data = etopo_nc._data[np.min(lat_indices):np.max(lat_indices)+1,
                                            np.min(lon_indices):np.max(lon_indices)+1]
            etopo_nc.lons = etopo_nc.lons[np.min(lon_indices):np.max(lon_indices)+1]
            etopo_nc.lats = etopo_nc.lats[np.min(lat_indices):np.max(lat_indices)+1]
            self.feedback.info("Raster clipped to the specified bounds.")
            self.feedback.progress += 10
            
            # Exporting result as GeoTIFF
            path = os.path.join(self.temp_dir, f"ETOPO_{model_name}_{reconstruction_time}.0Ma.tif")
            exportArrayToGeoTIFF(path, etopo_nc._data, etopo_nc._lons, etopo_nc._lats, self.crs)
            
        elif raster_type == 'Bathymetry':
            self.feedback.info("Starting reconstruction...")
            run_paleo_age_grids(model_name, model_data_dir, self.temp_dir, self.feedback, start_time,
                                end_time, time_step, resolution, minlon, maxlon, minlat, maxlat, threads)
            self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
            
            # Exporting result as GeoTIFF
            path = os.path.join(self.temp_dir, "grid_files", "masked", f"{model_name}_seafloor_age_mask_{end_time}.0Ma.nc")
            agegrid = gplately.Raster(data=path, plate_reconstruction=model)
            path = os.path.join(self.temp_dir, f"{model_name}_seafloor_age_mask_{end_time}.0Ma.tif")
            exportArrayToGeoTIFF(path, agegrid._data, agegrid._lons, agegrid._lats, self.crs)
            
        rlayer = QgsRasterLayer(path, "Temp layer", "gdal")

        if not rlayer.isValid():
            self.feedback.error("Layer failed to load!")
            self.kill()
            self.finished.emit(False)
        else:
            self.finished.emit(True, path)
            self.feedback.progress = 100
