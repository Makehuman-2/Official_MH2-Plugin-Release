"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck, Elvaerwyn_MH2 2026 V1.2

    Classes:
    * MemTableModel
    * MHQTableView
    * MHMemWindow
"""

from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, QRadioButton, QGroupBox, QCheckBox,
    QTableView, QGridLayout, QHeaderView, QAbstractItemView, QScrollArea, QLineEdit, QComboBox
    )
from PySide6.QtGui import QColor, QPixmap
from gui.common import IconButton, ErrorBox, ImageBox

import sys
import os

class MemTableModel(QAbstractTableModel):
    def __init__(self, data, columns):
        super(MemTableModel, self).__init__()

        self.horizontalHeaders = [''] * len(columns)
        for i, c in enumerate(columns):
            self.setHeaderData(i, Qt.Horizontal, c)

        self._data = data

    def bestFit(self, table):
        h = table.horizontalHeader()
        for i in range(0, len(self.horizontalHeaders)):
            h.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def refreshData(self, data):
        self._data = data

    def setHeaderData(self, section, orientation, data, role=Qt.EditRole):
        if orientation == Qt.Horizontal and role in (Qt.DisplayRole, Qt.EditRole):
            try:
                self.horizontalHeaders[section] = data
                return True
            except:
                return False
        return super().setHeaderData(section, orientation, data, role)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            try:
                return self.horizontalHeaders[section]
            except:
                pass
        return super().headerData(section, orientation, role)

    def data(self, index, role):
        if not self._data or index.row() >= len(self._data):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            try:
                return self._data[index.row()][index.column()]
            except IndexError:
                return None

    def rowCount(self, index=None):
        return len(self._data)

    def columnCount(self, index=None):
        if not self._data or len(self._data) == 0:
            return len(self.horizontalHeaders)
        return len(self._data[0])

    def refreshWithReset(self, data):
        self.beginResetModel()
        self.refreshData(data)
        self.endResetModel()

class MHQTableView(QTableView):
    def __init__(self, parent, mtype, callback=None):
        super().__init__()
        self.type = mtype
        self.filter_proxy = None
        self.refresh_func = None
        self.mtmode = None
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setVisible(False)

        self.callback = callback
        if callback is not None:
            self.clicked.connect(self.sendResult)

    def addModel(self, refresh_func, header):

        self.refresh_func = refresh_func
        self.header = header
        self.mtmodel = MemTableModel(refresh_func(self.type), header)

        self.filter_proxy = QSortFilterProxyModel()
        self.filter_proxy.setSourceModel(self.mtmodel)
        self.filter_proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter_proxy.setFilterKeyColumn(-1)
        self.setModel(self.filter_proxy)
        self.mtmodel.bestFit(self)

    def headerColumns(self):
        return self.header

    def addFilter(self, column, text):
        if self.filter_proxy:
            self.filter_proxy.setFilterFixedString(text)
            self.filter_proxy.setFilterKeyColumn(column)

    def refreshData(self):
        if self.refresh_func and self.mtmodel:
            self.mtmodel.refreshWithReset(self.refresh_func(self.type))
            self.viewport().update()

    def createPage(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        layout.addWidget(self)
        return page

    def sendResult(self):
        idx = self.selectionModel().currentIndex()
        if self.filter_proxy and idx.isValid():
            source_idx = self.filter_proxy.mapToSource(idx)
            value= idx.sibling(idx.row(),0).data()
            if self.callback:
                self.callback(value)

class MHMemWindow(QWidget):
    """
    Message window to display used data
    """
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        self.setWindowTitle("Memory Usage and Ressources")
        self.resize (800, 600)

        self.tables = []
        tab = QTabWidget()

        # assets
        #
        table = MHQTableView(self, "assets")
        table.addModel(self.refreshAssetTable, ["Group", "Name", "used", "UUID",  "Author", "File Name", "Tags"])
        tab.addTab(table.createPage(), "Asset Repository")
        self.tables.append(table)

        # targets
        #
        table = MHQTableView(self, "targets")
        table.addModel(self.refreshTargetTable, ["Name", "File Increment", "Verts I",  "File Decrement", "Verts D", "MHM Identifier", "Current"])
        tab.addTab(table.createPage(), "Targets")
        self.tables.append(table)

        # macros
        #
        table = MHQTableView(self, "macros")
        table.addModel(self.refreshMacroTable, ["Name", "Verts"])
        tab.addTab(table.createPage(), "Macro-Targets")
        self.tables.append(table)

        # meshes
        #
        table = MHQTableView(self, "objects")
        table.addModel(self.refreshObjectTable, ["Name", "UUID", "File Name"])
        tab.addTab(table.createPage(), "Meshes")
        self.tables.append(table)

        # materials
        #
        table = MHQTableView(self, "material")
        table.addModel(self.refreshMaterialTable, ["Name", "File Name"])
        tab.addTab(table.createPage(), "Materials")
        self.tables.append(table)

        # textures
        #
        table = MHQTableView(self, "textures")
        table.addModel(self.refreshTextureTable, ["#", "Name", "Width", "Height"])
        tab.addTab(table.createPage(), "Textures")
        self.tables.append(table)

        # missing targets
        #
        table = MHQTableView(self, "missing targets")
        table.addModel(self.refreshMissTargetTable, ["Name"])
        tab.addTab(table.createPage(), "Missing Targets (last load)")
        self.tables.append(table)

        layout = QVBoxLayout()
        layout.addWidget(tab)
        hlayout = QHBoxLayout()

        rbutton = QPushButton("Redisplay")
        rbutton.clicked.connect(self.redisplay_call)
        hlayout.addWidget(rbutton)

        button = QPushButton("Close")
        button.clicked.connect(self.close_call)
        hlayout.addWidget(button)

        layout.addLayout(hlayout)
        self.setLayout(layout)

    def refreshAssetTable(self, dummy):
        data = []
        if self.glob.baseClass is not None:
            for elem in self.glob.cachedInfo:
                tags = " ".join(elem.tag) if len(elem.tag) > 0 else ""
                used = "yes" if elem.used else "no"
                data.append([elem.folder, elem.name, used, elem.uuid, elem.author, elem.path, tags])
        if len(data) == 0:
            data = [["no assets discovered"]]
        return (data)

    def refreshTargetTable(self, dummy):
        data = []
        targets = self.glob.Targets
        if targets is not None:
            for target in targets.modelling_targets:
                data.append(target.memInfo())
        if len(data) == 0:
            data = [["no targets loaded"]]
        return (data)

    def refreshMacroTable(self, dummy):
        data = []
        macros = self.glob.macroRepo
        if macros is not None:
            for macro in macros:
                m = self.glob.macroRepo[macro]
                data.append([str(macro), len(m.verts)])
        if len(data) == 0:
            data = [["no macros loaded"]]
        return (data)

    def refreshObjectTable(self, dummy):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            for elem in base.attachedAssets:
                data.append([elem.name, elem.uuid, elem.obj_file])
        if len(data) == 0:
            data = [["no objects loaded"]]
        return (data)

    def refreshMaterialTable(self, dummy):
        data = []
        if self.glob.baseClass is not None:
            base = self.glob.baseClass
            data.append(["base", base.skinMaterial])
            for elem in base.attachedAssets:
                data.append([elem.name, elem.material])
        if len(data) == 0:
            data = [["no material loaded"]]
        return (data)

    def refreshTextureTable(self, dummy):
        data = []
        t = self.glob.textureRepo.getTextures()
        if len(t) > 0:
            for texture in t:
                data.append([t[texture][1], texture, t[texture][0].width(), t[texture][0].height()])
        else:
            data = [["no textures loaded"]]
        return (data)


    def refreshMissTargetTable(self, dummy):
        data = []
        targets = self.glob.missingTargets
        for target in targets:
            data.append([target])
        if len(data) == 0:
            data = [["no missing targets found"]]
        return (data)


    def redisplay_call(self):
        """
        refreshes all tabs
        """
        for table in self.tables:
            table.refreshData()

    def close_call(self):
        self.close()

