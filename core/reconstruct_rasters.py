#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from osgeo import gdal
from PyQt5 import QtCore
from qgis.core import QgsRasterLayer
from .base_algorithm import TaBaseAlgorithm
from .utils import clipArrayToExtent, convertAgeToDepth
from .cache_manager import cache_manager

from agegrid.run_paleo_age_grids import run_paleo_age_grids

import gplately
import os

class TaReconstructRasters(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)

    def run(self):
        # Obtaining input from dialog
        model_name = self.dlg.modelName.currentData(QtCore.Qt.UserRole)
        raster_type = self.dlg.rasterType.currentText()
        if raster_type == "Topography":
            reconstruction_time = self.dlg.reconstruction_time.spinBox.value()
            raster = self.dlg.inputRaster.currentText()
            local = raster == 'Local'
            if local:
                local_layer = self.dlg.localLayer.currentLayer()
                if not local_layer:
                    self.feedback.error("No input layer selected.")
                    self.kill()
            resampling = self.dlg.resampling.isChecked()
            resampling_resolution = self.dlg.resampling_resolution.value()
            interpolationMethod = self.dlg.interpolationMethod.currentIndex()
        if raster_type == "Agegrid":
            start_time = self.dlg.startTime.spinBox.value()
            end_time = self.dlg.endTime.spinBox.value()
            time_step = self.dlg.timeStep.spinBox.value()
            resolution = self.dlg.resolution.value()
            convert = self.dlg.convertToBathymetry.isChecked()
            spreading_rate = self.dlg.spreading_rate.value()
            
        minlon = self.dlg.minlon.value()
        maxlon = self.dlg.maxlon.value()
        minlat = self.dlg.minlat.value()
        maxlat = self.dlg.maxlat.value()
        
        n_threads = self.dlg.threads.spinBox.value()
        output_path = self.dlg.outputPath.filePath()
        if not output_path:
            output_path = self.dlg.outputPath.lineEdit().placeholderText()
        
        if raster_type == 'Topography':
            # Downloading rotation model files
            if not self.killed:
                try:
                    if reconstruction_time > 0:
                        self.feedback.info(f"Downloading {model_name} model...")
                        rotation_model = cache_manager.download_model(model_name, self.feedback)
                        cache_manager.download_all_layers(model_name, self.feedback)
                        topology_features = cache_manager.get_layer(model_name, "Topologies", self.feedback)
                        static_polygons = cache_manager.get_layer(model_name, "StaticPolygons", self.feedback)
                        cobs = cache_manager.get_layer(model_name, "COBs", self.feedback)
                        if cobs is None:
                            self.feedback.info("Using static polygons instead.")
                        model = gplately.PlateReconstruction(rotation_model, topology_features, static_polygons)
                    else:
                        model = None
                except Exception:
                    self.feedback.error(f"There was an error while downloading the {model_name} model files.")
                    self.kill()
            
            # Obtaning input layer
            if not self.killed:
                if not local:
                    try:
                        self.feedback.info("Downloading present day topography raster...")
                        data = cache_manager.download_raster(raster, self.feedback)
                        with gdal.config_option('GDAL_PAM_ENABLED', 'NO'):
                            local_layer = QgsRasterLayer(data, data, 'gdal')
                    except Exception:
                        self.feedback.error("There was an error while downloading the input raster.")
                        self.kill()
                try:
                    data = gdal.Open(local_layer.dataProvider().dataSourceUri())
                    data = data.GetRasterBand(1).ReadAsArray()
                    input_extent = local_layer.extent()
                    input_extent = (input_extent.xMinimum(), input_extent.xMaximum(), input_extent.yMaximum(), input_extent.yMinimum())
                    topo_raster = gplately.Raster(data=data, extent=input_extent)
                except Exception:
                    self.feedback.error("There was an error while reading the input raster.")
                    self.kill()
                    
                    
            # Resampling to desired resolution
            if not self.killed:
                try:
                    topo_raster._data = topo_raster._data.astype(float)
                    if resampling:
                        self.feedback.info("Resampling...")
                        topo_raster.resample(resampling_resolution, resampling_resolution, method=interpolationMethod, inplace=True)
                    self.feedback.progress += 20
                except Exception:
                    self.feedback.error("There was an error while resampling the input raster.")
                    self.kill()
            
            # Reconstructing raster to desired age
            if not self.killed:
                try:
                    if reconstruction_time > 0:
                        topo_raster.plate_reconstruction = model
                        partitioning_features = cobs if cobs else static_polygons
                        self.feedback.info("Starting reconstruction...")
                        topo_raster.reconstruct(reconstruction_time, threads=n_threads, inplace=True,
                                            partitioning_features=partitioning_features)
                        self.feedback.info("Reconstruction finished.")
                    self.feedback.progress += 30
                except Exception:
                    self.feedback.error("There was an error while reconstructing raster to the desired age.")
                    self.kill()
            
            # Clip the raster according to the defined extent
            if not self.killed:
                try:
                    extent = (minlon, maxlon, minlat, maxlat)
                    if extent != (-180, 180, -90, 90):
                        clipArrayToExtent(topo_raster, extent)
                        self.feedback.info("Raster clipped to the specified bounds.")
                    self.feedback.progress += 10
                except Exception:
                    self.feedback.error("There was an error while clipping the raster.")
                    self.kill()
            
            # Exporting result as NetCDF file
            if not self.killed:
                if os.path.exists(output_path):
                    try:
                        os.unlink(output_path)
                    except Exception:
                        self.feedback.error(f"Cannot save output file {output_path}. There is a file with the same name which is currently being used. Check if the layer has already been added to the project.")
                        self.kill()
            if not self.killed:
                try:
                    topo_raster.save_to_netcdf4(output_path)
                except Exception:
                    self.feedback.error("There was an error while exporting the result to NetCDF.")
                    self.kill()
                        
                    
        elif raster_type == 'Agegrid':
            # Downloading rotation model files
            if not self.killed:
                try:
                    self.feedback.info(f"Downloading {model_name} model...")
                    cache_manager.download_model(model_name, self.feedback)
                except Exception:
                    self.feedback.error(f"There was an error while downloading the {model_name} model files.")
                    self.kill()
                    
            # Downloading the model's vector layers
            if not self.killed:
                try:
                    self.feedback.info(f"Downloading {model_name} associated vector layers...")
                    cache_manager.download_all_layers(model_name, self.feedback)
                    cache_manager.get_layer(model_name, "Topologies", self.feedback)
                    cache_manager.get_layer(model_name, "COBs", self.feedback)
                except Exception:
                    self.feedback.error(f"There was an error while downloading the {model_name} vector layer files.")
                    self.kill()
            
            # Running reconstruction algorithm
            if not self.killed:
                try:
                    self.feedback.info("Starting reconstruction...")
                    run_paleo_age_grids(model_name, cache_manager.model_data_dir, self.temp_dir, self.feedback,
                                        start_time, end_time, time_step, resolution, minlon, maxlon,
                                        minlat, maxlat, n_threads, spreading_rate)
                    path = os.path.join(self.temp_dir, "grid_files", "masked", f"{model_name}_seafloor_age_mask_{end_time}.0Ma.nc")
                    agegrid = gplately.Raster(data=path)
                    self.feedback.info("Reconstruction finished.")
                except Exception:
                    self.feedback.error("There was an error while performing the reconstuction.")
                    self.kill()
            
            # Converting ocean age to bathymetry
            if convert:
                if not self.killed:
                    try:
                        self.feedback.info("Converting ocean age to bathymetry...")
                        agegrid._data = convertAgeToDepth(agegrid._data, 0, 0)
                        self.feedback.progress += 5
                    except Exception:
                        self.feedback.error("There was an error while converting age raster to bathymetry.")
                        self.kill()
                
            # Exporting result as NetCDF file
            if not self.killed:
                if os.path.exists(output_path):
                    try:
                        os.unlink(output_path)
                    except Exception:
                        self.feedback.error(f"Cannot save output file {output_path}. There is a file with the same name which is currently being used. Check if the layer has already been added to the project.")
                        self.kill()
                if not self.killed:
                    try:
                        agegrid.save_to_netcdf4(output_path)
                    except Exception:
                        self.feedback.error("There was an error while exporting the result to NetCDF.")
                        self.kill()
        
        # Saving the result
        rlayer = QgsRasterLayer(output_path, "Temp layer", "gdal")
        
        if self.killed:
            self.finished.emit(False, "")
        elif not rlayer.isValid():
            self.feedback.error("Layer failed to load!")
            self.kill()
            self.finished.emit(False, "")
        else:
            self.finished.emit(True, output_path)
            self.feedback.progress = 100
