from PyQt6.QtWidgets import QScrollArea, QDialog, QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QComboBox, QCheckBox, QDateTimeEdit, QSlider, QLabel, QMessageBox, QGridLayout
from PyQt6.QtCore import pyqtSlot, Qt, QThread
from functools import partial
import webbrowser
import requests
import sys
import os
import subprocess
import textwrap
from downloader import NewVersionDownloader


GITHUB_OWNER = "AltitudeRocketry"
class NotificationCenter(QDialog):
    def __init__(self, controller, close_callback, parent=None):
    
        super().__init__(parent)
        self.controller = controller
        self.close_callback = close_callback # Function to call when 'X' is clicked
        self.downloader = None  # Thread reference guard

        self.setWindowTitle("Notifications")
        self.setMinimumSize(350, 400)

        self.initUI()

    def initUI(self):
        NotificationLayout = QVBoxLayout(self)
        header = QHBoxLayout()

        NotificationsAlerts = QLabel("Notification Center")
        CloseButton = QPushButton("X")
        CloseButton.clicked.connect(self.close_callback)

        header.addWidget(NotificationsAlerts)
        header.addWidget(CloseButton)
        NotificationLayout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scrollContent = QWidget()
        self.scrollLayout = QVBoxLayout(scrollContent)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(scrollContent)
        NotificationLayout.addWidget(scroll)

    def refresh_notifications(self):
        """Clears old alerts and pulls live status from the main controller"""
        while self.scrollLayout.count():
            child = self.scrollLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Access the update variable stored in the main WindowController
        update_state = self.controller.UpdateAvailable

        any_updates = False

        for module_name, info in update_state.items():
            if info["updateAvailable"]:
                print(info["ExeName"])
                any_updates = True
                self.add_alert(
                    f"⚠️ {module_name} Update", 
                    f"{module_name} has updates awaiting extraction.", 
                    "#b73e0e",
                    button_title="Update Now",
                    module_name=module_name,
                    fileTarget= info["ExeName"]
                    )

        # Optional fallback if no modules need updating:
        if not any_updates:
            self.add_alert(
                "✅ System Clear", 
                "All local configuration modules match production updates.", 
                "#00ff66"
            )
        
    def add_alert(self, title, description, badge_color, button_title=None, module_name=None, fileTarget=None):
            card = QFrame()
            card.setStyleSheet(f"background-color: #262626; border-radius: 6px; border-left: 4px solid {badge_color};")
            card_lay = QVBoxLayout(card)
            
            lbl_t = QLabel(f"<b>{title}</b>")
            lbl_d = QLabel(description)
            lbl_d.setWordWrap(True)
            lbl_d.setStyleSheet("color: #a6a6a6; font-size: 11px;")
            
            card_lay.addWidget(lbl_t)
            card_lay.addWidget(lbl_d)

            if button_title and module_name:
                btn = QPushButton(button_title)
                btn.setStyleSheet("""
                QPushButton {
                    background-color: #b73e0e;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #d14912;
                }
            """)

                on_click = partial(self.handle_module_update, module_name, fileTarget, btn, lbl_d)
                btn.clicked.connect(on_click)
                card_lay.addWidget(btn)

            self.scrollLayout.addWidget(card)

    def handle_module_update(self, module_name, FileName, btn_widget, status_label):

        btn_widget.setEnabled(False)
        btn_widget.setText("Downloading....")
        status_label.setText("Connecting to server....")

        self.downloader = NewVersionDownloader(GITHUB_OWNER, module_name, exe_name=FileName)

        self.downloader.status_changed.connect(status_label.setText)
        self.downloader.progress_changed.connect(
        lambda pct: status_label.setText(f"Downloading update: {pct}%")
        )
        self.downloader.download_finished.connect(
        lambda success, msg, path: self.onDownloadComplete(success, msg, path, btn_widget, status_label)
        )
    
        self.downloader.start()

    def onDownloadComplete(self, success, message, new_path, btn_widget, status_label):
        if success:
            status_label.setText("Update downloaded! Ready to install.")
            btn_widget.setText("Install & Restart")
            btn_widget.setStyleSheet("background-color: #00ff66; color: black; font-weight: bold;")
            btn_widget.setEnabled(True)
            
            # Disconnect download trigger and re-bind button to installer launcher
            btn_widget.clicked.disconnect()

            # install_action = partial(self.apply_update_and_restart, new_path)
            # btn_widget.clicked.connect(install_action)
            btn_widget.clicked.connect(lambda _: self.apply_update_and_restart(new_path))
        else:
            status_label.setText(message)
            btn_widget.setText("Retry Update")
            btn_widget.setEnabled(True)

    def apply_update_and_restart(self, new_exe_path):
# 1. Handle dev environment check
        if not getattr(sys, 'frozen', False):
            QMessageBox.information(
                self, 
                "Dev Mode", 
                f"Downloaded to:\n{new_exe_path}\n\nRunning from source script (.py). Auto-swap skipped."
            )
            return

        current_exe = os.path.abspath(sys.executable)
        app_dir = os.path.dirname(current_exe)
        exe_name = os.path.basename(current_exe)
        new_exe = os.path.abspath(new_exe_path)
        bat_path = os.path.join(app_dir, "update_installer.bat")

        # 2. Verify downloaded file actually exists before proceeding
        if not os.path.exists(new_exe):
            QMessageBox.critical(self, "Update Error", f"Cannot find downloaded update file at:\n{new_exe}")
            return

        # 3. Create a retry loop batch script to handle file locks cleanly
        # PowerShell script handles retry loop + elevated file replacement
        ps_script = textwrap.dedent(f"""\
                Start-Sleep -Seconds 1
                Stop-Process -Name "{os.path.splitext(exe_name)[0]}" -Force -ErrorAction SilentlyContinue
                
                $retry = 0
                while ($retry -lt 5) {{
                    try {{
                        Move-Item -Path "{new_exe}" -Destination "{current_exe}" -Force -ErrorAction Stop
                        break
                    }} catch {{
                        Start-Sleep -Seconds 1
                        $retry++
                    }}
                }}
                
                # Relaunch via Explorer to pass bootloader security validation
                explorer.exe "{current_exe}"
                
                # Self-delete this PowerShell script file
                Remove-Item -Path $MyInvocation.MyCommand.Path -Force
            """)

        ps_path = os.path.join(app_dir, "update_installer.ps1")
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(ps_script)

        # Launch PowerShell with elevated 'RunAs' permissions to bypass Access Denied
        cmd = f'Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File ""{ps_path}""" -Verb RunAs'
        
        subprocess.Popen(
            ["powershell", "-Command", cmd],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        # 6. Exit Qt application immediately to free file locks
        sys.exit(0)