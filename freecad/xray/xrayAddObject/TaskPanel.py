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


class TaskPanel:
    def __init__(self):
        self.name = "XRay object to scan"
        self.ui = ":/ui/TaskPanel_xrayAddObject.ui"
        self.form = Gui.PySideUic.loadUi(self.ui)

    def accept(self):
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
        self.form.attenuations = self.widget(QtGui.QTableWidget, "attenuations")
        self.form.add_row = self.widget(QtGui.QPushButton, "add_row")
        self.form.del_row = self.widget(QtGui.QPushButton, "del_row")
        self.form.dens = self.widget(QtGui.QLineEdit, "dens")
        self.form.preset = self.widget(QtGui.QComboBox, "preset")

        if self.initValues():
            return True
        QtCore.QObject.connect(
            self.form.preset,
            QtCore.SIGNAL("currentIndexChanged(int)"),
            self.onPreset)

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
        Tools.init_presets(self.form.preset)
        default_index = Tools.get_preset_index("Calcium")
        self.form.preset.setCurrentIndex(default_index)
        self.onPreset(default_index)
        return False

    def onPreset(self, i):
        dens, data = Tools.load_preset(i)
        self.form.dens.setText(dens.UserString)
        self.form.attenuations.clearContents()
        for i, (e, mu) in enumerate(data):
            self.form.attenuations.insertRow(i)
            item = QtGui.QTableWidgetItem()
            item.setText(e.UserString)
            self.form.attenuations.setItem(i, 0, item)
            item = QtGui.QTableWidgetItem()
            item.setText(mu.UserString)
            self.form.attenuations.setItem(i, 1, item)


def createTask():
    panel = TaskPanel()
    Gui.Control.showDialog(panel)
    if panel.setupUi():
        Gui.Control.closeDialog()
        return None
    return panel
