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


import time
import numpy as np
from skimage.transform import radon, iradon
import FreeCAD as App
from FreeCAD import Units, Vector, Mesh
from PySide import QtGui, QtCore
import Part
from ..xrayUtils import LuxCore, LightUnits
from ..xrayRadiography import Tools as Radiography


RUNNING = None


def __angles(n):
    angles = np.linspace(0, 180.0, num=n, endpoint=False)
    angles += 0.5 * (angles[1] - angles[0])
    return angles


def sinogram(xray, n, e):
    global RUNNING
    RUNNING = True

    # Make FreeCAD responsive
    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    QtCore.QObject.connect(timer,
                           QtCore.SIGNAL("timeout()"),
                           loop,
                           QtCore.SLOT("quit()"))

    # Setup the sinogram image
    angles = __angles(n)
    sino = np.zeros((n, xray.SensorResolutionX, xray.SensorResolutionY),
                    dtype=np.float)

    folder = None
    bkg = None
    for i, angle in enumerate(angles):
        a = angle * Units.Degree
        samples = []
        if bkg is not None:
            samples.append(bkg)
        sessions = Radiography.radiography(
            xray, a, e, tmppath=folder, background=bkg is None)
        for folder, session in sessions:
            while not session.HasDone():
                if not RUNNING:
                    session.Stop()
                    raise StopIteration
                session.UpdateStats()
                stats = session.GetStats()
                step = stats.Get("stats.renderengine.pass").GetInt()
                conv = stats.Get("stats.renderengine.convergence").GetFloat()
                App.Console.PrintMessage("\t\t{} {:.1f}%\n".format(
                    step, 100 * conv))
                timer.start(0.0)
                loop.exec_()
                time.sleep(1.0)
            session.Stop()
            imgs = Radiography.get_imgs(folder, session)
            if bkg is None:
                # Keep just one background image channel
                bkg = imgs[0]
                imgs = [bkg]
            samples = samples + imgs

        # Assemble the final radiography
        img = Radiography.assemble_radiography(xray, samples)
        sino[i, :, :] = np.transpose(img[:, :])
        yield sino


def tomography(xray, sino):
    global RUNNING
    RUNNING = True

    # Make FreeCAD responsive
    loop = QtCore.QEventLoop()
    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    QtCore.QObject.connect(timer,
                           QtCore.SIGNAL("timeout()"),
                           loop,
                           QtCore.SLOT("quit()"))

    # Setup the sinogram image
    angles = __angles(sino.shape[0])
    w = xray.SensorResolutionX
    h = xray.SensorResolutionY
    dcm = np.zeros((w, w, h), dtype=np.float)

    for z in range(h):
        if not RUNNING:
            raise StopIteration
        img = iradon(np.transpose(sino[:, :, z]), theta=angles, circle=True)
        dcm[:, :, z] = img
        timer.start(0.0)
        loop.exec_()
        yield dcm


def stop():
    global RUNNING
    RUNNING = False
