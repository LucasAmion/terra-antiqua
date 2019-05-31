# -*- coding: utf-8 -*-

import numpy as np
from osgeo import gdal, gdalconst

import os
from .topo_modifier_dialog import TopoModifierDialog  as td




class TopoTools:
	def __init__(self):
		pass

	def mod_min_max(in_array, fmin:int, fmax:int):
		"""
		Modifies the elevation/bathimetry
		values based on the current and provided
		minimum and maximum values.
		This is basically flattening and roughening.
		:param in_array: input numpy array for modification.
		:param fmin: final minimum value of elevation/bathymetry.
		:param fmax: final maximum value of elevation/bathymetry.
		:return: modified array of eleveation/bathymetry values.
		"""

		#Define the initial minimum and maximum values of the array
		#imin = in_array.min()
		imax = in_array[np.isfinite(in_array)].max()
		out_array=in_array

		ratio=(imax-fmin)/(fmax-fmin)
		out_array[out_array>=fmin]=fmin+(in_array[in_array>=fmin]-fmin)/ratio
		return out_array

	def fill_no_data(in_layer, no_data_value=None):
		"""
		Fils the missing data by interpolating from edges.
		:param in_layer: QgsRasterLayer
		:param no_data_value: NoDataValue of the input layer
		:return: Boolean
		"""
		#Get the input raster dataset
		rlayer=in_layer
		raster_ds = gdal.Open(rlayer.dataProvider().dataSourceUri(), gdalconst.GA_Update)
		in_band = raster_ds.GetRasterBand(1)
		in_array = in_band.ReadAsArray()

		if no_data_value == None:
			in_band.SetNoDataValue(np.nan)
		else:
			in_band.SetNoDataValue(no_data_value)

		if no_data_value != None:
			in_array[in_array == no_data_value] = np.nan

		#Define the parameters for creating a mask raster of valid values.
		path=os.path.split(rlayer.dataProvider().dataSourceUri())[0]
		mask_name="mask_"+os.path.split(rlayer.dataProvider().dataSourceUri())[1]
		mask_file=os.path.join(path,mask_name)
		geotransform = raster_ds.GetGeoTransform()
		cols = in_array.shape[1]
		rows = in_array.shape[0]

		out_array = np.ones(in_array.shape)

		out_array[np.isnan(in_array)] = np.nan
		out_array[np.isfinite(in_array)] = 1

		#Create Target - TIFF
		out_raster = gdal.GetDriverByName('GTiff').Create(mask_file, cols, rows, 1, gdal.GDT_Byte)
		out_raster.SetGeoTransform(geotransform)
		out_band = out_raster.GetRasterBand(1)
		out_band.SetNoDataValue(np.nan)
		out_band.WriteArray(out_array)

		result = gdal.FillNodata(targetBand = in_band, maskBand = out_band,
								 maxSearchDist = 100, smoothingIterations = 0)
		in_band.FlushCache()

		raster_ds = None
		out_raster = None
		return result

	def raster_smoothing(in_layer, factor):
		"""
		Smoothes values of pixels in a raster  by averaging  values around them
		:param in_layer: input raster layer for smoothing
		:return:Boolean
		"""

		rlayer = in_layer
		raster_ds = gdal.Open(rlayer.dataProvider().dataSourceUri(), gdalconst.GA_Update)
		in_band = raster_ds.GetRasterBand(1)
		in_array = in_band.ReadAsArray()
		rows=in_array.shape[0]
		cols=in_array.shape[1]

		out_array=np.zeros(in_array.shape)

		import time
		start=time.time()
		for i in range(rows):
			for j in range(cols):
				# Define smoothing mask; periodic boundary along date line
				x_vector = np.mod((np.arange((i - factor), (i + factor + 1))), (cols))
				x_vector = x_vector.reshape(1, len(x_vector))
				y_vector = np.arange(np.maximum(0, j - factor), (np.minimum((rows - 1), j + factor) + 1), 1)
				y_vector = y_vector.reshape(len(y_vector), 1)
				#out_array[i, i] = np.mean(in_array[y_vector, x_vector])
		end=time.time()
		print(end-start)

		in_band.WriteArray(out_array)
		in_band.FlushCache()
		return True