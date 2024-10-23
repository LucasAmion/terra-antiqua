#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from qgis.core import (
    QgsRasterLayer,
)
from .base_algorithm import TaBaseAlgorithm
from .utils import exportArrayToGeoTIFF
from .cache_manager import cache_manager

from agegrid.run_paleo_age_grids import run_paleo_age_grids

import numpy as np
import gplately
import os

class TaReconstructRasters(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)

    def run(self):
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
        n_threads = self.dlg.threads.spinBox.value()

        self.feedback.info(f"Downloading {model_name} model...")
        rotation_model, topology_features, \
            static_polygons, cobs = cache_manager.download_model(model_name, self.feedback)
        model = gplately.PlateReconstruction(rotation_model, topology_features, static_polygons)
        
        if raster_type == 'Topography':
            self.feedback.info("Downloading present day topography raster...")
            data = cache_manager.download_raster(rasterIdx, self.feedback)
            topo_raster = gplately.Raster(data=data, plate_reconstruction=model)
            self.feedback.progress += 10

            # Resampling to desired resolution
            topo_raster._data = topo_raster._data.astype(float)
            if resampling == True:
                self.feedback.info("Resampling...")
                topo_raster.resample(resampling_resolution, resampling_resolution, method=interpolationMethod, inplace=True)
            self.feedback.progress += 20
            
            # Reconstructing raster to desired age
            if reconstruction_time > 0:
                topo_raster.plate_reconstruction = model
                partitioning_features = cobs if cobs else static_polygons
                self.feedback.info("Starting reconstruction...")
                topo_raster.reconstruct(reconstruction_time, threads=n_threads, inplace=True,
                                     partitioning_features=partitioning_features)
                self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
            
            # Clip the raster according to the defined extent
            lon_indices = np.where((topo_raster.lons >= minlon) & (topo_raster.lons <= maxlon))[0]
            lat_indices = np.where((topo_raster.lats >= minlat) & (topo_raster.lats <= maxlat))[0]
            topo_raster._data = topo_raster._data[np.min(lat_indices):np.max(lat_indices)+1,
                                            np.min(lon_indices):np.max(lon_indices)+1]
            topo_raster.lons = topo_raster.lons[np.min(lon_indices):np.max(lon_indices)+1]
            topo_raster.lats = topo_raster.lats[np.min(lat_indices):np.max(lat_indices)+1]
            self.feedback.info("Raster clipped to the specified bounds.")
            self.feedback.progress += 10
            
            # Exporting result as GeoTIFF
            path = os.path.join(self.temp_dir, f"Topography_{reconstruction_time}_{model_name}.0Ma.tif")
            exportArrayToGeoTIFF(path, topo_raster._data, topo_raster._lons, topo_raster._lats, self.crs)
            
        elif raster_type == 'Bathymetry':
            self.feedback.info("Starting reconstruction...")
            run_paleo_age_grids(model_name, cache_manager.model_data_dir, self.temp_dir, self.feedback,
                                start_time, end_time, time_step, resolution, minlon, maxlon,
                                minlat, maxlat, n_threads)
            self.feedback.info("Reconstruction finished.")
            self.feedback.progress += 30
            
            # Exporting result as GeoTIFF
            path = os.path.join(self.temp_dir, "grid_files", "masked", f"{model_name}_seafloor_age_mask_{end_time}.0Ma.nc")
            agegrid = gplately.Raster(data=path, plate_reconstruction=model)
            path = os.path.join(self.temp_dir, f"Agegrid_{end_time}.0Ma_{model_name}.tif")
            exportArrayToGeoTIFF(path, agegrid._data, agegrid._lons, agegrid._lats, self.crs)
            
        rlayer = QgsRasterLayer(path, "Temp layer", "gdal")

        if not rlayer.isValid():
            self.feedback.error("Layer failed to load!")
            self.kill()
            self.finished.emit(False)
        else:
            self.finished.emit(True, path)
            self.feedback.progress = 100
