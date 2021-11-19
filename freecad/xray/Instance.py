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


EMITTER_TYPES = ['Parallel', 'Helical', 'Cone']


def add_xray_props(obj):
    """This function adds the properties to a ship instance, in case they are
    not already created

    Position arguments:
    obj -- Part::FeaturePython object

    Returns:
    The same input object, that now has the properties added
    """
    try:
        obj.getPropertyByName('IsXRay')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "True if it is a valid X-Ray instance, False otherwise",
            None)
        obj.addProperty("App::PropertyBool",
                        "IsXRay",
                        "XRay",
                        tooltip).IsXRay = False

    # Emitter options
    try:
        obj.getPropertyByName('EmitterMinFreq')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "Minimum emitter frequency",
            None)
        obj.addProperty("App::PropertyFrequency",
                        "EmitterMinFreq",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('EmitterMaxFreq')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "Maximum emitter frequency",
            None)
        obj.addProperty("App::PropertyFrequency",
                        "EmitterMaxFreq",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('EmitterSpectrum')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "Spectrum values",
            None)
        obj.addProperty("App::PropertyFloatList",
                        "EmitterSpectrum",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('EmitterSamples')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "Number of frequency samples to take",
            None)
        obj.addProperty("App::PropertyInteger",
                        "EmitterSamples",
                        "XRay",
                        tooltip).EmitterSamples = 3
    try:
        obj.getPropertyByName('EmitterType')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "The type of emitter",
            None)
        obj.addProperty("App::PropertyString",
                        "EmitterType",
                        "XRay",
                        tooltip).EmitterType = EMITTER_TYPES[0]
    try:
        obj.getPropertyByName('EmitterCollimation')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "X-Rays spread angle",
            None)
        obj.addProperty("App::PropertyAngle",
                        "EmitterCollimation",
                        "XRay",
                        tooltip).EmitterCollimation = Units.parseQuantity('1 deg')

    try:
        obj.getPropertyByName('ChamberRadius')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "The radius of the scanner chamber",
            None)
        obj.addProperty("App::PropertyLength",
                        "ChamberRadius",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('ChamberHeight')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "The height of the scanner chamber",
            None)
        obj.addProperty("App::PropertyLength",
                        "ChamberHeight",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('ChamberDistance')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "The distance between the sensor and the emitter",
            None)
        obj.addProperty("App::PropertyLength",
                        "ChamberDistance",
                        "XRay",
                        tooltip)

    try:
        obj.getPropertyByName('SensorResolutionX')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "Number of samples took in the horizontal direction",
            None)
        obj.addProperty("App::PropertyInteger",
                        "SensorResolutionX",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('SensorResolutionY')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "Number of samples took in the vertical direction",
            None)
        obj.addProperty("App::PropertyInteger",
                        "SensorResolutionY",
                        "XRay",
                        tooltip)
    try:
        obj.getPropertyByName('ScanObjects')
    except AttributeError:
        tooltip = QtGui.QApplication.translate(
            "XRay",
            "List of objects to scan",
            None)
        obj.addProperty("App::PropertyLinkList",
                        "ScanObjects",
                        "XRay",
                        tooltip)

    return obj


