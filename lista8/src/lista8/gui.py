import sys
from datetime import datetime, time as datetime_time
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QDateEdit, QFormLayout,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import QDate, Qt

from lista8.models import HttpLogBrowserState
from lista8.log_parser import HttpLogRecord


class LogBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Log browser")
        self.resize(900, 500)

        self.state = HttpLogBrowserState()

        self.init_ui()

    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Top section: Load File
        top_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select log file...")
        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.on_open_clicked)
        
        top_layout.addWidget(self.path_edit)
        top_layout.addWidget(self.open_button)
        main_layout.addLayout(top_layout)

        # Middle section: Master-Detail
        middle_layout = QHBoxLayout()

        # left side (Master) - Filters & List
        left_layout = QVBoxLayout()
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("From"))
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.dateChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.from_date_edit)

        filter_layout.addWidget(QLabel("To"))
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.dateChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.to_date_edit)
        left_layout.addLayout(filter_layout)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_list_selection_changed)
        left_layout.addWidget(self.list_widget)

        middle_layout.addLayout(left_layout, stretch=2)

        # right side(Detail) - Log details
        right_layout = QFormLayout()

        self.remote_host_edit = QLineEdit()
        self.remote_host_edit.setReadOnly(True)
        right_layout.addRow("Remote host:", self.remote_host_edit)

        self.date_edit_field = QLineEdit()
        self.date_edit_field.setReadOnly(True)
        right_layout.addRow("Date:", self.date_edit_field)

        # Time and timezone layout
        time_tz_layout = QHBoxLayout()
        self.time_edit = QLineEdit()
        self.time_edit.setReadOnly(True)
        self.timezone_edit = QLineEdit()
        self.timezone_edit.setReadOnly(True)
        time_tz_layout.addWidget(self.time_edit)
        time_tz_layout.addWidget(QLabel("Timezone:"))
        time_tz_layout.addWidget(self.timezone_edit)
        right_layout.addRow("Time:", time_tz_layout)

        # Status code circle and method layout
        status_method_layout = QHBoxLayout()
        self.status_code_label = QLabel("-")
        self.status_code_label.setFixedSize(40, 25)
        self.status_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.method_edit = QLineEdit()
        self.method_edit.setReadOnly(True)
        status_method_layout.addWidget(self.status_code_label)
        status_method_layout.addWidget(QLabel("Method:"))
        status_method_layout.addWidget(self.method_edit)
        right_layout.addRow("Status code:", status_method_layout)

        self.resource_edit = QLineEdit()
        self.resource_edit.setReadOnly(True)
        right_layout.addRow("Resource:", self.resource_edit)

        self.size_label = QLabel("-")
        right_layout.addRow("Size:", self.size_label)

        middle_layout.addLayout(right_layout, stretch=3)
        main_layout.addLayout(middle_layout)

        # Bottom section: Navigation
        bottom_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.on_previous_clicked)
        self.prev_button.setEnabled(False)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.on_next_clicked)
        self.next_button.setEnabled(False)

        bottom_layout.addWidget(self.prev_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.next_button)
        main_layout.addLayout(bottom_layout)

    # Event handling
    def on_open_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open HTTP Log File", "", "Log Files (*.log);;All Files (*)"
        )
        if file_path:
            self.load_log_file(file_path)

    def load_log_file(self, path_str):
        try:
            path = Path(path_str)
            self.state.load_from_path(path)
            self.path_edit.setText(str(path))

            # Block filter signals during date initialization
            self.from_date_edit.blockSignals(True)
            self.to_date_edit.blockSignals(True)

            if self.state.records:
                timestamps = [r.timestamp for r in self.state.records]
                min_date = min(timestamps).date()
                max_date = max(timestamps).date()

                self.from_date_edit.setDate(QDate(min_date.year, min_date.month, min_date.day))
                self.to_date_edit.setDate(QDate(max_date.year, max_date.month, max_date.day))

            self.from_date_edit.blockSignals(False)
            self.to_date_edit.blockSignals(False)

            # Full UI refresh
            self.refresh_ui()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load log file:\n{str(e)}")

    def on_filter_changed(self):
        # Get dates and convert to Python types
        start_date = self.from_date_edit.date().toPyDate()
        end_date = self.to_date_edit.date().toPyDate()

        # Set end time to EOD (23:59:59)
        start_dt = datetime.combine(start_date, datetime_time.min)
        end_dt = datetime.combine(end_date, datetime_time.max)

        self.state.set_time_range(start_dt, end_dt)
        self.refresh_ui()

    def on_list_selection_changed(self, row):
        if row < 0:
            return
        self.state.select_index(row)
        self.update_detail_view()
        self.update_navigation_buttons()

    def on_previous_clicked(self):
        self.state.select_previous()
        self.sync_state_selection_to_list()

    def on_next_clicked(self):
        self.state.select_next()
        self.sync_state_selection_to_list()

    # --- HELPER METHODS ---

    def refresh_ui(self):
        """Refresh visible logs (Master) and detail view."""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        
        # Get truncated log lines from backend
        previews = self.state.master_items(max_length=30)
        self.list_widget.addItems(previews)
        
        self.list_widget.blockSignals(False)

        # Sync list selection with backend state
        self.sync_state_selection_to_list()

    def sync_state_selection_to_list(self):
        """Update QListWidget highlight based on app state."""
        idx = self.state.selected_index
        self.list_widget.blockSignals(True)
        if idx is not None and 0 <= idx < self.list_widget.count():
            self.list_widget.setCurrentRow(idx)
        else:
            self.list_widget.setCurrentRow(-1)
        self.list_widget.blockSignals(False)

        self.update_detail_view()
        self.update_navigation_buttons()

    def update_detail_view(self):
        """Populate detail components with selected log data."""
        record: HttpLogRecord = self.state.selected_record

        if record is None:
            # Clear view if no selection
            self.remote_host_edit.clear()
            self.date_edit_field.clear()
            self.time_edit.clear()
            self.timezone_edit.clear()
            self.status_code_label.setText("-")
            self.status_code_label.setStyleSheet("")
            self.method_edit.clear()
            self.resource_edit.clear()
            self.size_label.setText("-")
            return

        # Map backend data
        self.remote_host_edit.setText(str(record.orig_h))
        self.date_edit_field.setText(str(record.date))
        self.time_edit.setText(str(record.time))
        self.timezone_edit.setText(record.timestamp.tzname() or "UTC")
        self.method_edit.setText(str(record.method))
        self.resource_edit.setText(str(record.uri))
        
        size = record.response_body_len
        self.size_label.setText(f"{size} Bytes" if size is not None else "-")

        # Style status code circle
        status = record.status_code
        if status is not None:
            self.status_code_label.setText(str(status))
            if 200 <= status < 300:
                # Green for success
                self.status_code_label.setStyleSheet("background-color: #2ECC71; color: white; border-radius: 5px; font-weight: bold;")
            elif 300 <= status < 400:
                # Blue for redirects
                self.status_code_label.setStyleSheet("background-color: #3498DB; color: white; border-radius: 5px; font-weight: bold;")
            else:
                # Red for errors
                self.status_code_label.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px; font-weight: bold;")
        else:
            self.status_code_label.setText("-")
            self.status_code_label.setStyleSheet("")

    def update_navigation_buttons(self):
        """Enable/disable buttons based on list position."""
        self.prev_button.setEnabled(self.state.can_select_previous)
        self.next_button.setEnabled(self.state.can_select_next)

