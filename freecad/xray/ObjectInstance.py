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

import time
import math
from PySide import QtGui, QtCore
import FreeCAD
import FreeCADGui
from FreeCAD import Base, Vector, Units
import Part
from .xrayUtils import LightUnits


def add_xray_obj_props(obj):
    """This function adds the properties to a ship instance, in case they are
    not already created

    Position arguments:
    obj -- Part::FeaturePython object

    Returns:
    The same input object, that now has the properties added
    """
    try:
        obj.getPropertyByName('IsXRayObject')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "True if it is a valid X-Ray instance, False otherwise",
            None)
        obj.addProperty("App::PropertyBool",
                        "IsXRayObject",
                        "XRay",
                        tooltip).IsXRayObject = False

    # Emitter options
    try:
        obj.getPropertyByName('Source')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "The object",
            None)
        obj.addProperty("App::App::PropertyLink",
                        "Source",
                        "XRay",
                        tooltip)

    return obj


class XRayObj:
    def __init__(self, obj, source):
        """Create an object to be considered in the scan

        Keyword arguments:
        obj -- Part::FeaturePython created object which should be transformed
               in a scanned object instance.
        source -- The object to be linked
        """
        add_xray_obj_props(obj)
        obj.Source = source
        obj.Shape = None
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Detects the ship data changes.

        Keyword arguments:
        fp -- Part::FeaturePython object affected.
        prop -- Modified property name.
        """
        pass

    def execute(self, fp):
        """Detects the entity recomputations.

        Keyword arguments:
        fp -- Part::FeaturePython object affected.
        """
        pass


class ViewProviderXRayObj:
    def __init__(self, obj):
        """Add this view provider to the selected object.

        Keyword arguments:
        obj -- Object which must be modified.
        """
        obj.Proxy = self

    def attach(self, obj):
        """Setup the scene sub-graph of the view provider, this method is
        mandatory.
        """
        return

    def updateData(self, fp, prop):
        """If a property of the handled feature has changed we have the chance
        to handle this here.

        Keyword arguments:
        fp -- Part::FeaturePython object affected.
        prop -- Modified property name.
        """
        return

    def getDisplayModes(self, obj):
        """Return a list of display modes.

        Keyword arguments:
        obj -- Object associated with the view provider.
        """
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode. It must be defined in
        getDisplayModes."""
        return "Shaded"

    def setDisplayMode(self, mode):
        """Map the display mode defined in attach with those defined in
        getDisplayModes. Since they have the same names nothing needs to be
        done. This method is optional.

        Keyword arguments:
        mode -- Mode to be activated.
        """
        return mode

    def onChanged(self, vp, prop):
        """Detects the ship view provider data changes.

        Keyword arguments:
        vp -- View provider object affected.
        prop -- Modified property name.
        """
        pass

    def __getstate__(self):
        """When saving the document this object gets stored using Python's
        cPickle module. Since we have some un-pickable here (the Coin stuff)
        we must define this method to return a tuple of all pickable objects
        or None.
        """
        return None

    def __setstate__(self, state):
        """When restoring the pickled object from document we have the chance
        to set some internals here. Since no data were pickled nothing needs
        to be done here.
        """
        return None

    def claimChildren(self):
        objs = []
        return objs

    def getIcon(self):
        """Returns the icon for this kind of objects."""
        return ":/icons/XRay_Object.svg"