class XRay:
    def __init__(self, obj, min_energy, max_energy, spectrum, samples,
                 emitter_type, collimation, radius, height, distance,
                 res_x, res_y):
        """Create a X-Ray machine instance.

        Keyword arguments:
        obj -- Part::FeaturePython created object which should be transformed
        in a X-Ray machine instance.
        min_energy -- Minimum considered energy in the spectrum
        max_energy -- Maximum considered energy in the spectrum
        spectrum -- Renormalize light intensity spectrum
        samples -- Number of samples to take between min_energy and max_energy
        emitter_type -- 0 for parallel beam, 1 for hellical fan, 2 for cone beam
        collimation -- The spread angle of the X-Rays
        radius -- Radius of the scanning chamber
        height -- Height of the scanning chamber
        distance -- Distance between the light emitter and the detector
        res_x -- Horizontal detector resolution
        res_y -- Vertical detector resolution
        """
        add_xray_props(obj)
        obj.EmitterMinFreq = LightUnits.to_frequency(min_energy)
        obj.EmitterMaxFreq = LightUnits.to_frequency(max_energy)
        obj.EmitterSpectrum = spectrum
        obj.EmitterSamples = samples
        obj.EmitterType = EMITTER_TYPES[emitter_type]
        obj.EmitterCollimation = collimation
        obj.ChamberRadius = radius
        obj.ChamberHeight = height
        obj.ChamberDistance = distance
        obj.SensorResolutionX = res_x
        obj.SensorResolutionY = res_y
        obj.Shape = Part.Vertex(0, 0, 0)  # self.regen_geom(obj)
        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Detects the ship data changes.

        Keyword arguments:
        fp -- Part::FeaturePython object affected.
        prop -- Modified property name.
        """
        geom_changers = ["EmitterType", "ChamberRadius", "ChamberHeight",
                         "ChamberDistance", "IsXRay"]
        if prop in geom_changers and fp.IsXRay:
            fp.Shape = self.regen_geom(fp)

    def execute(self, fp):
        """Detects the entity recomputations.

        Keyword arguments:
        fp -- Part::FeaturePython object affected.
        """
        pass

    def regen_geom(self, fp):
        light = self.light(fp)
        screen = self.screen(fp)
        return Part.makeCompound([light, screen])

    def __min_dims(self, fp, grow_factor=1.05):
        l = fp.ChamberRadius
        h = fp.ChamberHeight
        spread = math.tan(fp.EmitterCollimation.getValueAs('rad').Value)
        d = fp.ChamberDistance * spread
        return grow_factor * (l + d), grow_factor * (h + d)

    def light(self, fp):
        radius, height = self.__min_dims(fp)
        if fp.EmitterType == 'Parallel':
            l = Part.makePlane(
                height, radius,
                Vector(-0.5 * height, -0.5 * radius, 0))
            l = l.rotate((0, 0, 0), (0, 1, 0), Units.parseQuantity('90 deg'))
            FreeCAD.ActiveDocument.recompute()
        elif fp.EmitterType == 'Helical':
            angle = math.atan((radius / fp.ChamberDistance).Value)
            s = Part.makeCylinder(
                0.01 * fp.ChamberDistance, height,
                Vector(0, 0, 0), Vector(0, 0, 1),
                angle * Units.Radian)
            s = s.translate((0, 0, -0.5 * height))
            # We just want the cylindrical face
            for f in s.Faces:
                if f.Surface.TypeId == 'Part::GeomCylinder':
                    l = f
                    break
        elif fp.EmitterType == 'Cone':
            radius = math.sqrt(
                radius.Value**2 + height.Value**2)
            angle = math.atan(radius / fp.ChamberDistance.Value)
            s = Part.makeSphere(
                0.01 * fp.ChamberDistance,
                Vector(0,0,0), Vector(1, 0, 0),
                0,
                Units.parseQuantity('90 deg'),
                Units.parseQuantity('360 deg'))
            Part.show(s)
            s = FreeCAD.ActiveDocument.Objects[-1]
            s2 = Part.makeSphere(
                0.01 * fp.ChamberDistance,
                Vector(0,0,0), Vector(1, 0, 0),
                0,
                Units.parseQuantity('90 deg') - angle * Units.Radian,
                Units.parseQuantity('360 deg'))
            Part.show(s2)
            s2 = FreeCAD.ActiveDocument.Objects[-1]
            FreeCAD.ActiveDocument.recompute()
            cut = FreeCAD.ActiveDocument.addObject("Part::Cut", "CutHelper")
            cut.Base = s
            cut.Tool = s2
            FreeCAD.ActiveDocument.recompute()
            # We just want the spherical face
            for f in cut.Shape.Faces:
                if f.Surface.TypeId == 'Part::GeomSphere':
                    l = f.copy()
                    break
            FreeCAD.ActiveDocument.removeObject(cut.Name)
            FreeCAD.ActiveDocument.removeObject(s.Name)
            FreeCAD.ActiveDocument.removeObject(s2.Name)
            FreeCAD.ActiveDocument.recompute()
        else:
            raise ValueError('Unknown emitter type "{}"'.format(fp.EmitterType))

        l = l.translate((-0.5 * fp.ChamberDistance, 0, 0))

        return l

    def screen(self, fp):
        radius, height = self.__min_dims(fp)
        s = Part.makePlane(
            height, radius,
            Vector(-0.5 * height, -0.5 * radius, 0))
        s = s.rotate((0, 0, 0), (0, 1, 0), -Units.parseQuantity('90 deg'))
        s = s.translate((0.5 * fp.ChamberDistance, 0, 0))
        FreeCAD.ActiveDocument.recompute()

        return s


class ViewProviderXRay:
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
        # Locate the owner object
        doc_objs = FreeCAD.ActiveDocument.Objects
        obj = None
        for doc_obj in doc_objs:
            try:
                v_provider = doc_obj.ViewObject.Proxy
                if v_provider == self:
                    obj = doc_obj
            except:
                continue
        if obj is None:
            FreeCAD.Console.PrintError("Orphan view provider found...\n")
            FreeCAD.Console.PrintError(self)
            FreeCAD.Console.PrintError('\n')
            return []

        # Check everything is all right
        add_xray_props(obj)

        return obj.ScanObjects

    def getIcon(self):
        """Returns the icon for this kind of objects."""
        return ":/icons/XRay_Workbench.svg"
