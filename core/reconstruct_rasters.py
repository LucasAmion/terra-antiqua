#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
# Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py

from osgeo import gdal
from PyQt5 import QtCore, QtWidgets, QtGui

from qgis.core import QgsRasterLayer
from .base_algorithm import TaBaseAlgorithm
from .utils import clipArrayToExtent, convertAgeToDepth
from .cache_manager import cache_manager

try:
    from agegrid.run_paleo_age_grids import run_paleo_age_grids
except Exception:
    QtWidgets.QMessageBox.warning(None, "Terra Antiqua - GMT not found",
                                        "Make sure you have GMT installed in your system and add it to path, otherwise the Bathymetry/Agegrid reconstruction feature won't be available. "
                                        'You can follow the instructions on this page if you do not know how to do it: <a href="https://github.com/LucasAmion/terra-antiqua?tab=readme-ov-file#windows">https://github.com/LucasAmion/terra-antiqua?tab=readme-ov-file#windows</a>')

import gplately
import os
import shutil

class TaReconstructRasters(TaBaseAlgorithm):

    def __init__(self, dlg):
        super().__init__(dlg)

    def run(self):
        # Obtaining input from dialog
        model_name = self.dlg.modelName.currentData(QtCore.Qt.UserRole)
        raster_type = self.dlg.rasterType.currentText()
        if raster_type == "Topography":
            save_multiple_rasters = self.dlg.createSequence.isChecked()
            if save_multiple_rasters:
                start_time = self.dlg.topoStartTime.spinBox.value()
                end_time = self.dlg.reconstruction_time.spinBox.value()
                time_step = self.dlg.topoTimeStep.spinBox.value()
            reconstruction_time = self.dlg.reconstruction_time.spinBox.value()
            raster = self.dlg.inputRaster.currentData(QtCore.Qt.UserRole)
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
            save_multiple_rasters = self.dlg.saveAll.isChecked()
            
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
                        self.feedback.info(f"Downloading {model_name} model if needed...")
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
                    self.feedback.info("Reading input raster...")
                    data = gdal.Open(local_layer.dataProvider().dataSourceUri())
                    data = data.GetRasterBand(1).ReadAsArray()
                    input_extent = local_layer.extent()
                    input_extent = (input_extent.xMinimum(), input_extent.xMaximum(), input_extent.yMaximum(), input_extent.yMinimum())
                    topo_raster = gplately.Raster(data=data, extent=input_extent)
                    self.feedback.progress += 10
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
                    self.feedback.progress += 10
                except Exception:
                    self.feedback.error("There was an error while resampling the input raster.")
                    self.kill()
            
            # Reconstructing raster to desired age
            if not self.killed:
                try:
                    if save_multiple_rasters:
                        rasters = []
                        for t in range(start_time, end_time + time_step, time_step):
                            self.feedback.info(f"Reconstructing raster to {t} Ma...")
                            topo_raster.plate_reconstruction = model
                            partitioning_features = cobs if cobs else static_polygons
                            reconstructed_raster = topo_raster.reconstruct(t, threads=n_threads,
                                                    partitioning_features=partitioning_features)
                            rasters.append(reconstructed_raster)
                    else:
                        if reconstruction_time > 0:
                            topo_raster.plate_reconstruction = model
                            partitioning_features = cobs if cobs else static_polygons
                            self.feedback.info("Starting reconstruction...")
                            topo_raster.reconstruct(reconstruction_time, threads=n_threads, inplace=True,
                                                partitioning_features=partitioning_features)
                            rasters = [topo_raster]
                            self.feedback.info("Reconstruction finished.")
                        self.feedback.progress += 20
                except Exception:
                    self.feedback.error("There was an error while reconstructing raster to the desired age.")
                    self.kill()
            
            # Clip the raster according to the defined extent
            if not self.killed:
                try:
                    extent = (minlon, maxlon, minlat, maxlat)
                    if extent != (-180, 180, -90, 90):
                        for raster in rasters:
                            clipArrayToExtent(raster, extent)
                        self.feedback.info("Raster clipped to the specified bounds.")
                    self.feedback.progress += 10
                except Exception:
                    self.feedback.error("There was an error while clipping the raster.")
                    self.kill()
                    
            # Exporting result as NetCDF file
            if not self.killed:
                try:
                    if save_multiple_rasters:
                        if not os.path.exists(output_path):
                            os.makedirs(output_path)
                        for raster in rasters:
                            filename = f"Topography_{model_name}_{raster.time}.0Ma.nc"
                            file_path = os.path.join(output_path, filename)
                            if os.path.exists(file_path):
                                try:
                                    os.unlink(file_path)
                                except Exception:
                                    self.feedback.error(f"Cannot save output file {file_path}. There is a file with the same name which is currently being used.")
                                    self.kill()
                            raster.save_to_netcdf4(os.path.join(output_path, filename))
                        self.feedback.info(f"All topography files saved to the output folder {output_path}.")
                    else:
                        if os.path.exists(output_path):
                            try:
                                os.unlink(output_path)
                            except Exception:
                                self.feedback.error(f"Cannot save output file {output_path}. There is a file with the same name which is currently being used.")
                                self.kill()
                        rasters[0].save_to_netcdf4(output_path)
                except Exception:
                    self.feedback.error("There was an error while exporting the result to NetCDF.")
                    self.kill()
                    
        elif raster_type == 'Agegrid':
            # Downloading rotation model files
            if not self.killed:
                try:
                    self.feedback.info(f"Downloading {model_name} model if needed...")
                    cache_manager.download_model(model_name, self.feedback)
                except Exception:
                    self.feedback.error(f"There was an error while downloading the {model_name} model files.")
                    self.kill()
                    
            # Downloading the model's vector layers
            if not self.killed:
                try:
                    self.feedback.info(f"Downloading {model_name} associated vector layers if needed...")
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
                    shutil.rmtree(os.path.join(self.temp_dir, "grid_files"), ignore_errors=True)
                    model_dir = cache_manager.get_model(model_name).get_model_dir()
                    run_paleo_age_grids(model_name, model_dir, self.temp_dir, self.feedback,
                                        start_time, end_time, time_step, resolution, minlon, maxlon,
                                        minlat, maxlat, n_threads, spreading_rate)
                    self.feedback.info("Reconstruction finished.")
                except Exception:
                    self.feedback.error("There was an error while performing the reconstuction.")
                    self.kill()
            
            # Reading the resulting raster or rasters
            if not self.killed:
                rasters = []
                if save_multiple_rasters:
                    path = os.path.join(self.temp_dir, "grid_files", "masked")
                    for filename in os.listdir(path):
                        file_path = os.path.join(path, filename)
                        if os.path.isfile(file_path):
                            rasters.append(gplately.Raster(data=file_path))
                else:
                    path = os.path.join(self.temp_dir, "grid_files", "masked", f"{model_name}_seafloor_age_mask_{end_time}.0Ma.nc")
                    rasters.append(gplately.Raster(data=path))
            
            # Converting ocean age to bathymetry
            if convert:
                if not self.killed:
                    try:
                        self.feedback.info("Converting ocean age to bathymetry...")
                        for raster in rasters:
                            raster._data = convertAgeToDepth(raster._data, 0, 0)
                            self.feedback.progress += 5
                    except Exception:
                        self.feedback.error("There was an error while converting age raster to bathymetry.")
                        self.kill()
            
            # Exporting result as NetCDF file
            if not self.killed:
                try:
                    if save_multiple_rasters:
                        if not os.path.exists(output_path):
                            os.makedirs(output_path)
                        for raster in rasters:
                            if convert:
                                filename = f"Bathymetry_{model_name}_{raster.filename.rsplit('_', 1)[-1]}"
                            else:
                                filename = f"Agegrid_{model_name}_{raster.filename.rsplit('_', 1)[-1]}"
                            file_path = os.path.join(output_path, filename)
                            if os.path.exists(file_path):
                                try:
                                    os.unlink(file_path)
                                except Exception:
                                    self.feedback.error(f"Cannot save output file {file_path}. There is a file with the same name which is currently being used.")
                                    self.kill()
                            raster.save_to_netcdf4(file_path)
                        self.feedback.info(f"All agegrid files saved to the output folder {output_path}.")
                    else:
                        if os.path.exists(output_path):
                            try:
                                os.unlink(output_path)
                            except Exception:
                                self.feedback.error(f"Cannot save output file {output_path}. There is a file with the same name which is currently being used.")
                                self.kill()
                        rasters[0].save_to_netcdf4(output_path)
                except Exception:
                    self.feedback.error("There was an error while exporting the result to NetCDF.")
                    self.kill()
        
        # Saving the result
        if self.killed:
            self.finished.emit(False, "")
        else:
            if save_multiple_rasters:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(output_path))
                self.feedback.progress = 100
                self.finished.emit(True, None)
            else:
                rlayer = QgsRasterLayer(output_path, "Temp layer", "gdal")
                if not rlayer.isValid():
                    self.feedback.error("Layer failed to load!")
                    self.kill()
                    self.finished.emit(False, "")
                else:
                    self.finished.emit(True, output_path)
                    self.feedback.progress = 100
