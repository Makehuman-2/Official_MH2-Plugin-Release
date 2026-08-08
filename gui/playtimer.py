"""
    License information: data/licenses/makehuman_license.txt
    Author: Elvaerwyn_MH2 Makehuman 2 2026

    Classes:
    * MHPlayTimer
    * MHPlayAlert
"""

import os
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QInputDialog, QDialog
from PySide6.QtGui import QIcon

class MHPlayAlert(QDialog):
    def __init__(self, parent, custom_minutes, total_minutes):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        self.setStyleSheet(
            "QDialog { background-color: #2b2b2b; border: 3px solid #f69038; border-radius: 8px; }"
            "QLabel { color: #ffffff; font-family: 'Segoe UI'; font-size: 12px; margin-top: 2px; background: transparent; }"
            "QPushButton { background-color: #444444; color: #ffffff; font-weight: bold; border: 1px solid #666; border-radius: 4px; padding: 5px 15px; min-width: 80px; }"
            "QPushButton:hover { background-color: #f69038; border: 1px solid #fdb863; color: #ffffff; }"
        )
        
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)
        
        # 1. CUSTOM THEME HEADER BAR
        custom_header = QWidget()
        custom_header.setStyleSheet("background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #f69038, stop:1 #323232); border-top-left-radius: 5px; border-top-right-radius: 5px;")
        header_layout = QHBoxLayout(custom_header)
        header_layout.setContentsMargins(15, 6, 15, 6)
        
        header_title = QLabel("Immersive Play Break Reminder ⏳ ")
        header_title.setStyleSheet("color: #ffffff; font-family: 'Segoe UI'; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_title)
        master_layout.addWidget(custom_header)
        
        # 2. INNER CONTENT CONTAINER PANEL
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Display the continuous lifetime sum accumulation text string
        text_lbl = QLabel(
            f"<h3>You have been creating for a total of {total_minutes} minutes!</h3>"
            f"<p>To stay fresh and prevent creative eye strain, it is highly recommended to take a short break ⏱️.</p>"
            f"<b>Please remember to save your active character modifications before closing MH2 💾!</b>"
        )
        text_lbl.setWordWrap(True)
        content_layout.addWidget(text_lbl)
        
        # Interactive response button layout row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(False)
        self.ok_btn.setAutoDefault(False)
        self.ok_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        self.keep_btn = QPushButton("Keep Creating")
        self.keep_btn.setDefault(False)
        self.keep_btn.setAutoDefault(False)
        self.keep_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.keep_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.keep_btn)
        
        content_layout.addLayout(btn_layout)
        master_layout.addWidget(content_widget)


