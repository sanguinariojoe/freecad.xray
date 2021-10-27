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

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Units
import Part
from PySide import QtGui, QtCore
from . import Tools
from .. import XRay_rc


SLIDER_STYLESHEET = """
QSlider::groove:vertical {
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
    stop: 0 #66e, stop: 1 #bbf);
background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
    stop: 0 #bbf, stop: 1 #55f);
border: 1px solid #777;
width: 10px;
border-radius: 4px;
}

QSlider::sub-page:vertical {
background: white;
border: 1px solid #bbb;
width: 10px;
border-radius: 4px;
}

QSlider::add-page:vertical {
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,
    stop: 0 #66e, stop: 1 #bbf);
background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
    stop: 0 #bbf, stop: 1 #55f);
border: 1px solid #777;
width: 10px;
border-radius: 4px;
}

QSlider::handle:vertical {
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #eee, stop:1 #ccc);
border: 1px solid #777;
height: 5px;
margin-top: -2px;
margin-bottom: -2px;
border-radius: 4px;
}

QSlider::handle:vertical:hover {
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
    stop:0 #fff, stop:1 #ddd);
border: 1px solid #444;
border-radius: 4px;
}

QSlider::sub-page:vertical:disabled {
background: #bbb;
border-color: #999;
}

QSlider::add-page:vertical:disabled {
background: #eee;
border-color: #999;
}

QSlider::handle:vertical:disabled {
background: #eee;
border: 1px solid #aaa;
border-radius: 4px;
}
"""

class TaskPanel:
    def __init__(self):
        self.name = "XRay simulator creation"
        self.ui = ":/ui/TaskPanel_xrayCreate.ui"
        self.form = Gui.PySideUic.loadUi(self.ui)

    def accept(self):
        xray = Tools.createSimulator(
            Units.parseQuantity(self.form.min_freq.text()),
            Units.parseQuantity(self.form.max_freq.text()),
            [v.value() / 100 for v in self.form.spectrum],
            self.form.freqs_n.value(),
            self.form.projection.currentIndex(),
            Units.parseQuantity(self.form.radius.text()),
            Units.parseQuantity(self.form.height.text()),
            Units.parseQuantity(self.form.distance.text()),
            self.form.resolution_x.value(),
            self.form.resolution_y.value())
        xray = App.ActiveDocument.Objects[-1]
        xray.IsXRay = True

        # Ugly trick to enforce FreeCAD to show the XRay geom
        Part.show(xray.Shape)
        App.ActiveDocument.recompute()
        App.ActiveDocument.removeObject(App.ActiveDocument.Objects[-1].Name)
        App.ActiveDocument.recompute()

        return True

    def reject(self):
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
        self.form.min_freq = self.widget(QtGui.QLineEdit, "min_freq")
        self.form.max_freq = self.widget(QtGui.QLineEdit, "max_freq")
        i = 1
        self.form.spectrum = []
        while widget := self.widget(QtGui.QSlider, "spectrum_{:02d}".format(i)):
            widget.setStyleSheet(SLIDER_STYLESHEET)
            self.form.spectrum.append(widget)
            i += 1
        self.form.preset = self.widget(QtGui.QComboBox, "preset")
        self.form.freqs_n = self.widget(QtGui.QSpinBox, "freqs_n")
        self.form.projection = self.widget(QtGui.QComboBox, "projection")

        self.form.radius = self.widget(QtGui.QLineEdit, "radius")
        self.form.height = self.widget(QtGui.QLineEdit, "height")
        self.form.distance = self.widget(QtGui.QLineEdit, "distance")

        self.form.resolution_x = self.widget(QtGui.QSpinBox, "resolution_x")
        self.form.resolution_y = self.widget(QtGui.QSpinBox, "resolution_y")

        if self.initValues():
            return True
        QtCore.QObject.connect(
            self.form.preset,
            QtCore.SIGNAL("currentIndexChanged(int)"),
            self.onPreset)
        QtCore.QObject.connect(
            self.form.freqs_n,
            QtCore.SIGNAL("valueChanged(int)"),
            self.onNFreqs)

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
        self.onPreset(self.form.preset.currentIndex())
        return False

    def onPreset(self, i):
        min_f, max_f, values = Tools.ligth_preset(i, len(self.form.spectrum))
        self.form.min_freq.setText(min_f.UserString)
        self.form.max_freq.setText(max_f.UserString)
        for i,v in enumerate(values):
            self.form.spectrum[i].setValue(int(round(100 * v)))

    def onNFreqs(self, i):
        if i % 3 == 0:
            return
        i = int(3 * round(i / 3))
        self.form.freqs_n.setValue(i)


def createTask():
    panel = TaskPanel()
    Gui.Control.showDialog(panel)
    if panel.setupUi():
        Gui.Control.closeDialog()
        return None
    return panel
