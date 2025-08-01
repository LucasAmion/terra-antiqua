#Copyright (C) 2021 by Jovid Aminov, Diego Ruiz, Guillaume Dupont-Nivet
#Terra Antiqua is a plugin for the software QGis that deals with the reconstruction of paleogeography.
#Full copyright notice in file: terra_antiqua.py


# -*- coding: utf-8 -*-
import os
from PyQt5 import QtWidgets, QtCore
from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsRasterLayer
from qgis.gui import (
    QgsMapLayerComboBox,
    QgsDoubleSpinBox, QgsGroupBoxCollapseButton
)
from .base_dialog import TaBaseDialog
from .widgets import (
    TaVectorLayerComboBox,
    TaTableWidget,
    TaButtonGroup,
    TaCheckBox
)

class TaCompileTopoBathyDlg(TaBaseDialog):
    openRasterButtonSignal=QtCore.pyqtSignal(QtWidgets.QWidget)
    def __init__(self, parent=None):
        super(TaCompileTopoBathyDlg, self).__init__(parent)
        self.openRasterButtonSignal.connect(self.openRasterFromDisk)
        self.defineParameters()
        # fill the parameters tab of the dialog with widgets appropriate to defined parameters
        self.fillDialog()

    def defineParameters(self):
       """ Adds parameters to a list object that is used by the TaBaseDialog
       class to create widgets and place them in parameters tab.
       """
       self.tableWidget = self.addParameter(TaTableWidget)
       self.itemControlButtons = self.addParameter(TaButtonGroup)
       self.itemControlButtons.add.clicked.connect(self.addRow)
       self.itemControlButtons.remove.clicked.connect(self.removeRow)
       self.itemControlButtons.down.clicked.connect(self.tableWidget.moveRowDown)
       self.itemControlButtons.up.clicked.connect(self.tableWidget.moveRowUp)
       self.tableWidget.insertColumn(0)
       self.tableWidget.insertColumn(1)
       self.tableWidget.setHorizontalHeaderLabels(["Input layer", ""])
       header = self.tableWidget.horizontalHeader()
       header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
       header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
       self.tableWidget.setMinimumHeight(200)
       self.addRow(0)

       #Add advanced parameters
       self.removeOverlapBathyCheckBox = self.addAdvancedParameter(TaCheckBox,
                                                           label='Remove overlapping bathymetry',
                                                           widget_type='CheckBox')
       self.maskComboBox = self.addAdvancedParameter(TaVectorLayerComboBox,
                                                     label="Mask layer:",
                                                     widget_type="TaMapLayerComboBox")
       self.selectedFeaturesCheckBox = self.addAdvancedParameter(TaCheckBox,
                                                                 label = ("Selected features only"),
                                                                 widget_type = "CheckBox")
       self.bufferDistanceForRemoveOverlapBath = self.addAdvancedParameter(QgsDoubleSpinBox, "Buffer distance (In map units):")

       self.maskComboBox.layerChanged.connect(self.onLayerChange)
       self.removeOverlapBathyCheckBox.registerEnabledWidgets([self.maskComboBox,
                                                               self.bufferDistanceForRemoveOverlapBath])
       self.removeOverlapBathyCheckBox.stateChanged.connect(self.onRemoveOverlapCheckBoxStateChange)
       self.selectedFeaturesCheckBox.registerLinkedWidget(self.maskComboBox)
       self.bufferDistanceForRemoveOverlapBath.setValue(0.5)

    def addRow(self, row):
        if not row:
            row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setCellWidget(row, 0, QgsMapLayerComboBox(self))
        self.tableWidget.setCellWidget(row, 1, QgsGroupBoxCollapseButton(self))
        if self.tableWidget.columnCount()>2:
            checkBoxWidget = QtWidgets.QWidget()
            checkBox = TaCheckBox('')
            checkBox.setObjectName("apply_mask_checkbox")
            layout = QtWidgets.QHBoxLayout(checkBoxWidget)
            layout.addWidget(checkBox)
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            self.tableWidget.setCellWidget(row, 2,checkBoxWidget)
        btn = self.tableWidget.cellWidget(row, 1)
        btn.setText('...')
        btn.setIconSize(QtCore.QSize(10,10))
        filter_model= QgsMapLayerProxyModel()
        filter_model.setFilters(QgsMapLayerProxyModel.RasterLayer)
        cmb = self.tableWidget.cellWidget(row, 0)
        cmb.setFilters(filter_model.filters())
        btn.clicked.connect(lambda: self.openRasterButtonSignal.emit(cmb))
        self.tableWidget.setCurrentCell(row,0)

    def removeRow(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        rows_selected = [i.row() for i in selected_rows]
        if not len(rows_selected)>0:
            self.msgBar.pushWarning("Warning:", "No row is selected. Click on the row number to select it.")
        else:
            for index in selected_rows:
                if self.tableWidget.rowCount()>1:
                    self.tableWidget.removeRow(index.row())


    def openRasterFromDisk(self, cmb):
        fd = QtWidgets.QFileDialog()
        filter = "Raster files (*.jpg *.tif *.grd *.nc *.png *.tiff)"
        fname, _ = fd.getOpenFileName(caption='Select a vector layer', directory=None, filter=filter)

        if fname:
            name, _ = os.path.splitext(os.path.basename(fname))
            rlayer = QgsRasterLayer(fname, name, 'gdal')
            QgsProject.instance().addMapLayer(rlayer)
            cmb.setLayer(rlayer)

    def addColumn(self):
        self.tableWidget.insertColumn(2)
        self.tableWidget.setHorizontalHeaderLabels(["Input layer", "", "Apply mask"])
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        for i in range(self.tableWidget.rowCount()):
            checkBoxWidget = QtWidgets.QWidget()
            checkBox = TaCheckBox('')
            checkBox.setObjectName("apply_mask_checkbox")
            layout = QtWidgets.QHBoxLayout(checkBoxWidget)
            layout.addWidget(checkBox)
            layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            self.tableWidget.setCellWidget(i, 2,checkBoxWidget)


    def onLayerChange(self, layer):
        if layer and not self.tableWidget.columnCount()>2:
            self.addColumn()
        elif not layer and self.tableWidget.columnCount()>2:
            self.tableWidget.removeColumn(2)
            header = self.tableWidget.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)

    def onRemoveOverlapCheckBoxStateChange(self, state):
        if state == QtCore.Qt.CheckState.Checked:
            self.maskComboBox.setLayer(self.maskComboBox.layer(1))
        else:
            self.maskComboBox.setLayer(self.maskComboBox.layer(0))

