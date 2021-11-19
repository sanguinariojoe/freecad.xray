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
import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Units
import Part
from PySide import QtGui, QtCore
from . import Tools, PlotAux
from .. import XRay_rc
from ..xrayUtils import Selection, LightUnits


class TaskPanel:
    def __init__(self):
        self.name = "XRay radiography"
        self.ui = ":/ui/TaskPanel_xrayRadiography.ui"
        self.form = Gui.PySideUic.loadUi(self.ui)
        self.luxcore = None
        self.plot = None

    def accept(self):
        if self.luxcore:
            self.onStop()
            return False
        return True

    def reject(self):
        if self.luxcore:
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
        self.form.angle = self.widget(QtGui.QLineEdit, "angle")
        self.form.max_error = self.widget(QtGui.QLineEdit, "max_error")
        self.form.run = self.widget(QtGui.QPushButton, "run")
        self.form.pbar = self.widget(QtGui.QProgressBar, "pbar")
        self.form.image = self.widget(QtGui.QComboBox, "image")

        if self.initValues():
            return True
        QtCore.QObject.connect(
            self.form.run,
            QtCore.SIGNAL("pressed()"),
            self.onStart)

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
        return False

    def onStart(self):
        if self.luxcore:
            self.onStop()
            return
        self.form.run.setText(QtGui.QApplication.translate(
            "XRay", "Stop", None))
        self.form.pbar.setValue(0)

        # Get the number of images/LuxCore sessions
        n = self.xray.EmitterSamples
        if n % 3:
            n = 3 * (n_samples // 3 + 1)
        n //= 3
        self.titles = ["Background"]
        e0 = LightUnits.to_energy(self.xray.EmitterMinFreq)
        e1 = LightUnits.to_energy(self.xray.EmitterMaxFreq)
        de = (e1 - e0) / (n + 1)
        for i in range(n):
            e = e0 + (i + 0.5) * de
            self.titles.append(e.UserString)
        n += 1  # The background image

        # Make FreeCAD responsive
        self.loop = QtCore.QEventLoop()
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        QtCore.QObject.connect(self.timer,
                               QtCore.SIGNAL("timeout()"),
                               self.loop,
                               QtCore.SLOT("quit()"))
        a = Units.parseQuantity(self.form.angle.text())
        e = Units.parseQuantity(self.form.max_error.text())
        self.images = []
        self.plot = PlotAux.Plot(self.xray)
        current_image = -1
        for i, radiography in enumerate(Tools.radiography(self.xray, a, e)):
            tmp_folder, session = radiography
            self.luxcore = session
            App.Console.PrintMessage("\t{} / {}\n".format(i + 1, n))
            last_conv = -1
            while not session.HasDone() and self.luxcore:
                session.UpdateStats()
                stats = session.GetStats()
                step = stats.Get("stats.renderengine.pass").GetInt()
                conv = stats.Get("stats.renderengine.convergence").GetFloat()
                App.Console.PrintMessage("\t\t{} {:.1f}%\n".format(
                    step, 100 * conv))
                self.form.pbar.setValue(100 * (i + conv) / n)
                self.timer.start(0.0)
                self.loop.exec_()
                if(not self.luxcore):
                    break
                if last_conv != conv:
                    imgs = Tools.get_imgs(tmp_folder, session)
                    if i == 0:
                        # For the background image we just need one channels
                        imgs = [imgs[0]]
                    for j, img in enumerate(imgs):
                        if last_conv < 0:
                            current_image += 1
                            self.images.append(img)
                            print(self.titles, current_image)
                            self.form.image.addItem(self.titles[current_image])
                            self.form.image.setCurrentIndex(current_image)
                        else:
                            self.images[j - len(imgs)] = img
                    if self.form.image.currentIndex() == current_image:
                        self.update_plot()
                    last_conv = conv
                else:
                    time.sleep(1.0)
            if(not self.luxcore):
                break

        # Produce the finalradiography image
        return True

    def onStop(self):
        if self.luxcore is None:
            return
        self.form.run.setText(QtGui.QApplication.translate(
            "XRay", "Start", None))
        self.luxcore.Stop()
        self.luxcore = None
        self.plot = None

    def update_plot(self):
        if not self.plot or not self.images:
            return
        img = self.images[self.form.image.currentIndex()]
        self.plot.update(img)


def createTask():
    panel = TaskPanel()
    Gui.Control.showDialog(panel)
    if panel.setupUi():
        Gui.Control.closeDialog()
        return None
    return panel
