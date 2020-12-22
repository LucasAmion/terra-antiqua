


from PyQt5.QtWidgets import (
    QComboBox
)
from qgis.gui import QgsSpinBox

from .base_dialog import TaBaseDialog
from .widgets import (
    TaRasterLayerComboBox,
    TaCheckBox,
    TaVectorLayerComboBox
)

class TaStandardProcessingDlg(TaBaseDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(TaStandardProcessingDlg, self).__init__(parent)
        self.defineParameters()
        self.fillingTypeBox.currentTextChanged.connect(self.reloadHelp)

    def defineParameters(self):
        self.fillingTypeBox = self.addParameter(QComboBox, "How would you like to process the input DEM?")
        self.fillingTypeBox.addItems(["Fill gaps",
                                      "Copy/Paste raster",
                                      "Smooth raster",
                                      "Isostatic compensation",
                                      "Set new sea level",
                                      "Calculate bathymetry"])
        self.baseTopoBox = self.addMandatoryParameter(TaRasterLayerComboBox,
                                                      "Raster to be modified:",
                                                      "TaMapLayerComboBox")
        #Parameters for filling the gaps
        self.interpInsidePolygonCheckBox = self.addVariantParameter(TaCheckBox,
                                                                    "Fill gaps",
                                                                    "Interpolate inside polygon(s) only.")
        self.masksBox = self.addVariantParameter(TaVectorLayerComboBox,
                                                 "Fill gaps",
                                                 "Mask layer:",
                                                 "TaMapLayerComboBox")
        self.interpInsidePolygonCheckBox.registerEnabledWidgets([self.masksBox])
        self.smoothingBox = self.addVariantParameter(TaCheckBox, "Fill gaps",
                                                     "Smooth the resulting raster")
        self.smoothingTypeBox = self.addVariantParameter(QComboBox,
                                                         "Fill gaps",
                                                         "Smoothing type:")
        self.smoothingTypeBox.addItems(["Gaussian filter",
                                        "Uniform filter"])
        self.smFactorSpinBox = self.addVariantParameter(QgsSpinBox,
                                                        "Fill gaps",
                                                        "Smoothing factor (in grid cells):")
        self.smFactorSpinBox.setMinimum(1)
        self.smFactorSpinBox.setMaximum(5)
        self.smoothingBox.registerEnabledWidgets([self.smoothingTypeBox,
                                                  self.smFactorSpinBox])

        #Parameters for Copying and pasting raster data
        self.copyFromRasterBox = self.addVariantParameter(TaRasterLayerComboBox,
                                                          "Copy/Paste raster",
                                                          "Raster to copy values from:",
                                                          "TaMapLayerComboBox",
                                                          mandatory = True)
        self.copyFromMaskBox = self.addVariantParameter(TaVectorLayerComboBox,
                                                        "Copy/Paste raster",
                                                        "Mask layer:",
                                                        "TaMapLayerComboBox",
                                                        mandatory = True)

        #Parameters for smothing rasters
        self.smoothingTypeBox2 = self.addVariantParameter(QComboBox,
                                                          "Smooth raster",
                                                          "Smoothing type:")
        self.smFactorSpinBox2 = self.addVariantParameter(QgsSpinBox,
                                                         "Smooth raster",
                                                         "Smoothing factor (in grid cells):")
        self.smoothingTypeBox2.addItems(["Gaussian filter",
                                         "Uniform filter"])
        self.smFactorSpinBox2.setMinimum(1)
        self.smFactorSpinBox2.setMaximum(5)

        #Parameters for Isostatic compensation
        self.selectIceTopoBox = self.addVariantParameter(TaRasterLayerComboBox,
                                                         "Isostatic compensation",
                                                         "Ice topography raster:",
                                                         mandatory = True)
        self.isostatMaskBox = self.addVariantParameter(TaVectorLayerComboBox,
                                                       "Isostatic compensation",
                                                       "Mask layer:",
                                                       mandatory = True)
        self.masksFromCoastCheckBox = self.addVariantParameter(
                                        TaCheckBox,
                                        "Isostatic compensation",
                                        "Get polar regions automatically.")
        self.iceAmountSpinBox = self.addVariantParameter(
                                        QgsSpinBox,
                                        "Isostatic compensation",
                                        "Amount of the ice to be removed (in %)"
                                        )
        self.iceAmountSpinBox.setMinimum(0)
        self.iceAmountSpinBox.setMaximum(100)
        self.iceAmountSpinBox.setValue(30)


        #Parameters for Setting sea level
        self.seaLevelShiftBox = self.addVariantParameter(QgsSpinBox,
                                                         "Set new sea level",
                                                         "Amount of sea level shift:")
        self.seaLevelShiftBox.setMinimum(-1000)
        self.seaLevelShiftBox.setMaximum(1000)
        self.seaLevelShiftBox.setValue(100)

        #Parameters for calculating bathymetry from ocean age
        self.reconstructionTime = self.addVariantParameter(QgsSpinBox,
                                                          "Calculate bathymetry",
                                                          "Reconstruction time:")


        self.fillDialog()
        self.showVariantWidgets(self.fillingTypeBox.currentText())
        self.fillingTypeBox.currentTextChanged.connect(self.showVariantWidgets)

    def reloadHelp(self):
        """
        Sets the name of the chosen processing algorithm (e.g. Smooth raster) to the dialog so that it can load the help
        file properly."""
        processing_alg_names = [("Fill gaps", "TaFillGaps"),
                                ("Copy/Paste raster", "TaCopyPasteRaster"),
                                ("Smooth raster", "TaSmoothRaster"),
                                ("Isostatic compensation", "TaIsostaticCompensation"),
                                ("Set new sea level", "TaSetSeaLevel"),
                                ("Calculate bathymetry", "TaCalculateBathymetry")]
        for alg, name in processing_alg_names:
            if self.fillingTypeBox.currentText() == alg:
                self.setDialogName(name)
        self.loadHelp()