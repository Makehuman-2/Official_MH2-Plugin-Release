"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck, Elvaerwyn_MH2 2026 V1.2

    Classes:
    * MemTableModel
    * MHQTableView
    * MHMemWindow
    * MHSelectAssetWindow
"""

import sys
import os
import json

from PySide6.QtCore import Qt, QAbstractTableModel, QSortFilterProxyModel, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QPushButton, 
    QGroupBox, QCheckBox, QTableView, QGridLayout, QHeaderView, 
    QAbstractItemView, QScrollArea, QLineEdit, QComboBox, QStyle
)
from PySide6.QtGui import QColor, QPixmap, QIcon 
from gui.common import IconButton, ErrorBox, ImageBox


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
            self.filter_proxy.setFilterKeyColumn(column)
            self.filter_proxy.setFilterFixedString(text)

    def refreshData(self):
        if hasattr(self, 'refresh_func') and self.mtmodel:
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
            value = source_idx.sibling(source_idx.row(), 0).data()
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
        self.setWindowTitle("Memory Usage and Resources")
        self.resize(800, 600)

        self.tables = []
        tab = QTabWidget()

        # Assets
        table = MHQTableView(self, "assets")
        table.addModel(self.refreshAssetTable, ["Group", "Name", "used", "UUID", "Author", "File Name", "Tags"])
        tab.addTab(table.createPage(), "Asset Repository")
        self.tables.append(table)

        # Targets
        table = MHQTableView(self, "targets")
        table.addModel(self.refreshTargetTable, ["Name", "File Increment", "Verts I", "File Decrement", "Verts D", "MHM Identifier", "Current"])
        tab.addTab(table.createPage(), "Targets")
        self.tables.append(table)

        # Macros
        table = MHQTableView(self, "macros")
        table.addModel(self.refreshMacroTable, ["Name", "Verts"])
        tab.addTab(table.createPage(), "Macro-Targets")
        self.tables.append(table)

        # Meshes
        table = MHQTableView(self, "objects")
        table.addModel(self.refreshObjectTable, ["Name", "UUID", "File Name"])
        tab.addTab(table.createPage(), "Meshes")
        self.tables.append(table)

        # Materials
        table = MHQTableView(self, "material")
        table.addModel(self.refreshMaterialTable, ["Name", "File Name"])
        tab.addTab(table.createPage(), "Materials")
        self.tables.append(table)

        # Textures
        table = MHQTableView(self, "textures")
        table.addModel(self.refreshTextureTable, ["#", "Name", "Width", "Height"])
        tab.addTab(table.createPage(), "Textures")
        self.tables.append(table)

        # Missing targets
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
        if self.glob and self.glob.baseClass is not None:
            for elem in getattr(self.glob, 'cachedInfo', []):
                tags = " ".join(elem.tag) if len(elem.tag) > 0 else ""
                used = "yes" if elem.used else "no"
                data.append([elem.folder, elem.name, used, elem.uuid, elem.author, elem.path, tags])
        if len(data) == 0:
            data = [["no assets discovered", "", "", "", "", "", ""]]
        return data

    def refreshTargetTable(self, dummy):
        data = []
        targets = getattr(self.glob, 'Targets', None)
        if targets is not None:
            for target in getattr(targets, 'modelling_targets', []):
                data.append(target.memInfo())
        if len(data) == 0:
            data = [["no targets loaded", "", "", "", "", "", ""]]
        return data

    def refreshMacroTable(self, dummy):
        data = []
        macros = getattr(self.glob, 'macroRepo', None)
        if macros is not None:
            for macro in macros:
                m = self.glob.macroRepo[macro]
                data.append([str(macro), len(m.verts)])
        if len(data) == 0:
            data = [["no macros loaded", ""]]
        return data

    def refreshObjectTable(self, dummy):
        data = []
        if self.glob and self.glob.baseClass is not None:
            base = self.glob.baseClass
            for elem in getattr(base, 'attachedAssets', []):
                data.append([elem.name, elem.uuid, elem.obj_file])
        if len(data) == 0:
            data = [["no objects loaded", "", ""]]
        return data

    def refreshMaterialTable(self, dummy):
        data = []
        if self.glob and self.glob.baseClass is not None:
            base = self.glob.baseClass
            data.append(["base", base.skinMaterial])
            for elem in getattr(base, 'attachedAssets', []):
                data.append([elem.name, elem.material])
        if len(data) == 0:
            data = [["no material loaded", ""]]
        return data

    def refreshTextureTable(self, dummy):
        data = []
        if self.glob and hasattr(self.glob, 'textureRepo'):
            t = self.glob.textureRepo.getTextures()
            if len(t) > 0:
                for texture in t:
                    data.append([t[texture], texture, t[texture].width(), t[texture].height()])
        if len(data) == 0:
            data = [["no textures loaded", "", "", ""]]
        return data

    def refreshMissTargetTable(self, dummy):
        data = []
        targets = getattr(self.glob, 'missingTargets', [])
        for target in targets:
            data.append([target])
        if len(data) == 0:
            data = [["no missing targets found"]]
        return data

    def redisplay_call(self):
        for table in self.tables:
            table.refreshData()

    def close_call(self):
        self.close()

class MHSelectAssetWindow(QWidget):
    def __init__(self, parent, json_data):
        super().__init__()
        self.parent = parent
        self.env = parent.env
        self.glob = parent.glob
        
        # Universal translation layer: Handles BOTH lists and dictionary formats safely
        self.assetjson = json_data if json_data is not None else {}
        self.json = self.assetjson if isinstance(self.assetjson, dict) else {}
        
        if isinstance(self.assetjson, list):
            self.json = {}
            for idx, item in enumerate(self.assetjson):
                if isinstance(item, dict):
                    key = item.get("title", item.get("id", str(idx)))
                    self.json[key] = item

        self.current_asset = None
        self.setWindowTitle("Select from asset list")
        self.resize(1000, 600)
        columns = ["id", "Name", "Category", "Author", "Faces"]

        
        # Unified path assignment so ALL components read/write to the exact same folder location
        self.favorites_path = os.path.join(self.env.path_userdata, "downloads", "favorites.json")
        self.thumbpath = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "thumb.png")
        self.renderpath = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "render")
        self.dbutton = None

        self.tables = []
        self.query = QLineEdit()
        self.columnNum = QComboBox()
        self.columnNum.currentIndexChanged.connect(self.applySearch)
        self.tab = QTabWidget()
        self.tab.currentChanged.connect(self.tabChanged)

        for name in ("clothes", "hair", "eyes", "eyebrows", "eyelashes", "teeth",
                     "expression", "pose", "skin", "rig", "target", "model", "material"):
            table = MHQTableView(self, name, self.callback)
            table.addModel(self.refreshGeneric, columns[:4])
            self.tab.addTab(table.createPage(), name.capitalize())
            self.tables.append(table)

        table = MHQTableView(self, "proxy", self.callback)
        table.addModel(self.refreshProxy, columns)
        self.tab.addTab(table.createPage(), "Proxy")
        self.tables.append(table)
        layout = QHBoxLayout()
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.tab)
        gb = QGroupBox("Filter")
        gb.setObjectName("subwindow")
        hlayout = QHBoxLayout()
        self.query.returnPressed.connect(self.applySearch)
        hlayout.addWidget(self.query)
        hlayout.addWidget(QLabel("Column:"))
        hlayout.addWidget(self.columnNum)
        rbutton = IconButton(3, os.path.join(self.env.path_sysicon, "rescan.png"), "Rescan list.", self.redisplay_call)
        hlayout.addWidget(rbutton)
        gb.setLayout(hlayout)
        vlayout.addWidget(gb)
        layout.addLayout(vlayout)

        right_vlayout = QVBoxLayout()
        assetgb = QGroupBox("Selected asset")
        assetgb.setObjectName("subwindow")
        gblayout = QGridLayout()
        self.camera = IconButton(1, os.path.join(self.env.path_sysicon, "camera.png"), "Load thumbnail", self.loadThumb)
        self.render = IconButton(2, os.path.join(self.env.path_sysicon, "render.png"), "Load demo picture", self.loadDemo)
        gblayout.addWidget(self.camera, 0, 0)
        gblayout.addWidget(self.render, 1, 0)
        self.imglabel = QLabel()
        self.displayThumb(None)
        gblayout.addWidget(self.imglabel, 0, 1, 2, 1)

        gblayout.addWidget(QLabel("Created:"), 2, 0)
        gblayout.addWidget(QLabel("Changed:"), 3, 0)
        gblayout.addWidget(QLabel("License:"), 4, 0)
        gblayout.addWidget(QLabel("Attached:"), 5, 0)
        self.created = QLabel()
        self.changed = QLabel()
        self.license = QLabel()
        self.attached = QLabel()

        self.description = QLabel()
        self.description.setWordWrap(True)
        scroll = QScrollArea(self)
        scroll.setWidget(self.description)
        scroll.setWidgetResizable(True)

        gblayout.addWidget(self.created, 2, 1)
        gblayout.addWidget(self.changed, 3, 1)
        gblayout.addWidget(self.license, 4, 1)
        gblayout.addWidget(self.attached, 5, 1)
        gblayout.addWidget(scroll, 6, 0, 1, 2)
        assetgb.setLayout(gblayout)
        right_vlayout.addWidget(assetgb)

        action_layout = QHBoxLayout()
        self.dbutton = QPushButton("Download")
        self.dbutton.clicked.connect(self.download_call)
        action_layout.addWidget(self.dbutton)

        self.cartBtn = QPushButton()
        self.cartBtn.setFixedWidth(40)
        self.cartBtn.clicked.connect(self.add_selected_to_cart_call)

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_cart_path = os.path.join(root_dir, "data", "icons", "cart.png")
        if not os.path.exists(self.icon_cart_path):
            self.icon_cart_path = os.path.join(self.env.path_sysicon, "cart.png")

        if os.path.exists(self.icon_cart_path):
            self.cartBtn.setIcon(QIcon(self.icon_cart_path))
            self.cartBtn.setIconSize(QSize(20, 20))
        else:
            self.cartBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        action_layout.addWidget(self.cartBtn)
        
        # ADDED: Single item deletion switch to pop an accidental queue addition back out
        self.removeCartBtn = QPushButton("Remove")
        self.removeCartBtn.setFixedWidth(60)
        self.removeCartBtn.setToolTip("Remove current selected item from cart")
        self.removeCartBtn.clicked.connect(self.remove_selected_from_cart_call)
        action_layout.addWidget(self.removeCartBtn)

        self.cartEstimateLabel = QLabel("")
        self.cartEstimateLabel.setStyleSheet("color: #888; font-size: 11px;")
        action_layout.addWidget(self.cartEstimateLabel)

        self.favBtn = QPushButton()
        self.favBtn.setFixedWidth(40)
        self.favBtn.setCheckable(True)
        self.favBtn.clicked.connect(self.toggle_favorite_call)
        action_layout.addWidget(self.favBtn)

        right_vlayout.addLayout(action_layout)
        button = QPushButton("Close")
        button.clicked.connect(self.close_call)
        right_vlayout.addWidget(button)
        layout.addLayout(right_vlayout)

        self.fav_right_panel = QGroupBox("Favorites ⭐")
        self.fav_right_panel.setFixedWidth(240)  
        fav_column_layout = QVBoxLayout(self.fav_right_panel)
        fav_column_layout.setContentsMargins(5, 10, 5, 10)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("<b>Bookmarked</b>"))
        header_row.addStretch()
        
        # ADDED: Empty entire active transfer list instantly inside the side tracking shelf
        self.clearAllCartBtn = QPushButton("Clear Cart")
        self.clearAllCartBtn.setStyleSheet("font-size: 10px; color: #cc0000; padding: 2px;")
        self.clearAllCartBtn.clicked.connect(self.clear_entire_cart_call)
        header_row.addWidget(self.clearAllCartBtn)

        self.refreshFavBtn = QPushButton("Refresh")
        self.refreshFavBtn.setFixedWidth(60)
        self.refreshFavBtn.setStyleSheet("font-size: 10px; padding: 2px;")
        self.refreshFavBtn.clicked.connect(self.populate_favorites_sidebar)
        header_row.addWidget(self.refreshFavBtn)
        fav_column_layout.addLayout(header_row)

        self.favScrollArea = QScrollArea()
        self.favScrollArea.setWidgetResizable(True)
        self.favScrollArea.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.favContentWidget = QWidget()
        self.favContentLayout = QVBoxLayout(self.favContentWidget)
        self.favContentLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.favContentLayout.setContentsMargins(0, 0, 0, 0)
        self.favScrollArea.setWidget(self.favContentWidget)
        fav_column_layout.addWidget(self.favScrollArea)
        layout.addWidget(self.fav_right_panel)

        self.setLayout(layout)
        self.fillComboBox()
        self.populate_favorites_sidebar()
        self.activateDownload()

    def callback(self, value):
        # Convert clicked row data into a plain text string reference
        str_val = str(value)
        matched_key = None
        
        # 1. Match the clicked text name back to its actual JSON database key position!
        if str_val in self.json:
            matched_key = str_val
        else:
            for k, rec in self.json.items():
                if isinstance(rec, dict) and rec.get("title") == str_val:
                    matched_key = k
                    break
                    
        # 2. RUN REGISTRY OPERATIONS IF A CLEAN KEY MATCH WAS DISCOVERED
        if matched_key is not None:
            if matched_key != self.current_asset:
                self.current_asset = matched_key
                self.displayThumb(None)
                
            self.activateDownload()
            m = self.json[matched_key]
            
            # Configure asset interaction permissions safely
            self.camera.setEnabled("files" in m and "thumb" in m["files"])
            self.render.setEnabled("files" in m and "render" in m["files"])
            self.created.setText(m.get("created", ""))
            self.changed.setText(m.get("changed", ""))
            self.license.setText(m.get("license", ""))
            
            text = ""
            if m.get("type") == "material" and "belongs_to" in m:
                b = m["belongs_to"]
                text = "not attached"
                if b.get("belonging_is_assigned") is True:
                    if "belongs_to_core_asset" in b:
                        text = b["belongs_to_core_asset"]
                    elif "belongs_to_title" in b:
                        text = b["belongs_to_title"]

            self.attached.setText(text)
            self.description.setText(m.get("description", ""))

    def update_cart_time_estimate(self):
        if not hasattr(self, 'cartEstimateLabel') or self.cartEstimateLabel is None:
            return
        cart_items = getattr(self.parent, 'download_cart', [])
        if not cart_items or not self.json:
            self.cartEstimateLabel.setText("")
            return

        total_files_to_download = 0
        for asset_name in cart_items:
            if asset_name in self.json:
                from core.importfiles import AssetPack
                assets_helper = AssetPack()
                try:
                    mtype, flist = assets_helper.alistGetFiles(self.json, asset_name)
                    if flist:
                        total_files_to_download += len(flist)
                except Exception:
                    total_files_to_download += 2

        if total_files_to_download == 0:
            self.cartEstimateLabel.setText("")
            return

        calculated_seconds = max(1, int(total_files_to_download * 0.75))
        if calculated_seconds < 60:
            self.cartEstimateLabel.setText(f"Est: ~{calculated_seconds}s ({total_files_to_download} files)")
        else:
            self.cartEstimateLabel.setText(f"Est: ~{round(calculated_seconds / 60, 1)}m ({total_files_to_download} files)")

    def fillComboBox(self):
        if len(self.tables) == 0:
            return
        tindex = self.tab.currentIndex()
        cols = self.tables[tindex].headerColumns()
        self.columnNum.blockSignals(True)
        self.columnNum.clear()
        self.columnNum.addItem("Any")
        self.columnNum.addItems(cols[1:])
        self.columnNum.blockSignals(False)

    def tabChanged(self):
        self.current_asset = None
        if len(self.tables) > 0:
            tindex = self.tab.currentIndex()
            self.tables[tindex].clearSelection()
        self.activateDownload()
        self.query.setText("")
        self.fillComboBox()

    def activateDownload(self):
        has_selection = self.current_asset is not None
        in_cart = has_selection and hasattr(self.parent, 'download_cart') and self.current_asset in self.parent.download_cart
        
        if self.dbutton is not None:
            self.dbutton.setEnabled(has_selection)
        if hasattr(self, 'removeCartBtn') and self.removeCartBtn:
            self.removeCartBtn.setEnabled(in_cart)
            
        if hasattr(self, 'cartBtn') and self.cartBtn is not None:
            self.cartBtn.setEnabled(has_selection)
            if in_cart:
                self.cartBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
                self.cartBtn.setToolTip("Added to Cart ✓")
            else:
                if os.path.exists(self.icon_cart_path):
                    self.cartBtn.setIcon(QIcon(self.icon_cart_path))
                else:
                    self.cartBtn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
                self.cartBtn.setToolTip("Add selected asset to download cart")

        if hasattr(self, 'favBtn') and self.favBtn is not None:
            self.favBtn.setEnabled(has_selection)
            fav_assets = getattr(self.parent, 'favorites_db', {}).get("assets", [])
            
            if has_selection and self.current_asset in fav_assets:
                self.favBtn.setIcon(QIcon())
                self.favBtn.setText("★")     
                self.favBtn.setStyleSheet("color: #ffcc00; font-size: 16px; font-weight: bold; border:none;") 
                self.favBtn.setChecked(True)
                self.favBtn.setToolTip("Favorited! ✓")
            else:
                self.favBtn.setIcon(QIcon())
                self.favBtn.setText("☆")     
                self.favBtn.setStyleSheet("color: #888888; font-size: 16px; border:none;") 
                self.favBtn.setChecked(False)
                self.favBtn.setToolTip("Mark as Favorite")
        
        if hasattr(self, 'update_cart_time_estimate'):
            self.update_cart_time_estimate()

    def applySearch(self):
        tindex = self.tab.currentIndex()
        text = self.query.text()
        col = self.columnNum.currentIndex()
        if col <= 0:
            col = -1
        self.tables[tindex].addFilter(col, text)

    def displayThumb(self, name=None):
        # 1. Start with any specific path string passed directly to the function
        target_path = name
        
        # 2. AUTO-LOAD CACHE LOOKUP: If no path is forced, build it using the asset name string
        if target_path is None and self.current_asset is not None:
            display_title = str(self.current_asset)
            
            # Extract the literal title name from your JSON metadata if available
            if hasattr(self, 'json') and self.current_asset in self.json:
                display_title = self.json[self.current_asset].get("title", display_title)
                
            # Strip away '.png' and replace it with '.thumb' to match the storage layout cleanly
            if display_title.lower().endswith(".png"):
                thumb_filename = display_title[:-4] + ".thumb"
            else:
                thumb_filename = display_title + ".thumb"
                
            # Direct target verification inside your local synchronized cache folder structure
            cached_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "render", thumb_filename)
            if os.path.exists(cached_file):
                target_path = cached_file

        # 3. Fallback to system default question mark placeholder if no file matches on disk
        if target_path is None or not os.path.exists(target_path):
            target_path = os.path.join(self.env.path_sysicon, "noidea.png")
            
        # 4. Scale and push the graphic array onto your right-side visual preview screen canvas
        pixmap = QPixmap(target_path).scaled(128, 128, aspectMode=Qt.KeepAspectRatio, mode=Qt.TransformationMode.SmoothTransformation)
        self.imglabel.setPixmap(pixmap)

    def loadThumb(self):
        v = self.current_asset
        if v is not None:
            # 1. Translate the current selection name into the real database ID key
            matched_key = None
            if v in self.json:
                matched_key = v
            else:
                for k, rec in self.json.items():
                    if isinstance(rec, dict) and rec.get("title") == str(v):
                        matched_key = k
                        break
            
            # 2. Pull down ONLY this specific thumbnail file on demand
            if matched_key is not None and matched_key in self.json:
                m = self.json[matched_key]
                if "files" in m and "thumb" in m["files"]:
                    thumb_url = m["files"]["thumb"]
                    self.env.logLine(8, "Load thumb " + thumb_url)
                    self.parent.assets.getUrlFile(thumb_url, self.thumbpath)
                    self.displayThumb(self.thumbpath)
                else:
                    ErrorBox(self, "Asset has no thumbnail.")
            else:
                ErrorBox(self, "Asset metadata key not found in repository.")

    def loadDemo(self):
        v = self.current_asset
        if v is not None:
            # 1. Translate the current selection name into the real database ID key
            matched_key = None
            if v in self.json:
                matched_key = v
            else:
                for k, rec in self.json.items():
                    if isinstance(rec, dict) and rec.get("title") == str(v):
                        matched_key = k
                        break
            
            # 2. Pull down ONLY this specific large demo render on demand
            if matched_key is not None and matched_key in self.json:
                m = self.json[matched_key]
                if "files" in m and "render" in m["files"]:
                    url = m["files"]["render"]
                    (base, ext) = os.path.splitext(url)
                    path = self.renderpath + ext
                    self.env.logLine(8, "Load render " + url + " to " + path)
                    self.parent.assets.getUrlFile(url, path)
                    ImageBox(self, "Demo image", path)
                else:
                    ErrorBox(self, "Asset has no demo picture.")
            else:
                ErrorBox(self, "Asset metadata key not found in repository.")


    def callback(self, value):
        str_val = str(value)
        matched_key = None
        
        if str_val in self.json:
            matched_key = str_val
        else:
            for k, rec in self.json.items():
                if isinstance(rec, dict) and rec.get("title") == str_val:
                    matched_key = k
                    break
                    
        if matched_key is not None:
            if matched_key != self.current_asset:
                self.current_asset = matched_key
                self.displayThumb(None)
                
            self.activateDownload()
            m = self.json[matched_key]
            
            self.camera.setEnabled("files" in m and "thumb" in m["files"])
            self.render.setEnabled("files" in m and "render" in m["files"])
            self.created.setText(m.get("created", ""))
            self.changed.setText(m.get("changed", ""))
            self.license.setText(m.get("license", ""))
            
            text = ""
            if m.get("type") == "material" and "belongs_to" in m:
                b = m["belongs_to"]
                text = "not attached"
                if b.get("belonging_is_assigned") is True:
                    if "belongs_to_core_asset" in b:
                        text = b["belongs_to_core_asset"]
                    elif "belongs_to_title" in b:
                        text = b["belongs_to_title"]

            self.attached.setText(text)
            self.description.setText(m.get("description", ""))

    def refreshGeneric(self, dtype):
        data = []
        for key, elem in self.json.items():
            if elem.get("type") == dtype:
                author = elem.get("username", "unknown")
                # FIXED: Put the text title at index 0 to match our column shift
                data.append([elem.get("title", key), key, elem.get("category", ""), author])
        if len(data) == 0:
            data = [["no " + dtype + " discovered", "", "", ""]]
        return data

    def refreshProxy(self, dtype):
        data = []
        for key, elem in self.json.items():
            if elem.get("type") == dtype:
                author = elem.get("username", "unknown")
                # FIXED: Put the text title at index 0 to match our column shift
                data.append([elem.get("title", key), key, elem.get("category", ""), author, str(elem.get("faces", ""))])
        if len(data) == 0:
            data = [["no " + dtype + " discovered", "", "", "", ""]]
        return data

    def toggle_favorite_call(self):
        if self.current_asset is None: 
            return
        if not hasattr(self.parent, 'favorites_db') or self.parent.favorites_db is None:
            self.parent.favorites_db = {"assets": [], "creators": []}
            
        if os.path.exists(self.favorites_path):
            try:
                with open(self.favorites_path, 'r', encoding='utf-8') as f:
                    self.parent.favorites_db = json.load(f)
            except Exception:
                pass

        if "assets" not in self.parent.favorites_db:
            self.parent.favorites_db["assets"] = []
        fav_list = self.parent.favorites_db["assets"]
        asset_name = self.current_asset
        
        if asset_name in fav_list:
            fav_list.remove(asset_name)
        else:
            fav_list.append(asset_name)
            
        try:
            os.makedirs(os.path.dirname(self.favorites_path), exist_ok=True)
            with open(self.favorites_path, 'w', encoding='utf-8') as f:
                json.dump(self.parent.favorites_db, f, indent=4)
        except Exception:
            pass
            
        self.activateDownload()
        self.populate_favorites_sidebar()

    def populate_favorites_sidebar(self):
        if not hasattr(self, 'favContentLayout') or self.favContentLayout is None: 
            return
            
        while self.favContentLayout.count() > 0:
            child = self.favContentLayout.takeAt(0)
            if child and child.widget(): 
                child.widget().deleteLater()

        if os.path.exists(self.favorites_path):
            try:
                with open(self.favorites_path, 'r', encoding='utf-8') as f:
                    self.parent.favorites_db = json.load(f)
            except Exception:
                pass

        fav_list = getattr(self.parent, 'favorites_db', {}).get("assets", [])
        if not fav_list:
            no_favs = QLabel("No starred items yet.")
            no_favs.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.favContentLayout.addWidget(no_favs)
            return

        for asset_key in fav_list:
            creator_name = "Unknown Author"
            item_number = "N/A"
            category_type = "Asset"
            
            # Default the visual text label value to the baseline key reference
            display_title = str(asset_key)
            
            matched_rec = None
            if isinstance(self.assetjson, dict):
                if asset_key in self.assetjson:
                    matched_rec = self.assetjson[asset_key]
                else:
                    for k, rec in self.assetjson.items():
                        if isinstance(rec, dict) and (rec.get("title") == asset_key or k == asset_key):
                            matched_rec = rec
                            break
            elif isinstance(self.assetjson, list):
                for item in self.assetjson:
                    if isinstance(item, dict) and (item.get("title") == asset_key or str(item.get("id")) == asset_key):
                        matched_rec = item
                        break

            if matched_rec:
                creator_name = matched_rec.get("username", matched_rec.get("author", "Unknown Author"))
                item_number = str(matched_rec.get("id", "N/A"))
                category_type = matched_rec.get("category", "Asset")
                display_title = matched_rec.get("title", display_title)

            item_box = QGroupBox()
            item_box.setStyleSheet("QGroupBox { background-color: #fcfcfc; border: 1px solid #dcdcdc; border-radius: 6px; }")
            card_vlayout = QVBoxLayout(item_box)
            card_vlayout.setContentsMargins(6, 6, 6, 6)
            card_vlayout.setSpacing(4)

            info_row_layout = QHBoxLayout()
            info_row_layout.setSpacing(6)

            thumb_canvas = QLabel()
            thumb_canvas.setFixedSize(45, 45)
            thumb_canvas.setStyleSheet("background-color: #eaeaea; border: 1px solid #ccc; border-radius: 3px;")
            thumb_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # ========================================================
            # MULTI-EXTENSION THUMBNAIL SEARCH ENGINE
            # ========================================================
            # 1. Search the main render folder directory for custom cache extensions
            local_thumb_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "render", f"{display_title}.thumb")
            
            if not os.path.exists(local_thumb_file):
                local_thumb_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "render", f"{display_title}.thumb.png")
                
            if not os.path.exists(local_thumb_file):
                local_thumb_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, "render", f"{display_title}.png")
                
            # 2. Fallback search nested folder profiles if main directories return unpopulated
            if not os.path.exists(local_thumb_file):
                local_thumb_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, category_type.lower(), display_title, f"{display_title}.thumb")
                
            if not os.path.exists(local_thumb_file):
                local_thumb_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, category_type.lower(), display_title, f"{display_title}.thumb.png")
                
            if not os.path.exists(local_thumb_file):
                local_thumb_file = os.path.join(self.env.path_userdata, "downloads", self.env.basename, category_type.lower(), display_title, f"{display_title}.png")
            # ========================================================

            if os.path.exists(local_thumb_file):
                pix = QPixmap(local_thumb_file)
                if not pix.isNull():
                    thumb_canvas.setPixmap(pix.scaled(43, 43, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                thumb_canvas.setText("📦")
                thumb_canvas.setStyleSheet("background-color: #e0e0e0; color: #777; font-size: 16px; border: 1px solid #ccc; border-radius: 3px;")

            info_row_layout.addWidget(thumb_canvas)

            text_stack = QVBoxLayout()
            text_stack.setSpacing(1)
            
            title_lbl = QLabel(f"<b>{display_title}</b>")
            title_lbl.setWordWrap(True)
            title_lbl.setStyleSheet("font-size: 11px; color: #222;")
            
            author_lbl = QLabel(f"By: {creator_name}")
            author_lbl.setStyleSheet("font-size: 10px; color: #555;")
            
            id_lbl = QLabel(f"ID: #{item_number}")
            id_lbl.setStyleSheet("font-size: 9px; color: #888; font-family: monospace;")

            text_stack.addWidget(title_lbl)
            text_stack.addWidget(author_lbl)
            text_stack.addWidget(id_lbl)
            
            info_row_layout.addLayout(text_stack)
            card_vlayout.addLayout(info_row_layout)

            btn_row = QHBoxLayout()
            btn_row.setSpacing(4)

            cart_btn = QPushButton("Add to Cart")
            cart_btn.setStyleSheet("font-size: 10px; padding: 2px 4px; height: 18px;")
            # Bind click shortcut mapping parameters strictly back to the unique asset key identifier
            cart_btn.clicked.connect(lambda checked=False, target_name=asset_key: self.add_shortcut_to_cart(target_name))
            btn_row.addWidget(cart_btn)

            unstar_btn = QPushButton("Unstar")
            unstar_btn.setStyleSheet("font-size: 10px; color: #cc0000; padding: 2px 4px; height: 18px;")
            unstar_btn.clicked.connect(lambda checked=False, target_name=asset_key: self.remove_shortcut_favorite(target_name))
            btn_row.addWidget(unstar_btn)

            card_vlayout.addLayout(btn_row)
            self.favContentLayout.addWidget(item_box)

    def remove_shortcut_favorite(self, asset_name):
        fav_assets = getattr(self.parent, 'favorites_db', {}).get("assets", [])
        if asset_name in fav_assets:
            fav_assets.remove(asset_name)
            
        try:
            with open(self.favorites_path, 'w', encoding='utf-8') as f:
                json.dump(self.parent.favorites_db, f, indent=4)
        except Exception:
            pass
            
        self.activateDownload()
        self.populate_favorites_sidebar()

    def add_shortcut_to_cart(self, asset_name):
        if hasattr(self.parent, 'download_cart') and asset_name not in self.parent.download_cart:
            self.parent.download_cart.append(asset_name)
            self.activateDownload()
            self.update_cart_time_estimate()
            self.sync_parent_cart_labels()

    def download_call(self):
        if self.current_asset is not None:
            self.env.logLine(8, "Download asset " + self.current_asset)
            self.parent.singleDownLoad(self.current_asset)

    def redisplay_call(self):
        for table in self.tables:
            table.refreshData()

    def close_call(self):
        self.close()

    def add_selected_to_cart_call(self):
        if self.current_asset is not None:
            assetname = self.current_asset
            if hasattr(self.parent, 'download_cart'):
                if assetname not in self.parent.download_cart:
                    self.parent.download_cart.append(assetname)
        self.sync_parent_cart_labels()
        self.activateDownload()

    def remove_selected_from_cart_call(self):
        if self.current_asset is not None and hasattr(self.parent, 'download_cart'):
            if self.current_asset in self.parent.download_cart:
                self.parent.download_cart.remove(self.current_asset)
                self.sync_parent_cart_labels()
            self.activateDownload()

    def clear_entire_cart_call(self):
        if hasattr(self.parent, 'download_cart'):
            self.parent.download_cart.clear()
            self.sync_parent_cart_labels()
        self.activateDownload()

    def sync_parent_cart_labels(self):
        cart_len = len(getattr(self.parent, 'download_cart', []))
        if hasattr(self.parent, 'masterCartLabel') and self.parent.masterCartLabel:
            self.parent.masterCartLabel.setText(f"Items waiting in queue: {cart_len}")
        if hasattr(self.parent, 'checkoutBtn') and self.parent.checkoutBtn:
            self.parent.checkoutBtn.setText(f"Download All ({cart_len} Items)")
            self.parent.checkoutBtn.setEnabled(cart_len > 0)
