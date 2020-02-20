"""
/***************************************************************************
 Terra Antiqua
								 A QGIS plugin
 The Terra Antiqua plugin creates a paleogeographic map of a specific time.
 It modifies present day topography and bathymetry that is rotated to the time
 of reconstruction in Gplates with a set of masks that are also rotated in Gplates.
 
							  -------------------
		begin				: 2019-03-18
		git sha			  : $Format:%H$
		copyright			: (C) 2019 by Jovid Aminov
		email				: jovid.aminov@outlook.com
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""
from PyQt5.QtCore import (
							QSettings,
							QTranslator,
							qVersion,
							QCoreApplication
						)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QToolBar
from qgis.core import QgsExpressionContext, QgsExpressionContextUtils, QgsProject, QgsMapLayerType
import datetime
import os.path



from .compile_tb import TaCompileTopoBathy
from .create_tb import TaCreateTopoBathy
from .create_tb_dlg import TaCreateTopoBathyDlg
from .prepare_masks_dlg import TaPrepareMasksDlg
from .prepare_masks import TaPrepareMasks
from .set_pls import TaSetPaleoshorelines
from .set_pls_dlg import TaSetPaleoshorelinesDlg
from .standard_proc import TaStandardProcessing
from .standard_proc_dlg import TaStandardProcessingDlg
from .compile_tb_dlg import TaCompileTopoBathyDlg
from .modify_tb import TaModifyTopoBathy
from .modify_tb_dlg import TaModifyTopoBathyDlg
from .utils import setRasterSymbology
from .remove_arts import TaPolygonCreator, TaRemoveArtefacts, TaFeatureSink
from .remove_arts_dlg import TaRemoveArtefactsDlg
from .remove_arts_tooltip import TaRemoveArtefactsTooltip
from .settings import TaSettings


class TerraAntiqua:
	
	def __init__(self, iface):
		"""Constructor.

		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		"""
		# Save reference to the QGIS interface
		self.iface = iface
		# the reference to the Map canvas of the current project
		self.canvas = self.iface.mapCanvas()
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'TerraAntiqua_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)

			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)

		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&Terra Antiqua')

		# Create a separate toolbar for the tool
		self.pg_toolBar = iface.mainWindow().findChild(QToolBar, u'Terra Antiqua')
		if not self.pg_toolBar:
			self.pg_toolBar = iface.addToolBar(u'Terra Antiqua')
			self.pg_toolBar.setObjectName(u'Terra Antiqua')
				
		# Load the settings object. Read settings and passes them to the plugin
		self.settings = TaSettings()
		
		# Check if plugin was started the first time in current QGIS session
		# Must be set in initGui() to survive plugin reloads
		self.first_start = None


	# Create the tool dialog

	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		"""Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		"""
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('TerraAntiqua', message)

	def add_action(
			self,
			icon_path,
			text,
			callback,
			enabled_flag = True,
			add_to_menu = True,
			add_to_toolbar = True,
			status_tip = None,
			whats_this = None,
			parent = None,
			checkable = False):
		"""Add a toolbar icon to the toolbar.

		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str

		:param text: Text that should be shown in menu items for this action.
		:type text: str

		:param callback: Function to be called when the action is triggered.
		:type callback: function

		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool

		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool

		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool

		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str

		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget

		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.

		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		"""

		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)
		

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			# Adds plugin icon to Plugins toolbar
			self.pg_toolBar.addAction(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)
		if checkable:
			action.setCheckable(True)
		self.actions.append(action)

		return action

	def initGui(self):
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""

		icons_path = os.path.join(self.plugin_dir, "../resources")
		dem_builder_icon = os.path.join(icons_path, 'icon.png')
		mask_prep_icon = os.path.join(icons_path, 'mask.png')
		topo_modifier_icon = os.path.join(icons_path, 'topomod.png')
		p_coastline_icon = os.path.join(icons_path, 'paleocoastlines.png')
		std_proc_icon = os.path.join(icons_path, 'fill_smooth.png')
		feat_create_icon = os.path.join(icons_path, 'feat_create.png')
		artefact_remover_icon = os.path.join(icons_path, 'artefact_rem.png')

		self.add_action(
			dem_builder_icon,
			text = self.tr(u'Compile Topo/Bathymetry'),
			callback = self.initCompileTopoBathy,
			parent = self.iface.mainWindow())
					
		self.add_action(
			p_coastline_icon,
			text = self.tr(u'Set Paleoshorelines'),
			callback = self.initSetPaleoShorelines,
			parent = self.iface.mainWindow())

		self.add_action(
			topo_modifier_icon,
			text = self.tr(u'Modify Topo/Bathymetry'),
			callback = self.initModifyTopoBathy,
			parent = self.iface.mainWindow())


		self.add_action(
			feat_create_icon,
			text = self.tr(u'Create Topo/Bathymetry'),
			callback = self.initCreateTopoBathy,
			parent = self.iface.mainWindow())


		self.add_action(
			artefact_remover_icon,
			text = self.tr(u'Remove Artefacts'),
			callback = self.initRemoveArtefacts,
			parent = self.iface.mainWindow(),
			checkable = True)
		
		self.add_action(
			mask_prep_icon,
			text = self.tr(u'Prepare masks'),
			callback = self.initPrepareMasks,
			parent = self.iface.mainWindow())
		
		self.add_action(
			std_proc_icon,
			text = self.tr(u'Standard Processing'),
			callback = self.initStandardProcessing,
			parent = self.iface.mainWindow())
		
		# will be set False in run()
		self.first_start = True

	def unload(self):
		"""Removes the plugin menu item and icon from QGIS GUI."""
		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&Paleogeography'),
				action)
			self.iface.removeToolBarIcon(action)
	
	def initCompileTopoBathy(self):
		"""Initializes the Compile Topo/Bathymetry algotithm and loads it"""
		self.compileTopoBathy = TaAlgorithm(TaCompileTopoBathyDlg, TaCompileTopoBathy, self.iface)
		self.compileTopoBathy.load()
	
	def initPrepareMasks(self):
		"""Initializes the Prepare masks algorithm and loads it"""
		self.prepareMasks = TaAlgorithm(TaPrepareMasksDlg, TaPrepareMasks, self.iface)
		self.prepareMasks.load()
	
	def initModifyTopoBathy(self):
		"""Initializes the Modify Topo/Bathymetry algorithm and loads it"""
		self.modifyTopoBathy = TaAlgorithm(TaModifyTopoBathyDlg, TaModifyTopoBathy, self.iface)
		self.modifyTopoBathy.load()

	
	def initSetPaleoShorelines(self):
		"""Initializes the Set Paleoshorelines algorithm and loads it"""
		self.setPaleoshorelines = TaAlgorithm(TaSetPaleoshorelinesDlg, TaSetPaleoshorelines, self.iface)
		self.setPaleoshorelines.load()
		
	def initStandardProcessing(self):
		"""Initializes the Standard processing algorithm set and loads it"""
		self.standardProcessing = TaAlgorithm(TaStandardProcessingDlg, TaStandardProcessing, self.iface)
		self.standardProcessing.load()

	def initCreateTopoBathy(self):
		"""Initializes the Create Topography/Bathymetry algorithm and loads it"""
		self.createTopoBathy = TaAlgorithm(TaCreateTopoBathyDlg, TaCreateTopoBathy, self.iface)
		self.createTopoBathy.load()
	
	def initRemoveArtefacts(self):
		"""Initializes the Remove artefacts algorithm and activates it"""
		if self.settings.removeArtefactsChecked:
			self.removeArtefacts.storeRubberbands(self.removeArtefacts.toolPoly.rubberband, self.removeArtefacts.toolPoly.vertices, self.removeArtefacts.toolPoly.points)
			self.removeArtefacts.clean()
		else:
			self.settings.removeArtefactsChecked = True
			self.removeArtefacts = TaRemoveArtefacts(TaRemoveArtefactsTooltip, TaRemoveArtefactsDlg, self.iface, self.actions, self.settings)
			self.removeArtefacts.initiate()
		
		
	

		

class TaAlgorithm:
	
	def __init__(self, dlg, thread, iface):
		self.dlg = dlg()
		self.thread = thread(self.dlg)
		self.iface = iface
		
	
	def load(self):
		self.dlg.show()
		self.dlg.runButton.clicked.connect(self.start)
		self.dlg.cancelButton.clicked.connect(self.stop)
		try:
			self.dlg.Tabs.setCurrentIndex(0)
		except Exception:
			pass
	
	def start(self):
		try:
			self.dlg.Tabs.setCurrentIndex(1)
		except Exception:
			pass
		self.dlg.cancelButton.setEnabled(True)
		self.dlg.runButton.setEnabled(False)
		self.thread.progress.connect(self.dlg.setProgressValue)
		self.thread.log.connect(self.log)
		self.thread.start()
		self.thread.finished.connect(self.add_result)
	
	def stop(self):
		self.thread.kill()
		self.dlg.resetProgressValue()
		self.dlg.cancelButton.setEnabled(False)
		self.dlg.runButton.setEnabled(True)
		self.log("The algorithm did not finish successfully, because the user canceled processing.")
		self.log("Or something went wrong. Please, refer to the log above for more details.")
		self.dlg.warningLabel.setText('Error!')
		self.dlg.warningLabel.setStyleSheet('color:red')
	
	def finish(self):
		self.dlg.cancelButton.setEnabled(False)
		self.dlg.runButton.setEnabled(True)
		self.dlg.warningLabel.setText('Done!')
		self.dlg.warningLabel.setStyleSheet('color:green')

	def log(self, msg):
		# get the current time
		time = datetime.datetime.now()
		time = "{}:{}:{}".format(time.hour, time.minute, time.second)
		if msg.split(' ')[0].lower() == 'error:' or msg.split(':')[0].lower() == 'error':
			msg = '<span style="color: red;">{} </span>'.format(msg)
		elif msg.split(' ')[0].lower() == 'warning:'.lower() or msg.split(':')[0].lower() == 'warning':
			msg = '<span style="color: blue;">{} </span>'.format(msg)
		
		#msg=msg.replace("<", "&lt;")
		#msg=msg.replace(">", "&gt;")
		self.dlg.logText.textCursor().insertHtml("{} - {} <br>".format(time, msg))
	
	def add_result(self, finished, output_path):
		if finished is True:
			file_name = os.path.splitext(os.path.basename(output_path))[0]
			ext = os.path.splitext(os.path.basename(output_path))[1]
			if ext == '.tif' or ext == '.tiff':
				layer = self.iface.addRasterLayer(output_path, file_name, "gdal")
			elif ext == '.shp':
				layer = self.iface.addVectorLayer(output_path, file_name, "ogr")
			if layer:
				# Rendering a symbology style for the resulting raster layer.
				if layer.type() == QgsMapLayerType.RasterLayer:
					setRasterSymbology(layer)
				else:
					pass
				self.log("The algorithm finished processing successfully,")
				self.log("and added the resulting raster/vector layer to the map canvas.")
			else:
				self.log("The algorithm finished successfully,")
				self.log("however the resulting layer did not load. You may need to load it manually.")
			self.finish()
		else:
			self.stop()
			
class TaRemoveArtefacts:
	
	def __init__(self, dlg1, dlg, iface, actions, settings):
		self.dlg = dlg()
		self.tooltip = dlg1()
		self.actions = actions
		self.settings = settings
		self.iface = iface
		self.canvas = self.iface.mapCanvas()
		self.nFeatures = None
		self.rbCollection = None
		self.pointCollection = None
		self.vertexCollection = None
		
		self.dlg.runButton.clicked.connect(self.start)
		self.dlg.cancelButton.clicked.connect(self.stop)
		self.dlg.addButton.clicked.connect(self.createPolygon)
		self.dlg.closeButton.clicked.connect(self.clean)
	
	def initiate(self):
		if self.tooltip.showAgain:
			self.tooltip.show()
			self.tooltip.accepted.connect(self.drawPolygon)
		else:
			self.drawPolygon()
	def drawPolygon(self):
		if self.tooltip.showAgain:
			if self.tooltip.showAgainCheckBox.isChecked():
				self.tooltip.setShowable(False)
		if not self.nFeatures:
			self.nFeatures = 0
		self.toolPoly = TaPolygonCreator(self.canvas, self.iface)
		self.toolPoly.finished.connect(self.load)
		self.canvas.setMapTool(self.toolPoly)
		for action in self.actions:
			if action.text() == "Remove Artefacts":
				self.toolPoly.setAction(action)

	
	def load(self):
		self.storeRubberbands(self.toolPoly.rubberband, self.toolPoly.vertices, self.toolPoly.points)
		self.dlg.show()
		if self.nFeatures==0:
			context = QgsExpressionContext()
			context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
			crs = context.variable("project_crs")
			self.feature_sink = TaFeatureSink(crs)
		
		
	
	def createPolygon(self):
		self.nFeatures+=1
		expr = self.dlg.exprLineEdit.value()
		geom = self.toolPoly.geometry
		self.feature_sink.createFeature(geom, expr)
		self.dlg.hide()
		self.drawPolygon()
		
	
	def start(self):
		expr = self.dlg.exprLineEdit.value()
		geom = self.toolPoly.geometry
		self.feature_sink.createFeature(geom, expr)
		self.vl = self.feature_sink.getVectorLayer()
		self.dlg.Tabs.setCurrentIndex(1)  # switch to the log tab.
		self.dlg.cancelButton.setEnabled(True)
		self.dlg.runButton.setEnabled(False)
		self.thread = TaRemoveArtefacts(self.vl, self.dlg, self.iface)
		self.thread.progress.connect(self.dlg.setProgressValue)
		self.thread.log.connect(self.log)
		self.thread.start()
		self.thread.finished.connect(self.addResult)
		self.nFeatures = 0
		
	
	def stop(self):
		self.thread.kill()
		self.dlg.resetProgressValue()
		self.dlg.cancelButton.setEnabled(False)
		self.dlg.runButton.setEnabled(True)
		self.log("The algorithm did not finish successfully, because the user canceled processing.")
		self.log("Or something went wrong. Please, refer to the log above for more details.")
		self.dlg.warningLabel.setText('Error!')
		self.dlg.warningLabel.setStyleSheet('color:red')
		self.nFeatures = 0
		self.clean()
	
	def storeRubberbands(self, rb, vrtx, pnt):
		if not self.rbCollection:
			self.rbCollection = []
		if not self.pointCollection:
			self.pointCollection = []
		if not self.vertexCollection:
			self.vertexCollection = []
		
		self.rbCollection.append(rb)
		self.pointCollection.append(pnt)
		self.vertexCollection.append(vrtx)
	
	
	def log(self, msg):
		# get the current time
		time = datetime.datetime.now()
		time = "{}:{}:{}".format(time.hour, time.minute, time.second)
		if msg.split(' ')[0].lower() == 'error:' or msg.split(':')[0].lower() == 'error':
			msg = '<span style="color: red;">{} </span>'.format(msg)
		elif msg.split(' ')[0].lower() == 'warning:'.lower() or msg.split(':')[0].lower() == 'warning':
			msg = '<span style="color: blue;">{} </span>'.format(msg)
		
		#msg=msg.replace("<", "&lt;")
		#msg=msg.replace(">", "&gt;")
		self.dlg.logText.textCursor().insertHtml("{} - {} <br>".format(time, msg))

	def addResult(self, finished, output_path):
		if finished is True:
			file_name = os.path.splitext(os.path.basename(output_path))[0]
			rlayer = self.iface.addRasterLayer(output_path, file_name, "gdal")
			if rlayer:
				setRasterSymbology(rlayer)
				self.log("The artefacts were removed successfully,")
				self.log(
					"and the resulting layer is added to the map canvas with the following name: {}.".format(file_name))
			else:
				self.log("The algorithm has removed artefacts successfully,")
				self.log("however the resulting layer did not load. You may need to load it manually.")
				self.log("The modified raster is saved at: {}".format(output_path))
			self.finish()
		else:
			self.stop()
	def finish(self):
			self.dlg.cancelButton.setEnabled(False)
			self.dlg.runButton.setEnabled(True)
			self.dlg.warningLabel.setText('Done!')
			self.dlg.warningLabel.setStyleSheet('color:green')
			self.clean()
	def clean(self):
		self.iface.actionPan().trigger()
		try:
			self.toolPoly.removePolygons(self.rbCollection, self.pointCollection, self.vertexCollection)
			self.nFeatures = 0
		except Exception:
			pass

		self.settings.removeArtefactsChecked = False