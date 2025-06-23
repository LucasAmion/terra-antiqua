from appdirs import user_data_dir
from plate_model_manager import PlateModelManager, PresentDayRasterManager, PlateModel
import logging
import os
import fnmatch

class TaCacheManager:
    
    available_rasters = {
        0: "etopo_bed_60",
        1: "etopo_bed_30",
        2: "etopo_ice_60",
        3: "etopo_ice_30"
    }
    
    rotations_allowed_extensions = ["*.rot", "*.grot"]
    
    layers_allowed_extensions = ["*.gpml", "*.gpmlz", "*.gpml.gz", "*.dat", "*.pla", "*.shp", "*.geojson", "*.json", "*.gpkg", "*.gmt", "*.vgp"]
    
    possible_layers = ["Topologies", "Coastlines", "COBs", "StaticPolygons", "ContinentalPolygons"]

    def __init__(self):
        data_dir = user_data_dir("QGIS3", "QGIS")
        self.model_data_dir = os.path.join(data_dir, "plugins", "terra_antiqua", "models")
        self.pm_manager = PlateModelManager()
        
        raster_data_dir = os.path.join(data_dir, "plugins", "terra_antiqua", "rasters")
        self.raster_manager = PresentDayRasterManager(os.path.join(os.path.dirname(__file__), "../resources/present_day_rasters.json"))
        self.raster_manager.set_data_dir(raster_data_dir)
        
        self.pmm_logger = logging.getLogger('pmm')
        self.pmm_logger.setLevel(logging.DEBUG)

        self.model_list = self.pm_manager.get_available_model_names()
        self.model_list.remove("default")
        
        self.display_model_list = [self.get_display_name(model) for model in self.model_list]
        
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
    
    def get_custom_model_names(self):
        """Return the names of locally available models as a list."""
        local_models = self.pm_manager.get_local_available_model_names(self.model_data_dir)
        custom_models = []
        for model in local_models:
            if model not in self.model_list:
                custom_models.append(model)
        return custom_models
        
    def get_available_models(self, required_layers=[]):
        """Return a list of available models, filtering by required layers."""
        available_models = self.display_model_list.copy()
        local_models = self.get_custom_model_names()
        available_models.extend(local_models)

        for layer in required_layers:
            for model in available_models:
                if not self.is_layer_available(layer, model):
                    available_models.remove(model)
        
        return available_models
    
    def is_model_available_locally(self, display_model_name):
        """Check if a model is available locally."""
        local_models = self.pm_manager.get_local_available_model_names(self.model_data_dir)
        index = self.display_model_list.index(display_model_name)
        model_name = self.model_list[index]
        return model_name in local_models
    
    def is_model_custom(self, model_name):
        """Check if a model is a custom model."""
        custom_models = self.get_custom_model_names()
        return model_name in custom_models
    
    def is_layer_available(self, layer, model_name):
        """Check if a specific layer is available in the given model."""
        model = self.get_model(model_name)
        available_layers = model.get_avail_layers()
        return layer in available_layers
    
    def get_model(self, display_model_name):
        """Get the model object by its display name."""
        local_models = self.get_custom_model_names()
        if display_model_name in local_models:
            model_name = display_model_name
            model = PlateModel(model_name, data_dir=self.model_data_dir, readonly=True)
        else:
            index = self.display_model_list.index(display_model_name)
            model_name = self.model_list[index]
            model = self.pm_manager.get_model(model_name, self.model_data_dir)
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
        if feedback: feedback.progress += 10
        
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        return rotation_model

    def download_all_layers(self, model_name, feedback=None):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        
        model = self.get_model(model_name)
        layers = model.get_avail_layers()
        
        if feedback: feedback.progress += 10
        
        for layer in layers:
            if layer in self.possible_layers:
                model.get_layer(layer, return_none_if_not_exist=True)
                if feedback: feedback.progress += 10
        
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
    
    def get_layer(self, model_name, layer_name, feedback=None):
        model = self.get_model(model_name)
        return model.get_layer(layer_name, return_none_if_not_exist=True)
    
    def download_raster(self, rasterIdx, feedback):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        output_filename = self.raster_manager.get_raster(self.available_rasters[rasterIdx])
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        
        return output_filename
    
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
        model = self.get_model(model_name)
        model.purge()
        
cache_manager = TaCacheManager()
    