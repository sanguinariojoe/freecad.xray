#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2021 Jose Luis Cercos Pita <jlcercos@gmail.com>         *
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


import os
import sys
import tempfile
import numpy as np
from PIL import Image
import FreeCAD as App
from FreeCAD import Units, Vector, Mesh
import Part
from ..xrayUtils import LuxCore, LightUnits


LIGHT_PLY = "light.ply"
SCREEN_PLY = "screen.ply"
SPECIFIC_POWER = 10
SCALE = 'mm'


def luxcore_templates_folder():
    _dir = os.path.dirname(__file__)
    return os.path.join(_dir, "..", "resources", "luxcore")


def __make_template(fname, replaces):
    txt = None
    with open(os.path.join(luxcore_templates_folder(), fname), 'r') as f:
        txt = f.read()
        for key, value in replaces.items():
            txt = txt.replace(key, value)
    return txt


def __freecad2meters(value):
    return App.Units.Quantity(value, App.Units.Length).getValueAs(SCALE).Value


def __shape2ply(shape, fname):
    # FreeCAD will export the object in its native length units, so we must
    # scale it to meters
    factor = __freecad2meters(1.0)
    shape = shape.scale(factor)
    area = shape.Area
    Part.show(shape)
    App.ActiveDocument.recompute()
    obj = App.ActiveDocument.Objects[-1]
    Mesh.export([obj], fname)
    App.ActiveDocument.removeObject(obj.Name)
    # Apparently luxcore does not likes the vertex_index keyword
    with open(fname, 'rb') as f:
        ply = f.read()
    header_orig = ply.decode('utf8', errors='ignore')
    header_orig = header_orig[:header_orig.find("end_header")]
    header_dst = header_orig.replace("vertex_index", "vertex_indices")
    l = len(header_orig.encode('utf8'))
    ply = header_dst.encode('utf8') + ply[l:]
    with open(fname, 'wb') as f:
        f.write(ply)
    return area


def __average_mu(obj, min_e, max_e, num=25):
    min_e = LightUnits.to_energy(min_e)
    max_e = LightUnits.to_energy(max_e)
    e = []
    for freq in obj.AttenuationFreqs:
        e.append(
            LightUnits.to_energy(Units.parseQuantity('{} THz'.format(freq))))
    mu = []
    for att in obj.AttenuationValues:
        mu.append(
            Units.parseQuantity('{} m^-1'.format(att)))
    # Convert everything to floats
    min_x = min_e.getValueAs('keV').Value
    max_x = max_e.getValueAs('keV').Value
    x = np.linspace(min_x, max_x, num=num)
    xp = [ee.getValueAs('keV').Value for ee in e]
    yp = [att.getValueAs(SCALE + '^-1').Value / 1000 for att in mu]
    # Interpolate and integrate
    y = np.interp(x, xp, yp)
    return np.trapz(y, x=x) / (max_x - min_x)


