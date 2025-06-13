from appdirs import user_data_dir
from plate_model_manager import PlateModelManager, PresentDayRasterManager
import logging
import os

class TaCacheManager:
    
    available_rasters = {
        0: "etopo_bed_60",
        1: "etopo_bed_30",
        2: "etopo_ice_60",
        3: "etopo_ice_30"
    }
    
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
        
    def get_available_models(self, required_layers=[]):
        available_models = self.display_model_list.copy()
        for layer in required_layers:
            for model in available_models:
                if not self.is_layer_available(layer, model):
                    available_models.remove(model)
        return available_models
    
    def is_layer_available(self, layer, model_name):
        model = self.get_model(model_name)
        available_layers = model.get_avail_layers()
        return layer in available_layers
    
    def get_model(self, display_model_name):
        """Get the model object by its display name."""
        index = self.display_model_list.index(display_model_name)
        model_name = self.model_list[index]
        return self.pm_manager.get_model(model_name)
    
    def get_model_bigtime(self, model_name):
        try:
            model = self.get_model(model_name)
            bigtime = model.get_big_time()
        except:
            bigtime = 1000
        return bigtime
            
    def download_model(self, model_name, feedback=None):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        
        model = self.get_model(model_name)
        model.set_data_dir(self.model_data_dir)
        
        rotation_model = model.get_rotation_model()
        if feedback: feedback.progress += 10
        
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        return rotation_model
    
    def download_layer(self, model_name, layer_name, feedback=None):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        
        model = self.get_model(model_name)
        model.set_data_dir(self.model_data_dir)
        
        layer = model.get_layer(layer_name, return_none_if_not_exist=True)
        if feedback: feedback.progress += 10
        
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        return layer
    
    def download_raster(self, rasterIdx, feedback):
        if feedback: self.pmm_logger.addHandler(feedback.log_handler)
        output_filename = self.raster_manager.get_raster(self.available_rasters[rasterIdx])
        if feedback: self.pmm_logger.removeHandler(feedback.log_handler)
        
        return output_filename
    
cache_manager = TaCacheManager()
    