from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from appdirs import user_data_dir
from plate_model_manager import PlateModelManager, PresentDayRasterManager, PlateModel
from plate_model_manager.exceptions import ServerUnavailable
from plate_model_manager.utils.download import FileDownloader
import logging
import os
import shutil
import fnmatch
import glob
import threading

class _CacheSignals(QObject):
    """Qt signals for TaCacheManager (must live on a QObject)."""
    initialized = pyqtSignal()
    server_unavailable = pyqtSignal()


class _CacheInitThread(QThread):
    """Background thread that runs the slow cache-manager initialization."""

    def __init__(self, cache_mgr, parent=None):
        super().__init__(parent)
        self._cache_mgr = cache_mgr

    def run(self):
        self._cache_mgr._do_initialize()


class TaCacheManager:
    """Cache manager for Terra Antiqua plugin, handling plate models and present-day rasters."""
    
    rotations_allowed_extensions = ["*.rot", "*.grot"]
    
    layers_allowed_extensions = ["*.gpml", "*.gpmlz", "*.gpml.gz", "*.dat", "*.pla", "*.shp", "*.geojson", "*.json", "*.gpkg", "*.gmt", "*.vgp"]
    
    possible_layers = ["Topologies", "Coastlines", "COBs", "Static Polygons", "Continental Polygons"]
    
    available_rasters = {
        "ETOPO 2022 Bedrock (60 arc seconds)": "etopo_bed_60",
        "ETOPO 2022 Ice Surface (60 arc seconds)": "etopo_ice_60",
        "ETOPO 2022 Bedrock (30 arc seconds)": "etopo_bed_30",
        "ETOPO 2022 Ice Surface (30 arc seconds)": "etopo_ice_30"
    }

    def __init__(self):
        data_dir = user_data_dir("QGIS3", "QGIS")
        self.model_data_dir = os.path.join(data_dir, "plugins", "terra_antiqua", "models")
        self.raster_data_dir = os.path.join(data_dir, "plugins", "terra_antiqua", "rasters")
        
        # Create directories if they don't exist
        os.makedirs(self.model_data_dir, exist_ok=True)
        os.makedirs(self.raster_data_dir, exist_ok=True)
        
        self.pmm_logger = logging.getLogger('pmm')
        self.pmm_logger.setLevel(logging.DEBUG)
        
        # Async-init bookkeeping
        self._initialized = False
        self._init_event = threading.Event()
        self._init_thread = None
        self.signals = _CacheSignals()
        self._server_unavailable = False
        
        # Defaults for attributes set during _do_initialize()
        self.pm_manager = None
        self.raster_manager = None
        self.model_list = []
        self.display_model_list = []
        
        # Caches to avoid repeated filesystem scans and network I/O
        self._local_model_names_cache = None
        self._raster_available_cache = {}
        self._icon_tooltip_cache = {}
    
    @property
    def is_initialized(self):
        """Return True if the background initialization has completed."""
        return self._initialized
    
    def start_background_init(self):
        """Start the slow initialization in a background QThread."""
        if self._initialized or self._init_thread is not None:
            return
        self._init_thread = _CacheInitThread(self)
        self._init_thread.finished.connect(self._on_init_finished)
        self._init_thread.start()
    
    def _on_init_finished(self):
        """Slot called on the main thread when the background init completes."""
        if self._server_unavailable:
            QtWidgets.QMessageBox.information(None, "Terra Antiqua - Server Unavailable",
                                              "The Plate Model Manager server is currently unavailable, some features wont work. "
                                              "Check your internet connection.")
        self.signals.initialized.emit()
    
    def _do_initialize(self):
        """Perform the slow initialization (runs in a background thread)."""
        try:
            self.pm_manager = PlateModelManager()
            self.raster_manager = PresentDayRasterManager(raster_manifest=os.path.join(os.path.dirname(__file__), "../resources/present_day_rasters.json"))
        except ServerUnavailable:
            self.pm_manager = PlateModelManager(os.path.join(os.path.dirname(__file__), "../resources/empty_json.json"))
            self.raster_manager = PresentDayRasterManager(raster_manifest=os.path.join(os.path.dirname(__file__), "../resources/empty_json.json"))
            self._server_unavailable = True
        
        self.raster_manager.set_data_dir(self.raster_data_dir)

        self.model_list = self.pm_manager.get_available_model_names()
        if not self.model_list:
            self.model_list = ["default"]
        self.model_list.remove("default")
        self.display_model_list = [self.get_display_name(model) for model in self.model_list]
        
        self._initialized = True
        self._init_event.set()
    
    def _ensure_initialized(self):
        """Block the calling thread until initialization is complete.
        
        If start_background_init() was never called, runs _do_initialize()
        synchronously (fallback for direct usage).
        """
        if self._initialized:
            return
        if self._init_thread is None:
            self._do_initialize()
        else:
            self._init_event.wait()
        
    def _get_local_model_names(self):
        """Cached wrapper for pm_manager.get_local_available_model_names."""
        if self._local_model_names_cache is None:
            self._local_model_names_cache = self.pm_manager.get_local_available_model_names(self.model_data_dir)
        return list(self._local_model_names_cache)
    
    def invalidate_cache(self):
        """Clear all cached lookups so the next access re-queries the filesystem / network."""
        self._local_model_names_cache = None
        self._raster_available_cache.clear()
        self._icon_tooltip_cache.clear()
    
    def get_display_name(self, model_name):
        """Convert model name to a more readable format."""
        # Replace underscores with spaces
        model_name = model_name.replace('_', ' ')
        # Capitalize first letter
        model_name = model_name[:1].upper() + model_name[1:]
        # Insert space before the first number
        for i, char in enumerate(model_name):
            if char.isdigit():
                return model_name[:i] + ' ' + model_name[i:]
        return model_name
    
    def get_icon_and_tooltip(self, model_or_raster_name):
        """Get the icon and tooltip for a model or raster (cached)."""
        self._ensure_initialized()
        if model_or_raster_name in self._icon_tooltip_cache:
            return self._icon_tooltip_cache[model_or_raster_name]
        result = ("", "")
        if model_or_raster_name is not None:
            if model_or_raster_name in self.get_available_rasters():
                raster_name = model_or_raster_name
                if self.is_raster_available_locally(raster_name):
                    result = ("✅", "Raster already downloaded")
            else:
                model_name = model_or_raster_name
                if self.model_list != []:
                    if cache_manager.is_model_custom(model_name):
                        result = ("🛠️", "Custom model")
                    elif cache_manager.is_model_available_locally(model_name):
                        result = ("✅", "Already downloaded")
        self._icon_tooltip_cache[model_or_raster_name] = result
        return result
    
    def get_custom_model_names(self):
        """Return the names of locally available models as a list."""
        self._ensure_initialized()
        local_models = self._get_local_model_names()
        for model in self.model_list:
            if model in local_models:
                local_models.remove(model)
        return local_models
        
    def get_available_models(self, required_layers=[]):
        """Return a list of available models, filtering by required layers."""
        self._ensure_initialized()
        available_models = self.display_model_list.copy()
        local_models = self.get_custom_model_names()
        available_models.extend(local_models)

        for layer in required_layers:
            available_models = [model for model in available_models if self.is_layer_available(layer, model)]
        
        return available_models
    
    def is_model_available_locally(self, display_model_name):
        """Check if a model is available locally."""
        self._ensure_initialized()
        local_models = self._get_local_model_names()
        index = self.display_model_list.index(display_model_name)
        model_name = self.model_list[index]
        return model_name in local_models
    
    def is_model_custom(self, model_name):
        """Check if a model is a custom model."""
        self._ensure_initialized()
        custom_models = self.get_custom_model_names()
        return model_name in custom_models
    
    def is_layer_available(self, layer, model_name):
        """Check if a specific layer is available in the given model."""
        model = self.get_model(model_name)
        available_layers = model.get_avail_layers()
        layer = layer.replace(" ", "")
        return layer in available_layers
    
    def get_model(self, display_model_name):
        """Get the model object by its display name."""
        self._ensure_initialized()
        local_models = self.get_custom_model_names()
        if display_model_name in local_models:
            model_name = display_model_name
            model = PlateModel(model_name, data_dir=self.model_data_dir, readonly=True)
        else:
            index = self.display_model_list.index(display_model_name)
            model_name = self.model_list[index]
            model = self.pm_manager.get_model(model_name, self.model_data_dir)
        self.invalidate_cache()
        return model
    
    def get_model_bigtime(self, model_name):
        try:
            model = self.get_model(model_name)
            bigtime = model.get_big_time()
        except Exception:
            bigtime = 1000
        return bigtime
    
    def get_model_smalltime(self, model_name):
        try:
            model = self.get_model(model_name)
            smalltime = model.get_small_time()
        except Exception:
            smalltime = 0
        return smalltime
            
    def download_model(self, model_name, feedback=None):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        
        model = self.get_model(model_name)
        
        rotation_model = model.get_rotation_model()
        if self.is_model_custom(model_name) and feedback:
            feedback.debug(f"Model '{model_name}' available locally, no need to download.")
        if feedback: feedback.progress += 10
        
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        self.invalidate_cache()
        return rotation_model

    def download_all_layers(self, model_name, feedback=None):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        
        model = self.get_model(model_name)
        layers = model.get_avail_layers()
        
        if feedback: feedback.progress += 10
        
        for layer in self.possible_layers:
            layer = layer.replace(" ", "")
            if layer in layers:
                model.get_layer(layer, return_none_if_not_exist=True)
                if self.is_model_custom(model_name) and feedback:
                    feedback.debug(f"Layer '{layer}' for model '{model_name}' available locally, no need to download.")
                if feedback: feedback.progress += 5
        
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        self.invalidate_cache()
    
    def get_layer(self, model_name, layer_name, feedback=None):
        model = self.get_model(model_name)
        layer_name = layer_name.replace(" ", "")
        result = model.get_layer(layer_name, return_none_if_not_exist=True)
        self.invalidate_cache()
        return result
    
    def get_available_rasters(self):
        """Return a list of available rasters. When offline, only return locally available ones."""
        self._ensure_initialized()
        if not self.raster_manager.rasters:
            return [name for name in self.available_rasters
                    if self.is_raster_available_locally(name)]
        return self.available_rasters.keys()
    
    def is_raster_available_locally(self, raster_name):
        """Check if a raster is already downloaded (cached)."""
        self._ensure_initialized()
        if raster_name in self._raster_available_cache:
            return self._raster_available_cache[raster_name]
        internal_name = self.available_rasters[raster_name]
        if internal_name not in self.raster_manager.rasters:
            raster_dir = os.path.join(self.raster_data_dir, internal_name)
            result = os.path.isdir(raster_dir) and any(
                f for f in os.listdir(raster_dir) if not f.startswith('.')
            )
        else:
            downloader = FileDownloader(
                self.raster_manager.rasters[internal_name],
                f"{self.raster_data_dir}/{internal_name}/.metadata.json",
                f"{self.raster_data_dir}/{internal_name}/",
                large_file_hint=True,
            )
            result = not downloader.check_if_file_need_update()
        self._raster_available_cache[raster_name] = result
        return result
    
    def download_raster(self, raster, feedback=None):
        self._ensure_initialized()
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        internal_name = self.available_rasters[raster]
        if internal_name not in self.raster_manager.rasters:
            files = glob.glob(f"{self.raster_data_dir}/{internal_name}/*")
            files = [f for f in files if not os.path.basename(f).startswith('.')]
            if files:
                if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
                return files[0]
            raise FileNotFoundError(
                f"Raster '{internal_name}' is not available on the server and no local copy was found."
            )
        output_filename = self.raster_manager.get_raster(internal_name)
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        self.invalidate_cache()
        return output_filename
    
    def delete_raster(self, raster_name):
        """Delete a raster from the local storage."""
        internal_name = self.available_rasters[raster_name]
        raster_path = os.path.join(self.raster_data_dir, internal_name)
        if os.path.exists(raster_path):
            shutil.rmtree(raster_path)
        self.invalidate_cache()
    
    def get_raster_path(self, raster_name):
        """Get the local path of a raster."""
        raster_name = self.available_rasters[raster_name]
        raster_path = os.path.join(self.raster_data_dir, raster_name)
        if os.path.exists(raster_path):
            return raster_path
        else:
            raise FileNotFoundError(f"Raster {raster_name} not found in {self.raster_data_dir}.")
    
    def is_valid_rotations_file(self, file_path):
        """Check if the given file path is a valid rotations file."""
        if not os.path.isfile(file_path):
            return False
        patterns = self.rotations_allowed_extensions
        if not any(fnmatch.fnmatch(file_path, pattern) for pattern in patterns):
            return False
        return True
    
    def is_valid_layers_file(self, file_path):
        """Check if the given file path is a valid layers file."""
        if not os.path.isfile(file_path):
            return False
        patterns = self.layers_allowed_extensions
        if not any(fnmatch.fnmatch(file_path, pattern) for pattern in patterns):
            return False
        return True
    
    def delete_model(self, model_name):
        """Delete a model from the local storage."""
        self._ensure_initialized()
        model = self.get_model(model_name)
        model.purge()
        self.invalidate_cache()
        
cache_manager = TaCacheManager()
    