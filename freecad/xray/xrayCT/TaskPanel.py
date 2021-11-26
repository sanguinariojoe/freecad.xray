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
import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Units, ImageGui
import Part
from PySide import QtGui, QtCore
from qtrangeslider import QRangeSlider
from . import Tools, PlotAux
from .. import XRay_rc
from ..xrayUtils import Selection, LightUnits


# The suggested power, as a function of the light area
SPECIFIC_POWER = Units.parseQuantity('1000 W/m^2')


class TaskPanel:
    def __init__(self):
        self.name = "XRay tomography"
        self.ui = ":/ui/TaskPanel_xrayCT.ui"
        self.form = Gui.PySideUic.loadUi(self.ui)
        self.sino = None
        self.ct = None
        self.running = False
        self.plot = None

    def accept(self):
        if self.running:
            return False
        return True

    def reject(self):
        if self.running:
            self.onStop()
        return True

    def clicked(self, index):
        pass

    def open(self):
        pass

    def needsFullSpace(self):
        return True

    def isAllowedAlterSelection(self):
        return False

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterDocument(self):
        return False

    def helpRequested(self):
        pass

    def setupUi(self):
        self.form.angles = self.widget(QtGui.QSpinBox, "angles")
        self.form.max_error = self.widget(QtGui.QLineEdit, "max_error")
        self.form.power = self.widget(QtGui.QLineEdit, "power")
        self.form.use_gpu = self.widget(QtGui.QCheckBox, "use_gpu")
        self.form.run = self.widget(QtGui.QPushButton, "run")
        self.form.pbar = self.widget(QtGui.QProgressBar, "pbar")
        self.form.image_group = self.widget(QtGui.QGroupBox, "image_group")
        self.form.image = self.widget(QtGui.QComboBox, "image")
        self.form.slice = self.widget(QtGui.QSlider, "slice")
        self.form.cmap = self.widget(QtGui.QComboBox, "cmap")
        self.form.crange = QRangeSlider(QtCore.Qt.Horizontal,
                                        self.form.image_group)
        self.form.crange.setMaximum(1000)
        self.form.crange.setValue((0, 1000))
        self.form.image_group.layout().addWidget(
            self.form.crange, 5, 1)
        self.form.image_group.hide()

        if self.initValues():
            return True
        QtCore.QObject.connect(
            self.form.run,
            QtCore.SIGNAL("pressed()"),
            self.onStart)
        QtCore.QObject.connect(
            self.form.image,
            QtCore.SIGNAL("currentIndexChanged(int)"),
            self.onImage)
        QtCore.QObject.connect(
            self.form.slice,
            QtCore.SIGNAL("valueChanged(int)"),
            self.onSlice)
        QtCore.QObject.connect(
            self.form.cmap,
            QtCore.SIGNAL("currentIndexChanged(int)"),
            self.onImage)
        self.form.crange.valueChanged.connect(self.onCrange)

    def getMainWindow(self):
        toplevel = QtGui.QApplication.topLevelWidgets()
        for i in toplevel:
            if i.metaObject().className() == "Gui::MainWindow":
                return i
        raise RuntimeError("No main window found")

    def widget(self, class_id, name):
        """Return the selected widget.

        Keyword arguments:
        class_id -- Class identifier
        name -- Name of the widget
        """
        mw = self.getMainWindow()
        form = mw.findChild(QtGui.QWidget, "TaskPanel")
        return form.findChild(class_id, name)

    def initValues(self):
        xrays = Selection.get_xrays()
        if len(xrays) != 1:
            # This situation isalready covered in ../XRayGui.py
            return True
        self.xray = xrays[0]

        area = self.xray.ChamberRadius * self.xray.ChamberHeight
        power = SPECIFIC_POWER * area
        self.form.power.setText(power.UserString)
        return False

    def onStart(self):
        if self.running:
            self.onStop()
            return
        self.form.run.setText(QtGui.QApplication.translate(
            "XRay", "Stop", None))
        self.form.pbar.setValue(0)

        n_angles = self.form.angles.value()
        n_radon = self.xray.SensorResolutionY
        e = Units.parseQuantity(self.form.max_error.text())
        p = Units.parseQuantity(self.form.power.text())

        self.form.image.clear()
        # Get a first empty sinogram
        self.sino = np.zeros((n_angles,
                              self.xray.SensorResolutionX,
                              self.xray.SensorResolutionY), dtype=np.float)
        self.plot = PlotAux.Plot()
        # Plot the first image
        self.form.image.addItem(QtGui.QApplication.translate(
            "XRay", "Sinogram (X slices)", None))
        self.form.image.addItem(QtGui.QApplication.translate(
            "XRay", "Sinogram (Y slices)", None))
        self.form.image.addItem(QtGui.QApplication.translate(
            "XRay", "Sinogram (Z slices)", None))
        self.form.image.setCurrentIndex(0)
        self.form.image.show()

        self.running = True
        sinograms = Tools.sinogram(
            self.xray, n_angles, e, p, use_gpu=self.form.use_gpu.isChecked())
        for i, self.sino in enumerate(sinograms):
            self.update_plot()
            App.Console.PrintMessage("\t{} / {}\n".format(i + 1, n_angles))
            self.form.pbar.setValue(100 * (i + 1) / n_angles)
            if not self.running:
                break

        if not self.running:
            return False

        # Get a first empty tomography and plot it
        self.ct = np.zeros((self.xray.SensorResolutionX,
                            self.xray.SensorResolutionX,
                            self.xray.SensorResolutionY), dtype=np.float)
        self.form.image.addItem(QtGui.QApplication.translate(
            "XRay", "Tomography (X slices)", None))
        self.form.image.addItem(QtGui.QApplication.translate(
            "XRay", "Tomography (Y slices)", None))
        self.form.image.addItem(QtGui.QApplication.translate(
            "XRay", "Tomography (Z slices)", None))
        self.form.image.setCurrentIndex(5)

        for i, self.ct in enumerate(Tools.tomography(self.xray, self.sino)):
            self.update_plot()
            App.Console.PrintMessage("\t{} / {}\n".format(i + 1, n_radon))
            self.form.pbar.setValue(100 * (i + 1) / n_radon)
            if not self.running:
                break

        if not self.running:
            return False

        return True

    def onStop(self):
        if not self.running:
            return
        self.form.run.setText(QtGui.QApplication.translate(
            "XRay", "Start", None))
        Tools.stop()
        self.running = False

    def onImage(self, i):
        # Set the slice slider maximum value
        f = self.form.slice.value() /  self.form.slice.maximum()
        if i < 3:
            # Sinogram image
            max_val = self.sino.shape[i] - 1
        else:
            # tomography
            max_val = self.ct.shape[i - 3] - 1
        self.form.slice.setMaximum(max_val)
        self.form.slice.setValue(int(f * max_val))
        self.update_plot()

    def onSlice(self, i):
        self.update_plot()

    def onCrange(self, values):
        self.update_plot()

    def update_plot(self):
        if not self.plot:
            self.form.image_group.hide()
            return
        self.form.image_group.show()

        aspect_real = (self.xray.ChamberHeight / self.xray.ChamberRadius).Value
        aspect_num = self.xray.SensorResolutionY / self.xray.SensorResolutionX
        aspect = aspect_real / aspect_num
        if self.form.image.currentIndex() < 3:
            i = self.form.image.currentIndex()
            img = self.sino
            if i != 0:
                aspect = 'auto'
        else:
            i = self.form.image.currentIndex() - 3
            img = self.ct
            if i != 2:
                aspect = 'auto'
        cmap = self.form.cmap.currentIndex()
        vmin, vmax = self.form.crange.value()
        vmin = vmin / 1000 * np.max(img)
        vmax = vmax / 1000 * np.max(img)
        slicer = [np.s_[:], np.s_[:], np.s_[:]]
        slicer[i] = self.form.slice.value()
        slicer = tuple(slicer)
        img = np.transpose(img[slicer])
        self.plot.update(
            img, cmap_index=cmap, vmin=vmin, vmax=vmax, aspect=aspect)


def createTask():
    panel = TaskPanel()
    Gui.Control.showDialog(panel)
    if panel.setupUi():
        Gui.Control.closeDialog()
        return None
    return panel
