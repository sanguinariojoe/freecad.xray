#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2011, 2016 Jose Luis Cercos Pita <jlcercos@gmail.com>   *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import PySide
from PySide import QtCore, QtGui
import FreeCAD
import FreeCADGui
import os
from . import XRay_rc
from .xrayUtils import Selection

FreeCADGui.addLanguagePath(":/XRay/translations")
FreeCADGui.addIconPath(":/XRay/icons")


class Create:
    def IsActive(self):
        return True

    def Activated(self):
        from . import xrayCreate
        xrayCreate.load()

    def GetResources(self):
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'XRay_Create',
            'Create a new X-Ray machine')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'XRay_Create',
            'Create a new X-Ray simulator, composed by the lamp, the lens ' +\
            '(if required) and the sensor')
        return {'Pixmap': 'XRay_Workbench',
                'MenuText': MenuText,
                'ToolTip': ToolTip}


class AddObject:
    def IsActive(self):
        objs = FreeCAD.ActiveDocument.Objects
        return bool(Selection.get_solids()) and bool(Selection.get_xrays(objs))

    def Activated(self):
        from . import xrayAddObject
        xrayAddObject.load()

    def GetResources(self):
        MenuText = QtCore.QT_TRANSLATE_NOOP(
            'XRay_AddObject',
            'Add an object to the scan')
        ToolTip = QtCore.QT_TRANSLATE_NOOP(
            'XRay_AddObject',
            'Add an object to the scan, setting its physical properties')
        return {'Pixmap': 'XRay_ObjectAdd',
                'MenuText': MenuText,
                'ToolTip': ToolTip}


FreeCADGui.addCommand('XRay_Create', Create())
FreeCADGui.addCommand('XRay_AddObject', AddObject())