class MHPlayTimer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.env = parent.env if hasattr(parent, 'env') else None
        self.icon_dir = os.path.join("data", "icons")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(4)

        # 1. The Clickable Time Ticker Label Component
        self.timeLabel = QLabel("Session: 00:00:00")
        self.timeLabel.setToolTip("Click to change break reminder interval!")
        self.timeLabel.mousePressEvent = self.label_clicked_event
        layout.addWidget(self.timeLabel)

        # 2. ON-SCREEN PLAY BUTTON
        self.playBtn = QPushButton()
        layout.addWidget(self.playBtn)

        # 3. ON-SCREEN PAUSE BUTTON
        self.pauseBtn = QPushButton()
        layout.addWidget(self.pauseBtn)

        # 4. ON-SCREEN STOP / RESET BUTTON
        self.stopBtn = QPushButton()
        layout.addWidget(self.stopBtn)

        # CRITICAL CONNECTIONS: Explicitly wires your buttons up to execute their Python tasks!
        self.playBtn.clicked.connect(self.resume_timer)
        self.pauseBtn.clicked.connect(self.pause_timer)
        self.stopBtn.clicked.connect(self.reset_timer)

        # Draw icons using your exact local folder assets directly
        self.style_all_buttons()

        # Lightweight interface heartbeat loop updates the text readout every 1 second
        self.visual_heartbeat = QTimer(self)
        self.visual_heartbeat.timeout.connect(self.update_display_text)
        self.visual_heartbeat.start(1000)

    def style_theme_button(self, button, icon_filename, fallback_text, tooltip):
        button.setFixedWidth(22)
        button.setFixedHeight(20)
        button.setToolTip(tooltip)
        
        button.setStyleSheet(
            "QPushButton {"
            "    background-color: transparent !important;"
            "    border: none !important;"
            "    padding: 2px !important;"
            "    margin: 0px !important;"
            "}"
            "QPushButton:hover {"
            "    background-color: rgba(255, 255, 255, 0.15) !important;" 
            "    border: 1px solid #ffffff !important;" 
            "    border-radius: 4px !important;"
            "}"
        )
        
        file_path = os.path.join(self.icon_dir, icon_filename)
        if os.path.exists(file_path):
            button.setIcon(QIcon(file_path))
            button.setIconSize(QSize(13, 13))
        else:
            button.setText(fallback_text)

    def label_clicked_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            current_minutes = 120
            if self.env and "play_timer_minutes" in self.env.session:
                current_minutes = self.env.session["play_timer_minutes"]

            new_minutes, ok_pressed = QInputDialog.getInt(
                self, "Set Break Alarm", "Enter break interval (Minutes):", current_minutes, 1, 1440, 1
            )
            
            if ok_pressed and self.env:
                self.env.session["play_timer_minutes"] = new_minutes
                if hasattr(self.env, 'saveSession'):
                    self.env.saveSession()
                
                if hasattr(self.parent, 'seconds_elapsed'):
                    self.parent.seconds_elapsed = 0
                    self.parent.total_minutes_elapsed = 0
                    self.parent.reminder_fired = False
                
                self.resume_timer()

    def pause_timer(self):
        main_clock = getattr(self.parent, 'session_clock', None)
        if main_clock:
            main_clock.stop()

    def resume_timer(self):
        main_clock = getattr(self.parent, 'session_clock', None)
        if main_clock:
            main_clock.start(1000)

    def reset_timer(self):
        if hasattr(self.parent, 'seconds_elapsed'):
            self.parent.seconds_elapsed = 0
            self.parent.total_minutes_elapsed = 0
            if hasattr(self.parent, 'reminder_fired'):
                self.parent.reminder_fired = False
        self.resume_timer()

    def style_all_buttons(self):
        self.style_theme_button(self.playBtn, "play_icon.png", "▶️", "Resume Session Tracking")
        self.style_theme_button(self.pauseBtn, "pause.png", "⏸", "Pause Session Tracking")
        self.style_theme_button(self.stopBtn, "reset2.png", "🔄", "Stop and Reset Session Clock")

    def update_display_text(self):
        if hasattr(self.parent, 'seconds_elapsed'):
            s_elapsed = self.parent.seconds_elapsed
            hours = s_elapsed // 3600
            minutes = (s_elapsed % 3600) // 60
            seconds = s_elapsed % 60
            
            main_clock = getattr(self.parent, 'session_clock', None)
            is_active = main_clock.isActive() if main_clock else True
            
            if not is_active:
                self.timeLabel.setText(f"Session: {hours:02d}:{minutes:02d}:{seconds:02d} (Paused)")
                self.timeLabel.setStyleSheet("font-family: 'Segoe UI', monospace; font-size: 11px; color: #777777; font-weight: bold; background: transparent; margin-top: 0px !important; padding: 0px 4px !important;")
                return
                
            self.timeLabel.setText(f"Session: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            if hasattr(self.parent, 'reminder_fired') and self.parent.reminder_fired and hasattr(self.parent, 'session_clock'):
                self.parent.session_clock.stop()
                
                chosen_minutes = 120
                if self.env and "play_timer_minutes" in self.env.session:
                    chosen_minutes = self.env.session["play_timer_minutes"]
                    
                self.parent.total_minutes_elapsed += chosen_minutes
                
                alert_box = MHPlayAlert(self.parent, chosen_minutes, self.parent.total_minutes_elapsed)
                result = alert_box.exec()
                if result == QDialog.Accepted:
                    self.parent.seconds_elapsed = 0
                    self.parent.total_minutes_elapsed = 0
                else:
                    self.parent.seconds_elapsed = 0
                    
                self.parent.reminder_fired = False
                self.parent.session_clock.start(1000)

            self.timeLabel.setStyleSheet("font-family: 'Segoe UI', monospace; font-size: 11px; color: #ffffff; font-weight: bold; background: transparent; margin-top: 0px !important; padding: 0px 4px !important;")
                