def radiography(xray, angle, max_error):
    # Create a temporal folder
    tmppath = tempfile.mkdtemp()
    print(tmppath)

    # Setup the light and the screen meshes
    light = xray.Proxy.light(xray)
    light = light.rotate((0, 0, 0), (0, 0, 1), angle)
    light_area = __shape2ply(light, os.path.join(tmppath, LIGHT_PLY))
    cam_dist = 0.01 * xray.ChamberDistance
    screen = xray.Proxy.screen(xray)
    screen = screen.translate((cam_dist, 0, 0))
    screen = screen.rotate((0, 0, 0), (0, 0, 1), angle)
    __shape2ply(screen, os.path.join(tmppath, SCREEN_PLY))

    # Get the camera position and target
    cam_pos = Vector(0.5 * xray.ChamberDistance, 0, 0)
    cam_target = cam_pos + Vector(cam_dist, 0, 0)
    cam_pos = Part.Vertex(cam_pos).rotate((0, 0, 0), (0, 0, 1), angle)
    cam_target = Part.Vertex(cam_target).rotate((0, 0, 0), (0, 0, 1), angle)
    cam_w = 0.5 * xray.ChamberRadius.getValueAs(SCALE).Value
    cam_h = 0.5 * xray.ChamberHeight.getValueAs(SCALE).Value

    # Setup the templates for the background/empty image
    max_error = min(max(max_error.Value, 0), 1)
    replaces = {
        "@WIDTH_OUTPUT@": "{}".format(xray.SensorResolutionX),
        "@HEIGHT_OUTPUT@": "{}".format(xray.SensorResolutionY),
        "@MAX_ERROR@": "{}".format(max_error),
    }
    with open(os.path.join(tmppath, "render.cfg"), 'w') as f:
        f.write(__make_template("render.cfg", replaces))

    replaces = {
        "@CAM_NEAR@": "{}".format(0.75 * cam_dist.getValueAs(SCALE).Value),
        "@CAM_FAR@": "{}".format(1.5 * cam_dist.getValueAs(SCALE).Value),
        "@CAM_POS@": "{} {} {}".format(__freecad2meters(cam_pos.X),
                                       __freecad2meters(cam_pos.Y),
                                       __freecad2meters(cam_pos.Z)),
        "@CAM_TARGET@": "{} {} {}".format(__freecad2meters(cam_target.X),
                                          __freecad2meters(cam_target.Y),
                                          __freecad2meters(cam_target.Z)),
        "@SCREEN_BOUNDS@": "{} {} {} {}".format(-0.5 * cam_w,
                                                0.5 * cam_w,
                                                -0.5 * cam_h,
                                                0.5 * cam_h),
        "@POWER@" : "{}".format(
            SPECIFIC_POWER * light_area),
        "@COLLIMATION@" : "{}".format(
            xray.EmitterCollimation.getValueAs('deg').Value),
        "@AREA_LIGHT_PLY@" : LIGHT_PLY,
        "@SCREEN_PLY@" : SCREEN_PLY,
    }
    scn = __make_template("scene.scn", replaces)
    with open(os.path.join(tmppath, "scene.scn"), 'w') as f:
        f.write(scn)

    # We are ready for the background simulation!
    yield tmppath, LuxCore.run_sim(tmppath, scn="scene.scn")

    # Now we should add a scene per tuple of sampled frequencies (in groups of
    # 3). We can start exporting the objects
    objs = xray.ScanObjects
    for i, obj in enumerate(objs):
        # BUG: We should check if it is a mesh
        __shape2ply(obj.Source.Shape.copy(), "mesh.{:05d}.ply".format(i))

    # And now we can traverse the groups of samples
    n_samples = xray.EmitterSamples
    if n_samples % 3:
        n_samples = 3 * (n_samples // 3 + 1)
    e0 = LightUnits.to_energy(xray.EmitterMinFreq)
    e1 = LightUnits.to_energy(xray.EmitterMaxFreq)
    de = (e1 - e0) / (n_samples + 1)
    n_samples //= 3
    scn_org = scn
    for i in range(n_samples):
        scn = scn_org
        for j, obj in enumerate(objs):
            # Compute the absortions
            mu = []
            for k in range(3):
                kk = i * 3 + k
                e_min = e0 + kk * de
                e_max = e0 + (kk + 1) * de
                mu.append(__average_mu(obj, e_min, e_max))
            replaces = {
                "@VOL_ID@": "{}".format(1000000 + j),
                "@MAT_ID@": "{}".format(2000000 + j),
                "@OBJ_ID@": "{}".format(3000000 + j),
                "@ATTENUATION@": "{} {} {}".format(mu[0],
                                                   mu[1],
                                                   mu[2]),
                "@OBJ_PLY@": "mesh.{:05d}.ply".format(j),
            }
            scn = scn + __make_template("object.scn", replaces)
        scn_name = "sample.{}.scn".format(i)
        with open(os.path.join(tmppath, scn_name), 'w') as f:
            f.write(scn)

        # We are ready for the background simulation!
        yield tmppath, LuxCore.run_sim(tmppath, scn=scn_name)

    
def get_imgs(folder, session=None):
    if session is None:
        return LuxCore.get_imgs(folder)
    return LuxCore.get_imgs(folder, session)
