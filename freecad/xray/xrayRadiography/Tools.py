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
import trimesh
import FreeCAD as App
from FreeCAD import Units, Vector, Mesh
import Part
from ..xrayUtils import LuxCore, LightUnits


LIGHT_PLY = "light.ply"
SCREEN_PLY = "screen.ply"
SCALE = 'm'
CAM_TYPE = "orthographic"  # "perspective"
MIN_INTENSITY_RATIO = 1E-6


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
    return Units.Quantity(value, Units.Length).getValueAs(SCALE).Value


def __make_ply(obj, fname):
    Mesh.export([obj], fname)
    # FreeCAD exported the object in its native length units, so we must scale
    # it to meters
    factor = __freecad2meters(1.0)
    mesh = trimesh.load(fname, force='mesh')
    mesh.apply_transform(trimesh.transformations.scale_matrix(factor))
    # The exported ply objects might have duplicated vertices and faces
    mesh.process()
    mesh.process()
    # trimesh is printing the file to the stdout!?!?!
    stdout = sys.stdout
    sys.stdout = open(os.path.join(os.path.dirname(fname), 'trimesh.log'), 'w')
    mesh.export(fname, file_type='ply')
    sys.stdout.close()
    sys.stdout = stdout
    return Units.parseQuantity('{} m^2'.format(mesh.area))


def __shape2ply(shape, fname):
    # FreeCAD will export the object in its native length units, so we must
    # scale it to meters
    Part.show(shape)
    App.ActiveDocument.recompute()
    obj = App.ActiveDocument.Objects[-1]
    area = __make_ply(obj, fname)
    App.ActiveDocument.removeObject(obj.Name)
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
    yp = [att.getValueAs(SCALE + '^-1').Value for att in mu]
    # Interpolate and integrate
    y = np.interp(x, xp, yp)
    return np.trapz(y, x=x) / (max_x - min_x)


def radiography(xray, angle, max_error, power,
                tmppath=None, background=True, use_gpu=False):
    # Create a temporal folder
    tmppath = tmppath or tempfile.mkdtemp()
    print(tmppath)

    # Setup the light and the screen meshes
    light = xray.Proxy.light(xray)
    light = light.rotate((0, 0, 0), (0, 0, 1), angle)
    light_area = __shape2ply(light, os.path.join(tmppath, LIGHT_PLY))
    cam_dist = 0.5 * xray.ChamberDistance
    screen = xray.Proxy.screen(xray)
    # screen = screen.translate((cam_dist, 0, 0))
    screen = screen.rotate((0, 0, 0), (0, 0, 1), angle)
    __shape2ply(screen, os.path.join(tmppath, SCREEN_PLY))

    # Get the camera position and target
    # cam_pos = Vector(0.5 * xray.ChamberDistance, 0, 0)
    # cam_target = cam_pos + Vector(cam_dist, 0, 0)
    cam_target = Vector(0.5 * xray.ChamberDistance, 0, 0)
    cam_pos = cam_target + Vector(cam_dist, 0, 0)
    cam_pos = Part.Vertex(cam_pos).rotate((0, 0, 0), (0, 0, 1), angle)
    cam_target = Part.Vertex(cam_target).rotate((0, 0, 0), (0, 0, 1), angle)
    cam_near = 0.001 * Units.parseQuantity('1 {}'.format(SCALE))
    if cam_near > 0.5 * cam_dist:
        cam_near = 0.5 * cam_dist
    if CAM_TYPE == "perspective":
        cam_w = 2
        cam_h = 2
        ratio = cam_dist / (0.5 * xray.ChamberRadius.getValueAs(SCALE))
        field_of_view = np.degrees(np.arctan(ratio.Value))
    else:
        cam_w = 0.5 * xray.ChamberRadius.getValueAs(SCALE).Value
        cam_h = 0.5 * xray.ChamberHeight.getValueAs(SCALE).Value
        field_of_view = 45.0

    # Since the light is actually bigger than intended, we need to scale the
    # power.
    power *= light_area / (xray.ChamberRadius * xray.ChamberHeight)
    # We have also to consider the exporting scale
    l_factor = (Units.parseQuantity('1 {}'.format(SCALE)) / Units.Metre).Value
    power *= l_factor * l_factor
    power = power.getValueAs('W').Value

    # Setup the templates for the background/empty image
    max_error = max(max_error.Value, 0) * power
    replaces = {
        "@WIDTH_OUTPUT@": "{}".format(xray.SensorResolutionX),
        "@HEIGHT_OUTPUT@": "{}".format(xray.SensorResolutionY),
        "@MAX_ERROR@": "{}".format(max_error),
    }
    template_file = "render_gpu.cfg" if use_gpu else "render.cfg"
    with open(os.path.join(tmppath, "render.cfg"), 'w') as f:
        f.write(__make_template(template_file, replaces))

    replaces = {
        "@CAM_NEAR@": "{}".format(cam_near.getValueAs(SCALE).Value),
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
        "@CAM_TYPE@": "{}".format(CAM_TYPE),
        "@FIELD_OF_VIEW@": "{}".format(field_of_view),
        "@POWER@" : "{}".format(power),
        "@COLLIMATION@" : "{}".format(
            xray.EmitterCollimation.getValueAs('deg').Value),
        "@AREA_LIGHT_PLY@" : LIGHT_PLY,
        "@SCREEN_PLY@" : SCREEN_PLY,
    }
    scn = __make_template("scene.scn", replaces)
    with open(os.path.join(tmppath, "scene.scn"), 'w') as f:
        f.write(scn)

    if background:
        # We are ready for the background simulation!
        yield tmppath, LuxCore.run_sim(tmppath, scn="scene.scn")

    # Now we should add a scene per tuple of sampled frequencies (in groups of
    # 3). We can start exporting the objects
    objs = xray.ScanObjects
    for i, obj in enumerate(objs):
        fname = os.path.join(tmppath, "mesh.{:05d}.ply".format(i))
        if os.path.isfile(fname):
            continue
        __make_ply(obj.Source, fname)

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


def __discretize_spectrum(xray):
    n = xray.EmitterSamples
    if n % 3:
        n = 3 * (n // 3 + 1)

    # 25 points per spectrum chunck
    n_per_sample = 25
    x = np.linspace(0.0, 1.0, num = n * n_per_sample)
    xp = np.linspace(0.0, 1.0, num=len(xray.EmitterSpectrum))
    yp = xray.EmitterSpectrum[:]
    y = np.interp(x, xp, yp)

    weights = []
    # Average the spectrum by pieces
    for i in range(n):
        i0 = i * n_per_sample
        i1 = (i + 1) * n_per_sample
        weights.append(
            np.trapz(y[i0:i1], x=x[i0:i1]) / (x[i1 - 1] - x[i0]))

    return weights


def assemble_radiography(xray, images):
    imgs = [img / images[0] for img in images[1:]]
    weights = __discretize_spectrum(xray)

    W = 0
    res = np.zeros(images[0].shape, dtype=images[0].dtype)
    for w, img in zip(weights, imgs):
        W += w
        res = res + img * w
    res = res / W

    res[res < MIN_INTENSITY_RATIO] = MIN_INTENSITY_RATIO
    return -np.log(res) 
