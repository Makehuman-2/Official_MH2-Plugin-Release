#############################################################################
##
## Plugin_panel to add custom features. V1.2
## Part of the MakeHuman 2 Project contributed by Elvaerwyn_MH2 2026
##
#############################################################################

import os
import sys
import importlib.util
from importlib.metadata import entry_points
from PySide6 import QtWidgets, QtCore

class CommunityPanel(QtWidgets.QWidget):
    def __init__(self, parent=None, app_reference=None, glob_reference=None):
        """
        Pure embedded layout panel. 
        Works perfectly inside the new non-parallel layout system.
        """
        super().__init__(parent)
        self.app = app_reference
        self.glob = glob_reference
        
        # Tracking dictionaries for both architectures
        self.registered_official = {}    # Holds the official TOML entry points
        self.registered_community = {}   # Holds the raw community .py files
        self.active_extensions = {}      # Tracks currently active modules
        self.checkboxes = {}             # Tracks visible UI toggles
        
        # Steam & PyInstaller Safe Paths
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # Steam & PyInstaller Safe Paths
        if getattr(sys, 'frozen', False):
            # Points to the root directory where makehuman.exe sits
            base_dir = os.path.dirname(sys.executable)
            # Use sys._MEIPASS or base_dir to anchor internal scripts
            self.internal_dir = getattr(sys, '_MEIPASS', base_dir)
        else:
            base_dir = os.path.abspath(os.getcwd())
            self.internal_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.extensions_dir = os.path.join(base_dir, 'extensions')

        
        # Build the user interface frame
        self.init_ui()
        
        # Isolated Sequential Execution (Non-Parallel Safe Loading)
        try:
            self.load_all_extensions_sequential()
        except Exception as startup_fault:
            print(f"[Extensions Rescue] System initialization issue: {startup_fault}")

    def init_ui(self):
        """Constructs a clean scroll interface separating official and mod components."""
        self.layout_tree = QtWidgets.QVBoxLayout(self)
        self.layout_tree.setContentsMargins(5, 5, 5, 5)
        self.layout_tree.setSpacing(6)
        
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout_tree.addWidget(self.scroll_area)

        # HOT REFRESH CONTROL: Mounts a clean button directly onto the interface tree
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh Community Extensions", self)
        self.refresh_btn.clicked.connect(self.trigger_live_refresh)
        self.layout_tree.addWidget(self.refresh_btn)
        
        # Visual Diagnostic Status
        self.status_label = QtWidgets.QLabel("Status: Engine Scanning Active...", self.scroll_widget)
        self.status_label.setStyleSheet("color: #4CAF50; font-style: italic; font-size: 11px;")
        self.scroll_layout.addWidget(self.status_label)

    # Inside class CommunityPanel in makehuman2/plugin_panel.py
    def load_all_extensions_sequential(self):
        """Runs discovery pipelines across official, local core, and community folders."""
        os.makedirs(self.extensions_dir, exist_ok=True)
        
        try:
            self.discover_official_plugins()
        except Exception as official_error:
            print(f"[MH2 Error] Official entry points pipeline halted: {official_error}")
            
        try:
            # FIXED: Look next to makehuman.exe when packaged, not inside python's internal zip files
            if getattr(sys, 'frozen', False):
                base_folder = os.path.dirname(sys.executable)
            else:
                base_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            core_tools_dir = os.path.join(base_folder, 'mh2_official_tools')
            if os.path.exists(core_tools_dir):
                original_extensions_dir = self.extensions_dir
                self.extensions_dir = core_tools_dir
                self.discover_community_extensions()
                self.extensions_dir = original_extensions_dir
        except Exception as core_scan_error:
            print(f"[MH2 Error] Core tools directory scan failed: {core_scan_error}")

        try:
            self.discover_community_extensions()
        except Exception as community_error:
            print(f"[MH2 Error] Community directory pipeline halted: {community_error}")


    # =========================================================================
    # PIPELINE 1: TOML Entry Points (Official Systems)
    # =========================================================================
    # This function is for inside makehuman2/plugin_panel.py
    def discover_official_plugins(self):
        """
        Queries metadata files registered via pyproject.toml natively.
        If not installed via pip, it parses the local pyproject.toml automatically
        so it works instantly for all users out-of-the-box.
        """
        from importlib.metadata import entry_points
        import importlib
        
        # 1. First run a standard metadata query pass 
        discovered = list(entry_points(group='makehuman2.plugins'))
        
        # 2. LOCAL TOML BACKUP FALLBACK ROUTINE
        # If no installed packages are found, read directly from the project root folder
        if not discovered:
            try:
                import tomllib  # Built-in python 3.11+
            except ImportError:
                try:
                    import toml as tomllib # Fallback for python < 3.11
                except ImportError:
                    tomllib = None

            if tomllib:
                # Travel up to target your root configuration file location
                current_dir = os.path.dirname(os.path.abspath(__file__))
                toml_path = os.path.join(os.path.dirname(current_dir), 'pyproject.toml')
                
                # Check alternative local structural paths if needed
                if not os.path.exists(toml_path):
                    toml_path = os.path.join(current_dir, 'pyproject.toml')

                if os.path.exists(toml_path):
                    with open(toml_path, "rb") as f:
                        toml_data = tomllib.load(f)
                    
                    # Dig through your exact formatting nodes to find registered extensions
                    entry_points_block = (toml_data.get("project", {})
                                         .get("entry-points", {})
                                         .get("makehuman2.plugins", {}))
                    
                    # Reconstruct mock entry point objects to sync with your loader mechanics 
                    from types import SimpleNamespace
                    for name, value in entry_points_block.items():
                        module_path, func_name = value.split(":")
                        
                        def local_load(m_path=module_path, f_name=func_name):
                            mod = importlib.import_module(m_path)
                            return getattr(mod, f_name)
                            
                        mock_ep = SimpleNamespace(
                            name=name,
                            value=value,
                            load=local_load
                        )
                        discovered.append(mock_ep)

        # 3. CONSTRUCT WIDGET CHECKBOXES 
        has_official = False
        for ep in discovered:
            if not has_official:
                self.add_section_header("Official Sub-Systems")
                has_official = True
                
            plugin_name = f"official_{ep.name}"
            self.registered_official[plugin_name] = ep
            
            # Mounts row cleanly to your scrolling tree canvas 
            self.create_row(
                internal_id=plugin_name,
                display_name=f"[Official] {ep.name.replace('_', ' ').title()}",
                toggle_callback=lambda state, target_ep=ep, name_id=plugin_name: self.toggle_official(target_ep, name_id, state)
            )

    def toggle_official(self, entry_point, name, state):
        """Loads official code modules into memory when enabled."""
        if state == 2 or state == QtCore.Qt.Checked:
            try:
                init_func = entry_point.load()
                res = init_func(self.app, self.glob)
                if res:
                    self.active_extensions[name] = res
                print(f"[MH2 Engine] Core Extension Hooked: {name}")
            except Exception as e:
                print(f"[MH2 Engine Error] Core feature execution failure on {name}: {e}")
        else:
            self.active_extensions.pop(name, None)

    # =========================================================================
    # PIPELINE 2: Dynamic User Directory (Community Drop-ins)
    # =========================================================================
    def discover_community_extensions(self):
        """
        Smart Hybrid Scanner: Finds loose .py files (like the lighting extension)
        AND checks inside subfolders for a script.
        """
        if not os.path.exists(self.extensions_dir):
            return
            
        items = os.listdir(self.extensions_dir)
        has_community = False
        
        if self.extensions_dir not in sys.path:
            sys.path.append(self.extensions_dir)
            
        for item in items:
            if item.startswith("__"):
                continue
                
            path_target = os.path.join(self.extensions_dir, item)
            file_path = None
            raw_module_name = ""
            
            # STYLE A: If it's a subfolder, look inside for the script
            if os.path.isdir(path_target):
                # Try common names like main.py or the folder's name itself
                for possible_name in ["main.py", f"{item}.py"]:
                    check_path = os.path.join(path_target, possible_name)
                    if os.path.exists(check_path):
                        file_path = check_path
                        raw_module_name = item
                        if path_target not in sys.path:
                            sys.path.append(path_target)
                        break

            # STYLE B: If it's a raw loose file (like your original DNA script)
            elif os.path.isfile(path_target) and item.endswith(".py") and item != "plugin_panel.py":
                file_path = path_target
                raw_module_name = item[:-3]

            # If we successfully located a valid python execution script, mount it
            if file_path and raw_module_name:
                if not has_community:
                    self.add_section_header("Community Extensions")
                    has_community = True
                    
                unique_sys_key = f"mh2_mod_{raw_module_name}"
                internal_id = f"community_{raw_module_name}"
                
                try:
                    # Dynamically compile the script payload context safely
                    spec = importlib.util.spec_from_file_location(unique_sys_key, file_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[unique_sys_key] = module
                    spec.loader.exec_module(module)
                    
                    self.registered_community[internal_id] = module
                    
                    # Create the checkbox UI row using the mod name string
                    self.create_row(
                        internal_id=internal_id,
                        display_name=raw_module_name.replace('_', ' ').title(),
                        toggle_callback=lambda state, name_id=internal_id: self.toggle_community(name_id, state)
                    )
                    print(f"[MH2 Extensions Engine] Successfully loaded community plugin: {raw_module_name}")
                except Exception as e:
                    print(f"[MH2 Extensions Error] Failed compiling script path {raw_module_name}: {e}")

    def toggle_community(self, name, state):
        """Runs the load/unload methods inside loose user scripts."""
        module = self.registered_community.get(name)
        if not module:
            return
            
        if state == 2 or state == QtCore.Qt.Checked:
            for hook_name in ["load_extension", "initialize_extension"]:
                if hasattr(module, hook_name):
                    try:
                        res = getattr(module, hook_name)(self.app, self.glob)
                        if res:
                            self.active_extensions[name] = res
                        break
                    except Exception as e:
                        print(f"[Mod Crash] Active hook error inside {name}: {e}")
        else:
            for hook_name in ["unload_extension", "shutdown_extension"]:
                if hasattr(module, hook_name):
                    try:
                        getattr(module, hook_name)()
                        break
                    except Exception as e:
                        print(f"[Mod Cleanup Error] Trace failure on {name}: {e}")
            self.active_extensions.pop(name, None)

    # =========================================================================
    # UI Layout Helpers
    # =========================================================================
    def add_section_header(self, text):
        header = QtWidgets.QLabel(text, self.scroll_widget)
        header.setStyleSheet("font-weight: bold; color: #888888; margin-top: 8px; font-size: 11px; text-transform: uppercase;")
        self.scroll_layout.addWidget(header)

    def create_row(self, internal_id, display_name, toggle_callback):
        checkbox = QtWidgets.QCheckBox(display_name, self.scroll_widget)
        checkbox.stateChanged.connect(toggle_callback)
        self.scroll_layout.addWidget(checkbox)
        self.checkboxes[internal_id] = checkbox
    # =========================================================================
    # EXTENSION HOT-REFRESH ENGINE (V1.3 - SEQUENTIAL PIPELINE CLEANUP)
    # =========================================================================
    def trigger_live_refresh(self):
        """
        Clears visible checkbox frames, unloads cached memory modules, 
        and re-runs your discovery pipeline live for fresh downloads.
        """
        print("\n[MH2 Refresh] Flushing compiled python script caches...")
        
        # 1. Force python to forget cached files so updates read fresh from disk
        import sys
        for internal_id in list(self.registered_community.keys()):
            raw_name = internal_id.replace("community_", "")
            unique_sys_key = f"mh2_mod_{raw_name}"
            if unique_sys_key in sys.modules:
                del sys.modules[unique_sys_key]

        # 2. Clear out your tracking dictionary lookup states completely
        self.registered_official.clear()
        self.registered_community.clear()
        self.active_extensions.clear()
        self.checkboxes.clear()

        # 3. Destroy all visible checkbox row layouts inside the layout tree
        # We save index 0 to protect your green status_label text widget frame!
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        # 4. Process event ticks to clear UI memory blocks and re-run your scanning methods
        QtCore.QCoreApplication.processEvents()
        self.load_all_extensions_sequential()
        print("[MH2 Refresh] Hot-refresh complete. New folders mapped successfully.\n")
