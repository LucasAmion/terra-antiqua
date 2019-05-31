# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DEMBuilder
                                 A QGIS plugin
 The plugin creates a paleoDEM by combyning present day topography and paleobathimetry, and modiying the final topography by introducing masks.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-03-18
        copyright            : (C) 2019 by Jovid Aminov
        email                : jovid.aminov@outlook.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load DEMBuilder class from file DEMBuilder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .dem_builder import DEMBuilder
    return DEMBuilder(iface)
