#This script creates a dialog form for our second tool in the plugin
import os

from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsVectorLayer, QgsRasterLayer
import os
import datetime


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'paleoshorelines_dialog_base.ui'))

class PaleoshorelinesDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(PaleoshorelinesDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS2.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #Set the mode of QgsFileWidget to directory mode
        self.outputPath.setStorageMode(self.outputPath.SaveFile)
        self.outputPath.setFilter('*.tif;;*.tiff')
        #Base topography layer
        self.baseTopoBox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.baseTopoBox.setLayer(None)
        # Connect the tool buttons to the file dialog that opens raster layers from disk
        self.selectTopoBaseButton.clicked.connect(self.addLayerToBaseTopo)


        #Input masks layer
        self.masksBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.masksBox.setLayer(None)
        # Connect the tool buttons to the file dialog that opens vector layers from disk
        self.selectMasksButton.clicked.connect(self.addLayerToMasks)

        self.logText.clear()
        self.logText.setReadOnly(True)


       #Set the run button enabled only when the user selected input layers.
        self.runButton.setEnabled(False)
        self.masksBox.layerChanged.connect(self.enableRunButton)
        self.baseTopoBox.layerChanged.connect(self.enableRunButton)
        
        #set the help text in the  help box (QTextBrowser)
        path_to_file = os.path.join(os.path.dirname(__file__),"help_text/help_Paleoshorelines.html")
        help_file = open(path_to_file, 'r', encoding='utf-8')
        help_text = help_file.read()
        self.helpBox.setHtml(help_text)


    def enableRunButton(self):
        if  self.baseTopoBox.currentLayer()!=None and self.masksBox.currentLayer()!=None:
            self.runButton.setEnabled(True)
            self.warningLabel.setText('')
        else:
            self.warningLabel.setText('Please, select all the mandatory fields.')
            self.warningLabel.setStyleSheet('color:red')


    # Function for enbling comboboxes for specifying a column in the attribute table
    # of the masks  layer where the names of the masks are stored. This will be used
    # to query only masks, which we need.

    def enableMaskField(self, state):
        if state > 0:
            self.maskNameField.setEnabled(False)
            self.maskNameText.setEnabled(False)

        else:
            self.maskNameField.setEnabled(True)
            self.maskNameText.setEnabled(True)

    def addLayerToBaseTopo(self):
        self.openRasterFromDisk(self.baseTopoBox)

    def addLayerToMasks(self):
        self.openVectorFromDisk(self.masksBox)

    def openVectorFromDisk(self, box):
        fd = QFileDialog()
        filter = "Vector files (*.shp)"
        fname, _ = fd.getOpenFileName(caption='Select a vector layer', directory=None, filter=filter)

        if fname:
            name, _ = os.path.splitext(os.path.basename(fname))
            vlayer = QgsVectorLayer(fname, name, 'ogr')
            QgsProject.instance().addMapLayer(vlayer)
            box.setLayer(vlayer)

    def openRasterFromDisk(self, box):
        fd = QFileDialog()
        filter = "Raster files (*.jpg *.tif *.grd *.nc *.png *.tiff)"
        fname, _ = fd.getOpenFileName(caption='Select a vector layer', directory=None, filter=filter)

        if fname:
            name, _ = os.path.splitext(os.path.basename(fname))
            rlayer = QgsRasterLayer(fname, name, 'gdal')
            QgsProject.instance().addMapLayer(rlayer)
            box.setLayer(rlayer)

    # Get the fields of the masks layer displaed in the field comboboxes
    def setFieldsInLayer(self):
        self.maskNameField.setLayer(self.masksBox.currentLayer())


        self.formulaField.setLayer(self.masksBox.currentLayer())


        self.minField.setLayer(self.masksBox.currentLayer())
        self.maxField.setLayer(self.masksBox.currentLayer())

        self.minValueField.setLayer(self.masksBox.currentLayer())
        self.maxValueField.setLayer(self.masksBox.currentLayer())

    #Set the groupbox for formula enabled.
    def setFormulaEnabled(self,state):
        if state > 0:
            self.formulaGroupBox.setEnabled(True)
            self.minMaxCheckBox.setChecked(False)
            self.minMaxGroupBox.setEnabled(False)
            self.minMaxGroupBox.setCollapsed(True)
            self.formulaGroupBox.setCollapsed(False)
            self.min_maxValueCheckBox.setChecked(True)


    #Set the groupbox for specifing final minimum and maximum values enabled.\
    #This is enabled if the user wants to use final minimuum and maximum values
    #for flattening and roughening instead of a formula.
    def setMinMaxEnabled(self, state):
        if state > 0:
            self.minMaxGroupBox.setEnabled(True)
            self.formulaCheckBox.setChecked(False)
            self.formulaGroupBox.setEnabled(False)
            self.formulaGroupBox.setCollapsed(True)
            self.minMaxGroupBox.setCollapsed(False)

    #Set fields for minimum and maximum values enabled. This is needed, when the user wants
    #get the minimum and maximum values from the attribute table
    def setMinMaxFromAttrEnabled(self, state):
        if state > 0:
            self.minField.setEnabled(True)
            self.maxField.setEnabled(True)
            self.minSpin.setEnabled(False)
            self.maxSpin.setEnabled(False)
        else:
            self.minField.setEnabled(False)
            self.maxField.setEnabled(False)
            self.minSpin.setEnabled(True)
            self.maxSpin.setEnabled(True)

    def setBoundingValuesForModification(self,state):
        if state>0:
            self.minValueField.setEnabled(True)
            self.maxValueField.setEnabled(True)
            self.minValueSpin.setEnabled(True)
            self.maxValueSpin.setEnabled(True)
            self.minMaxValuesFromAttrCheckBox.setEnabled(True)
            self.minMaxValuesFromSpinCheckBox.setEnabled(True)

            self.boundingValuesGroupBox.show()
        else:
            self.minValueField.setEnabled(False)
            self.maxValueField.setEnabled(False)
            self.minValueSpin.setEnabled(False)
            self.maxValueSpin.setEnabled(False)
            self.minMaxValuesFromAttrCheckBox.setEnabled(False)
            self.minMaxValuesFromSpinCheckBox.setEnabled(False)


            self.boundingValuesGroupBox.hide()

    def setBoundingValuesFromAttrEnabled(self, state):
        if state>0:
            self.minValueField.setEnabled(True)
            self.maxValueField.setEnabled(True)
            self.minValueSpin.setEnabled(False)
            self.maxValueSpin.setEnabled(False)
            self.minMaxValuesFromSpinCheckBox.setChecked(False)
    def setBoundingValuesFromSpinEnabled(self, state):
        if state>0:
            self.minValueField.setEnabled(False)
            self.maxValueField.setEnabled(False)
            self.minValueSpin.setEnabled(True)
            self.maxValueSpin.setEnabled(True)
            self.minMaxValuesFromAttrCheckBox.setChecked(False)




    def log(self,msgs):
        #get the current time
        time=datetime.datetime.now()
        time=str(time.hour)+':'+str(time.minute)+':'+str(time.second)
        msg=' '
        for m in msgs:
            msg=msg+' '+m

        # inserting log messages into the qplantextedit widget
        self.logText.textCursor().insertText(time+' - '+msg+' \n')

       #log_handler.setFormatter(logging.Formatter('\n %(asctime)s - %(levelname)s - %(message)s'))









