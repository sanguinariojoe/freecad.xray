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
from ..xrayUtils import Selection


class TaskPanel:
    def __init__(self):
        self.name = "XRay object to scan"
        self.ui = ":/ui/TaskPanel_xrayAddObject.ui"
        self.form = Gui.PySideUic.loadUi(self.ui)
        self.sources = []

    def accept(self):
        parent = self.xrays[self.form.xray.currentIndex()]
        freqs = []
        attenuations = []
        for i in range(self.form.attenuations.rowCount()):
            freqs.append(Units.parseQuantity(
                self.form.attenuations.item(i, 0).text()))
            attenuations.append(Units.parseQuantity(
                self.form.attenuations.item(i, 1).text()))
        dens = Units.parseQuantity(self.form.dens.text())

        for source in self.sources:
            obj = Tools.createXRayObject(
                parent,
                source,
                dens,
                freqs,
                attenuations)
            obj = App.ActiveDocument.Objects[-1]
            obj.IsXRayObject = True

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
        self.form.xray = self.widget(QtGui.QComboBox, "xray")
        self.form.attenuations = self.widget(QtGui.QTableWidget, "attenuations")
        self.form.add_row = self.widget(QtGui.QPushButton, "add_row")
        self.form.del_row = self.widget(QtGui.QPushButton, "del_row")
        self.form.dens = self.widget(QtGui.QLineEdit, "dens")
        self.form.preset = self.widget(QtGui.QComboBox, "preset")

        if self.initValues():
            return True
        QtCore.QObject.connect(
            self.form.add_row,
            QtCore.SIGNAL("pressed()"),
            self.onAddRow)
        QtCore.QObject.connect(
            self.form.del_row,
            QtCore.SIGNAL("pressed()"),
            self.onDelRow)
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
        self.sources = Selection.get_solids()
        self.xrays = Selection.get_xrays(App.ActiveDocument.Objects)
        if not self.xrays:
            # This situation isalready covered in ../XRayGui.py
            return True
        # Fill the X-Rays combo box
        icon = QtGui.QIcon(QtGui.QPixmap(":/icons/XRay_Workbench.svg"))
        self.form.xray.clear()
        for xray in self.xrays:
            self.form.xray.addItem(icon, xray.Label)
        self.form.xray.setCurrentIndex(0)

        # Fills the presets
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

    def __copy_row(self, org, dst):
        for i in range(2):
            item = QtGui.QTableWidgetItem()
            item.setText(self.form.attenuations.item(org, i).text())
            self.form.attenuations.setItem(dst, i, item)

    def __interpolate_row(self, i):
        i0 = None if i == 0 else i - 1
        i1 = None if i >= self.form.attenuations.rowCount() - 1 else i + 1
        if i0 is None and i1 is None:
            return
        if i0 is None or i1 is None:
            self.__copy_row(i0 if i1 is None else i1, i)
            return
        for j in range(2):
            try:
                prev_val = Units.parseQuantity(
                    self.form.attenuations.item(i0, j).text())
                next_val = Units.parseQuantity(
                    self.form.attenuations.item(i1, j).text())
            except OSError:
                continue
            try:
                val = 0.5 * (prev_val + next_val)
            except ArithmeticError:
                continue
            item = QtGui.QTableWidgetItem()
            item.setText(val.UserString)
            self.form.attenuations.setItem(i, j, item)            

    def onAddRow(self):
        if not self.form.attenuations.rowCount():
            i = 0
        else:
            i = self.form.attenuations.currentRow() + 1
        self.form.attenuations.insertRow(i)
        self.__interpolate_row(i)            
        self.form.del_row.setEnabled(True)

    def onDelRow(self):
        i = self.form.attenuations.currentRow()
        self.form.attenuations.removeRow(i)
        if self.form.attenuations.rowCount() <= 1:
            self.form.del_row.setEnabled(False)


def createTask():
    panel = TaskPanel()
    Gui.Control.showDialog(panel)
    if panel.setupUi():
        Gui.Control.closeDialog()
        return None
    return panel
