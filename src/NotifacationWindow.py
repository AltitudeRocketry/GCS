from PyQt6.QtWidgets import QScrollArea, QDialog, QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QComboBox, QCheckBox, QDateTimeEdit, QSlider, QLabel, QMessageBox, QGridLayout
from PyQt6.QtCore import pyqtSlot, Qt, QThread

class NotificationCenter(QDialog):
    def __init__(self, controller, close_callback, parent=None):
    
        super().__init__(parent)
        self.controller = controller
        self.close_callback = close_callback # Function to call when 'X' is clicked

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
        
        if update_state:
            self.add_alert("⚠️ Update Available", "Vanguard Ground Station has updates awaiting extraction.", "#b73e0e")
        else:
            self.add_alert("✅ System Clear", "All local configuration modules match production updates.", "#00ff66")
        
    def add_alert(self, title, description, badge_color):
            card = QFrame()
            card.setStyleSheet(f"background-color: #262626; border-radius: 6px; border-left: 4px solid {badge_color};")
            card_lay = QVBoxLayout(card)
            
            lbl_t = QLabel(f"<b>{title}</b>")
            lbl_d = QLabel(description)
            lbl_d.setWordWrap(True)
            lbl_d.setStyleSheet("color: #a6a6a6; font-size: 11px;")
            
            card_lay.addWidget(lbl_t)
            card_lay.addWidget(lbl_d)
            self.scrollLayout.addWidget(card)