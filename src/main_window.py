"""
Main Window - The primary UI for the photo culling application
"""

import os
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox,
    QMenuBar, QMenu, QStatusBar, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSignal as Signal, QUrl, QSize, QRect
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QAction, QTransform, QDragEnterEvent, QDropEvent, QIcon, QPainter, QFont, QColor
from PIL import Image, ImageOps
from dataclasses import dataclass
from typing import Callable

from .photo_manager import PhotoManager, PhotoPair, PhotoAction


@dataclass
class PendingAction:
    """Represents a pending action with its details."""
    action_type: str
    photo: PhotoPair
    description: str
    action_func: Callable
    previous_index: int


class CountdownWidget(QWidget):
    """Compact countdown widget integrated into status bar area with progress and undo."""
    
    action_confirmed = pyqtSignal()  # Emitted when countdown finishes
    action_cancelled = pyqtSignal()  # Emitted when user cancels
    
    def __init__(self):
        super().__init__()
        self.countdown_seconds = 5
        self.remaining_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_countdown)
        self.pending_action = None
        self.action_color = "#6b7280"
        
        # Compact design for status bar integration
        self.setFixedHeight(32)  # Reduced height to fit better in status bar
        self.setMinimumWidth(280)  # More compact minimum width
        self.setMaximumWidth(420)  # More compact maximum width
        self._setup_ui()
        self.hide()  # Initially hidden
    
    def _setup_ui(self):
        """Set up the compact countdown widget UI."""
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # Reduced margins for status bar
        layout.setSpacing(8)  # Tighter spacing between elements
        
        # Description label with better sizing
        self.description_label = QLabel()
        self.description_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 600;
                color: #e0e0e0;
                background: transparent;
                min-height: 24px;
                qproperty-alignment: 'AlignVCenter';
            }
        """)
        self.description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.description_label)
        
        # Progress container with proper sizing
        self.progress_container = QFrame()
        self.progress_container.setFixedSize(100, 22)  # More compact width
        self.progress_container.setStyleSheet("background: transparent;")
        layout.addWidget(self.progress_container)
        
        # Compact undo button
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setFixedSize(55, 22)  # Smaller to fit status bar
        self.undo_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 0px;
                border: none;
                border-radius: 4px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
            QPushButton:pressed {
                background-color: #374151;
            }
        """)
        self.undo_btn.clicked.connect(self._cancel_action)
        layout.addWidget(self.undo_btn)
    
    def start_countdown(self, pending_action: PendingAction):
        """Start the countdown for a pending action."""
        self.pending_action = pending_action
        self.remaining_time = self.countdown_seconds
        self.description_label.setText(pending_action.description)
        
        # Set action color based on action type
        action_colors = {
            "delete_raw": "#f59e0b",  # Amber
            "delete_all": "#ef4444", # Red  
            "keep_all": "#10b981",   # Green
            "skip": "#6b7280"        # Gray
        }
        
        self.action_color = action_colors.get(pending_action.action_type, "#6b7280")
        
        # Modern styling that matches the app theme
        self.setStyleSheet(f"""
            CountdownWidget {{
                background-color: #2a2a2a;
                border: 1px solid {self.action_color};
                border-radius: 6px;
                margin: 2px;
            }}
        """)
        
        # Update undo button color to match action
        self.undo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.action_color};
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 0px;
                border: none;
                border-radius: 4px;
                min-height: 22px;
            }}
            QPushButton:hover {{
                background-color: {self.action_color}CC;
            }}
            QPushButton:pressed {{
                background-color: {self.action_color}99;
            }}
        """)
        
        self.show()
        self.timer.start(50)  # Update every 50ms for smoother animation
        
    def _update_countdown(self):
        """Update the countdown timer and progress bar."""
        self.remaining_time -= 0.05  # Smoother decrement
        
        if self.remaining_time <= 0:
            self._confirm_action()
        else:
            self.update()  # Trigger repaint for progress bar
    
    def _confirm_action(self):
        """Confirm the pending action."""
        self.timer.stop()
        self.hide()
        self.action_confirmed.emit()
    
    def _cancel_action(self):
        """Cancel the pending action."""
        self.timer.stop()
        self.hide()
        self.action_cancelled.emit()
    
    def paintEvent(self, event):
        """Custom paint event for the smooth progress bar."""
        super().paintEvent(event)
        
        if not self.pending_action or self.remaining_time <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get progress container geometry
        container_rect = self.progress_container.geometry()
        
        # Countdown text positioned above the progress bar
        remaining_seconds = max(0, int(self.remaining_time + 0.99))  # Round up for display
        text = f"{remaining_seconds}s"
        
        # Text styling with better contrast
        painter.setPen(QColor("#f0f0f0"))
        font = QFont()
        font.setPointSize(9)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        
        # Position text in the top portion of the container
        text_rect = QRect(container_rect.x(), container_rect.y(), 
                         container_rect.width(), 10)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
        
        # Progress bar background positioned below the text
        bg_rect = QRect(container_rect.x(), container_rect.y() + 12, 
                       container_rect.width(), 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3a3a3a"))  # Lighter background for better contrast
        painter.drawRoundedRect(bg_rect, 4, 4)
        
        # Progress bar fill (smooth animation with gradient effect)
        progress = max(0.0, min(1.0, self.remaining_time / self.countdown_seconds))
        progress_width = int(bg_rect.width() * progress)
        
        if progress_width > 0:
            progress_rect = QRect(bg_rect.x(), bg_rect.y(), progress_width, bg_rect.height())
            
            # Create a subtle gradient effect
            gradient_color = QColor(self.action_color)
            painter.setBrush(gradient_color)
            painter.drawRoundedRect(progress_rect, 4, 4)


class FileStatusWidget(QWidget):
    """Modern visual file status indicator showing JPEG and RAW presence plus action status."""

    def __init__(self):
        super().__init__()
        self.has_jpeg = False
        self.has_raw = False
        self.action = None
        self.setFixedSize(140, 32)
        self.setStyleSheet("background: transparent;")
        self.setToolTip("File format indicators")

    def update_status(self, has_jpeg: bool, has_raw: bool, action=None):
        """Update the file status and trigger a repaint."""
        self.has_jpeg = has_jpeg
        self.has_raw = has_raw
        self.action = action
        self.update()  # Trigger paintEvent

        # Update tooltip based on current status
        tooltip_parts = []
        if has_jpeg and has_raw:
            tooltip_parts.append("Both JPEG and RAW files present")
        elif has_jpeg:
            tooltip_parts.append("JPEG file only")
        elif has_raw:
            tooltip_parts.append("RAW file only")
        else:
            tooltip_parts.append("No files present")

        if action and action.value != "none":
            action_text = {
                "keep_all": "✓ Kept all files",
                "delete_raw": "⚠ RAW deleted",
                "delete_all": "✗ All files deleted",
                "skipped": "→ Skipped"
            }.get(action.value, f"Action: {action.value}")
            tooltip_parts.append(action_text)

        self.setToolTip(" • ".join(tooltip_parts))

    def paintEvent(self, event):
        """Custom paint event to draw the file status indicators."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set font
        font = QFont()
        font.setPointSize(9)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)

        # Calculate dimensions
        spacing = 4
        indicator_width = (self.width() - spacing) // 2

        # Determine if this photo has been processed
        has_action = self.action and self.action.value != "none"

        # JPEG indicator
        jpeg_rect = self.rect().adjusted(0, 0, -indicator_width - spacing, 0)
        if self.has_jpeg:
            # Active state - filled with modern green and subtle shadow
            if not has_action:
                # First draw a subtle shadow/glow
                shadow_rect = jpeg_rect.adjusted(-1, 1, 1, 1)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(16, 185, 129, 30))  # Semi-transparent green
                painter.drawRoundedRect(shadow_rect, 6, 6)

            # Choose color based on action status
            if has_action:
                painter.setBrush(QColor("#6b7280"))  # Muted gray for processed
            else:
                painter.setBrush(QColor("#10b981"))  # Emerald green for unprocessed

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(jpeg_rect, 6, 6)
            painter.setPen(QColor("#ffffff"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
        else:
            # Inactive state - subtle outline with darker background
            painter.setPen(QColor("#404040"))
            painter.setBrush(QColor("#252525"))  # Darker background
            painter.drawRoundedRect(jpeg_rect, 6, 6)
            painter.setPen(QColor("#606060"))

        painter.drawText(jpeg_rect, Qt.AlignmentFlag.AlignCenter, "JPEG")

        # RAW indicator
        raw_rect = self.rect().adjusted(indicator_width + spacing, 0, 0, 0)
        if self.has_raw:
            # Active state - filled with modern amber and subtle shadow
            if not has_action:
                # First draw a subtle shadow/glow
                shadow_rect = raw_rect.adjusted(-1, 1, 1, 1)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(245, 158, 11, 30))  # Semi-transparent amber
                painter.drawRoundedRect(shadow_rect, 6, 6)

            # Choose color based on action status and action type
            if has_action:
                if self.action.value == "delete_raw":
                    painter.setBrush(QColor("#ef4444"))  # Red for deleted RAW
                else:
                    painter.setBrush(QColor("#6b7280"))  # Muted gray for other actions
            else:
                painter.setBrush(QColor("#f59e0b"))  # Amber for unprocessed

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(raw_rect, 6, 6)
            painter.setPen(QColor("#ffffff"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
        else:
            # Inactive state - subtle outline with darker background
            painter.setPen(QColor("#404040"))
            painter.setBrush(QColor("#252525"))  # Darker background
            painter.drawRoundedRect(raw_rect, 6, 6)
            painter.setPen(QColor("#606060"))

        painter.drawText(raw_rect, Qt.AlignmentFlag.AlignCenter, "RAW")


class ActionIndicatorWidget(QWidget):
    """Action status indicator showing a colored circle for the action taken."""

    def __init__(self):
        super().__init__()
        self.action = None
        self.setFixedSize(20, 20)
        self.setStyleSheet("background: transparent;")
        self.setToolTip("No action taken")

    def update_action(self, action=None):
        """Update the action and trigger a repaint."""
        self.action = action
        self.update()  # Trigger paintEvent

        # Update tooltip based on action
        if action and action.value != "none":
            action_tooltips = {
                "keep_all": "Kept all files",
                "delete_raw": "RAW file deleted",
                "delete_all": "All files deleted",
                "skipped": "Photo skipped"
            }
            self.setToolTip(action_tooltips.get(action.value, f"Action: {action.value}"))
        else:
            self.setToolTip("No action taken")

    def paintEvent(self, event):
        """Custom paint event to draw the action indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate circle position (centered)
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = 6

        # Determine if an action has been taken
        has_action = self.action and self.action.value != "none"

        if has_action:
            # Filled circle with action-specific color
            action_colors = {
                "keep_all": QColor("#10b981"),    # Green
                "delete_raw": QColor("#f59e0b"),  # Amber
                "delete_all": QColor("#ef4444"), # Red
                "skipped": QColor("#6b7280")     # Gray
            }

            action_color = action_colors.get(self.action.value, QColor("#6b7280"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(action_color)
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        else:
            # Unfilled circle (outline only)
            painter.setPen(QColor("#6b7280"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)


class ImageLabel(QLabel):
    """Custom QLabel for displaying images with proper scaling and drag & drop."""

    # Signal to notify when a folder is dropped
    folder_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setText("No image loaded\n\nDrag & drop a folder here to open it")
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 2px solid #404040;
                border-radius: 12px;
                color: #a0a0a0;
                font-size: 16px;
            }
        """)

        # Enable drag & drop
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            # Check if any of the URLs is a directory
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.is_dir():
                        event.acceptProposedAction()
                        # Change appearance to indicate drop is accepted
                        self.setStyleSheet("""
                            QLabel {
                                background-color: #252525;
                                border: 2px solid #10b981;
                                border-radius: 12px;
                                color: #10b981;
                                font-size: 16px;
                            }
                        """)
                        return
        event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        # Restore normal appearance
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 2px solid #404040;
                border-radius: 12px;
                color: #a0a0a0;
                font-size: 16px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        # Restore normal appearance
        self.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                border: 2px solid #404040;
                border-radius: 12px;
                color: #a0a0a0;
                font-size: 16px;
            }
        """)

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.is_dir():
                        self.folder_dropped.emit(str(file_path))
                        event.acceptProposedAction()
                        return
        event.ignore()


class ProgressWidget(QWidget):
    """Widget to show session progress."""

    def __init__(self):
        super().__init__()
        self.processed = 0
        self.total = 0
        self.setFixedHeight(24)
        self.setStyleSheet("background: transparent;")

    def update_progress(self, processed: int, total: int):
        """Update progress values."""
        self.processed = processed
        self.total = total
        self.update()

        # Update tooltip
        if total > 0:
            percentage = int((processed / total) * 100)
            self.setToolTip(f"Progress: {processed}/{total} photos processed ({percentage}%)")
        else:
            self.setToolTip("No photos loaded")

    def paintEvent(self, event):
        """Custom paint event for progress bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg_rect = self.rect().adjusted(0, 6, 0, -6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#404040"))
        painter.drawRoundedRect(bg_rect, 6, 6)

        # Progress bar
        if self.total > 0:
            progress_width = int((self.processed / self.total) * bg_rect.width())
            if progress_width > 0:
                progress_rect = bg_rect.adjusted(0, 0, -(bg_rect.width() - progress_width), 0)
                painter.setBrush(QColor("#10b981"))
                painter.drawRoundedRect(progress_rect, 6, 6)

        # Text
        if self.total > 0:
            percentage = int((self.processed / self.total) * 100)
            text = f"{percentage}%"
            painter.setPen(QColor("#e0e0e0"))
            font = QFont()
            font.setPointSize(9)
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.photo_manager = PhotoManager()
        self.current_pixmap: Optional[QPixmap] = None
        self.confirm_deletions = True  # Default to requiring confirmation
        self.pending_action: Optional[PendingAction] = None

        # Image cache for faster navigation
        self.image_cache = {}  # path -> QPixmap
        self.cache_size_limit = 10  # Cache up to 10 images

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()

        # Auto-resize timer to prevent too frequent resizing
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._delayed_image_update)

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("PhotoSift - Photo Management Tool")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        # Set modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #181818;
                color: #e0e0e0;
            }
            QWidget {
                background-color: #181818;
                color: #e0e0e0;
            }
            QMenuBar {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border-bottom: 1px solid #404040;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QMenuBar::item:selected {
                background-color: #2a2a2a;
            }
            QMenu {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #2a2a2a;
            }
            QStatusBar {
                background-color: #1e1e1e;
                color: #a0a0a0;
                border-top: 1px solid #404040;
            }
        """)

        # Set application icon
        self._set_app_icon()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create menu bar
        self._create_menu_bar()

        # Photo info panel with modern styling
        info_panel = QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(2, 8, 2, 8)

        # Action indicator (colored circle showing action status)
        self.action_indicator = ActionIndicatorWidget()
        info_layout.addWidget(self.action_indicator)

        # File name label
        self.filename_label = QLabel("No file loaded")
        self.filename_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0; background: transparent; border: none; margin-left: 2px;")
        info_layout.addWidget(self.filename_label)

        info_layout.addStretch()

        # File status widget (modern visual indicator)
        self.file_status_widget = FileStatusWidget()
        info_layout.addWidget(self.file_status_widget)

        main_layout.addWidget(info_panel)

        # Image display area
        self.image_label = ImageLabel()
        main_layout.addWidget(self.image_label)

        # Progress widget for session progress
        self.progress_widget = ProgressWidget()
        main_layout.addWidget(self.progress_widget)

        # Action buttons with improved spacing and grouping
        button_container = QFrame()
        button_container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(12, 8, 12, 8)

        # Keep all button
        self.keep_all_btn = QPushButton("Keep All (K)")
        self.keep_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.keep_all_btn.clicked.connect(self._keep_all_files)
        button_layout.addWidget(self.keep_all_btn)

        # Skip button (for marking as reviewed without action)
        self.skip_btn = QPushButton("Skip (S)")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
            QPushButton:pressed {
                background-color: #374151;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.skip_btn.clicked.connect(self._skip_photo)
        button_layout.addWidget(self.skip_btn)

        # Delete RAW button
        self.delete_raw_btn = QPushButton("Delete RAW (R)")
        self.delete_raw_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
            QPushButton:pressed {
                background-color: #b45309;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.delete_raw_btn.clicked.connect(self._delete_raw_file)
        button_layout.addWidget(self.delete_raw_btn)

        # Delete all button
        self.delete_all_btn = QPushButton("Delete All (D)")
        self.delete_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.delete_all_btn.clicked.connect(self._delete_all_files)
        button_layout.addWidget(self.delete_all_btn)

        main_layout.addWidget(button_container)

        # Navigation buttons with modern container
        nav_container = QFrame()
        nav_container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 8, 12, 8)

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
                padding: 10px 20px;
                border: 1px solid #4b5563;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4b5563;
                border-color: #6b7280;
            }
            QPushButton:pressed {
                background-color: #374151;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #606060;
                border-color: #404040;
            }
        """)
        self.prev_btn.clicked.connect(self._previous_photo)
        nav_layout.addWidget(self.prev_btn)

        # Photo counter in the center of navigation
        self.counter_label = QLabel("0 / 0")
        self.counter_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #e0e0e0;
            background: transparent;
            border: none;
            padding: 8px 16px;
        """)
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.counter_label)

        self.next_btn = QPushButton("Next →")
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #e0e0e0;
                font-size: 13px;
                font-weight: 500;
                padding: 10px 20px;
                border: 1px solid #4b5563;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #4b5563;
                border-color: #6b7280;
            }
            QPushButton:pressed {
                background-color: #374151;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #606060;
                border-color: #404040;
            }
        """)
        self.next_btn.clicked.connect(self._next_photo)
        nav_layout.addWidget(self.next_btn)

        main_layout.addWidget(nav_container)

        # Status bar with integrated countdown widget
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Open a folder to begin")
        
        # Add countdown widget to status bar (right side)
        self.countdown_widget = CountdownWidget()
        self.status_bar.addPermanentWidget(self.countdown_widget)

        # Initially disable action buttons
        self._update_button_states()

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_folder_action = QAction("Open Folder...", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+O"))
        open_folder_action.triggered.connect(self._open_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        self.confirm_action = QAction("Confirm Deletions", self)
        self.confirm_action.setCheckable(True)
        self.confirm_action.setChecked(self.confirm_deletions)
        self.confirm_action.triggered.connect(self._toggle_confirmation)
        settings_menu.addAction(self.confirm_action)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Action shortcuts
        QShortcut(QKeySequence("K"), self, self._keep_all_files)
        QShortcut(QKeySequence("S"), self, self._skip_photo)
        QShortcut(QKeySequence("R"), self, self._delete_raw_file)
        QShortcut(QKeySequence("D"), self, self._delete_all_files)
        
        # Undo shortcut
        QShortcut(QKeySequence("U"), self, self._undo_action)
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_action)

        # Navigation shortcuts
        QShortcut(QKeySequence("Left"), self, self._previous_photo)
        QShortcut(QKeySequence("Right"), self, self._next_photo)
        QShortcut(QKeySequence("Space"), self, self._next_photo)

    def _undo_action(self):
        """Undo the current pending action."""
        if self.pending_action:
            self.countdown_widget._cancel_action()

    def _connect_signals(self):
        """Connect PhotoManager signals to UI updates."""
        self.photo_manager.photos_loaded.connect(self._on_photos_loaded)
        self.photo_manager.photo_deleted.connect(self._on_photo_deleted)
        self.photo_manager.error_occurred.connect(self._on_error)
        self.photo_manager.session_updated.connect(self._on_session_updated)

        # Connect countdown widget signals
        self.countdown_widget.action_confirmed.connect(self._execute_pending_action)
        self.countdown_widget.action_cancelled.connect(self._cancel_pending_action)

        # Connect drag & drop signal
        self.image_label.folder_dropped.connect(self._on_folder_dropped)
    def _open_folder(self):
        """Open folder dialog and load photos."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Photo Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            self.photo_manager.load_folder(folder)

    def _on_photos_loaded(self, count: int):
        """Handle photos loaded signal."""
        # Clear cache when loading new folder
        self._clear_image_cache()

        if count > 0:
            self.status_bar.showMessage(f"Loaded {count} photos")
            self._update_display()
        else:
            self.status_bar.showMessage("No photos found in folder")
            self._clear_display()

        self._update_button_states()

    def _on_photo_deleted(self, photo_name: str):
        """Handle photo deleted signal."""
        self.status_bar.showMessage(f"Deleted {photo_name}")
        self._update_display()
        self._update_button_states()

    def _on_error(self, error_message: str):
        """Handle error signal."""
        QMessageBox.warning(self, "Error", error_message)
        self.status_bar.showMessage("Error occurred")

    def _on_session_updated(self):
        """Handle session data updates."""
        # Update the display to reflect new action status
        self._update_display()

        # Update status bar with progress info
        processed, total, percentage = self.photo_manager.get_session_progress()
        if total > 0:
            self.status_bar.showMessage(f"Progress: {processed}/{total} photos processed ({percentage}%)")

    def _update_display(self):
        """Update the photo display and info."""
        photo = self.photo_manager.get_current_photo()

        if photo:
            # Update filename
            self.filename_label.setText(photo.base_name)

            # Update action indicator
            self.action_indicator.update_action(photo.action)

            # Update file status widget with action information
            self.file_status_widget.update_status(photo.has_jpeg, photo.has_raw, photo.action)

            # Update counter
            current, total = self.photo_manager.get_photo_count()
            self.counter_label.setText(f"{current} / {total}")

            # Update progress widget
            processed, total_photos, percentage = self.photo_manager.get_session_progress()
            self.progress_widget.update_progress(processed, total_photos)

            # Load and display image
            self._load_image(photo.display_path)

            # Preload adjacent images for faster navigation
            QTimer.singleShot(100, self._preload_adjacent_images)
        else:
            self._clear_display()

    def _clear_display(self):
        """Clear the display when no photo is available."""
        self.filename_label.setText("No file loaded")
        self.action_indicator.update_action(None)
        self.file_status_widget.update_status(False, False, None)
        self.counter_label.setText("0 / 0")
        self.progress_widget.update_progress(0, 0)
        self.image_label.clear()
        self.image_label.setText("No image loaded")
        self.current_pixmap = None

    def _get_exif_orientation(self, image_path: Path) -> int:
        """Get EXIF orientation value quickly without loading full image."""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                exif = img.getexif()
                if exif is not None:
                    # Orientation tag is 274 in EXIF
                    return exif.get(274, 1)
        except:
            pass
        return 1  # Default orientation (no rotation)

    def _apply_orientation_transform(self, pixmap: QPixmap, orientation: int) -> QPixmap:
        """Apply rotation transform based on EXIF orientation."""
        if orientation == 1:
            return pixmap  # No rotation needed

        transform = QTransform()

        if orientation == 3:
            transform.rotate(180)
        elif orientation == 6:
            transform.rotate(90)
        elif orientation == 8:
            transform.rotate(-90)
        elif orientation == 2:
            transform.scale(-1, 1)  # Horizontal flip
        elif orientation == 4:
            transform.scale(1, -1)  # Vertical flip
        elif orientation == 5:
            transform.rotate(90)
            transform.scale(-1, 1)
        elif orientation == 7:
            transform.rotate(-90)
            transform.scale(-1, 1)

        return pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)

    def _load_image(self, image_path: Path):
        """Load and display an image with optimized caching and orientation."""
        # Check cache first
        cache_key = str(image_path)
        if cache_key in self.image_cache:
            self.current_pixmap = self.image_cache[cache_key]
            self._update_image_display()
            return

        try:
            # Load image directly with QPixmap (fastest method)
            pixmap = QPixmap(str(image_path))

            if pixmap.isNull():
                raise Exception("Failed to load image with QPixmap")

            # Check if we need orientation correction (only for JPEG files)
            if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                orientation = self._get_exif_orientation(image_path)
                if orientation != 1:
                    pixmap = self._apply_orientation_transform(pixmap, orientation)

            self.current_pixmap = pixmap

            # Add to cache (remove oldest if cache is full)
            if len(self.image_cache) >= self.cache_size_limit:
                # Remove oldest entry
                oldest_key = next(iter(self.image_cache))
                del self.image_cache[oldest_key]

            self.image_cache[cache_key] = pixmap
            self._update_image_display()

        except Exception as e:
            # Fallback to PIL method for problematic files
            try:
                with Image.open(image_path) as img:
                    # Use PIL's exif_transpose for complex cases
                    img = ImageOps.exif_transpose(img)

                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGB')

                    # Convert to QPixmap more efficiently
                    from io import BytesIO
                    temp_buffer = BytesIO()
                    img.save(temp_buffer, format='PNG', optimize=True)
                    temp_buffer.seek(0)

                    pixmap = QPixmap()
                    if pixmap.loadFromData(temp_buffer.getvalue()):
                        self.current_pixmap = pixmap
                        # Cache the result
                        if len(self.image_cache) >= self.cache_size_limit:
                            oldest_key = next(iter(self.image_cache))
                            del self.image_cache[oldest_key]
                        self.image_cache[cache_key] = pixmap
                        self._update_image_display()
                    else:
                        raise Exception("Failed to convert PIL image to QPixmap")

            except Exception as fallback_error:
                self.image_label.setText(f"Error loading image: {str(e)}")
                self.current_pixmap = None

    def _update_image_display(self):
        """Update the image display with proper scaling."""
        if self.current_pixmap:
            # Scale image to fit the label while maintaining aspect ratio
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def _delayed_image_update(self):
        """Delayed image update to prevent too frequent resizing."""
        self._update_image_display()

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        if self.current_pixmap:
            self.resize_timer.start(100)  # Delay 100ms before updating

    def _update_button_states(self):
        """Update button enabled/disabled states."""
        photo = self.photo_manager.get_current_photo()
        has_photos = photo is not None
        has_pending = self.pending_action is not None

        # All action buttons are always enabled when photos are available
        # Users can take new actions even during countdowns
        self.keep_all_btn.setEnabled(has_photos)
        self.skip_btn.setEnabled(has_photos)
        self.delete_raw_btn.setEnabled(has_photos and photo.has_raw if photo else False)
        self.delete_all_btn.setEnabled(has_photos)

        # Navigation buttons are disabled during pending actions to prevent confusion
        current, total = self.photo_manager.get_photo_count()
        self.prev_btn.setEnabled(current > 1 and not has_pending)
        self.next_btn.setEnabled(current < total and not has_pending)

    def _start_pending_action(self, action_type: str, description: str, action_func: Callable):
        """Start a pending action with countdown confirmation."""
        photo = self.photo_manager.get_current_photo()
        if not photo:
            return
            
        # Cancel any existing pending action
        if self.pending_action:
            self.countdown_widget._cancel_action()
        
        # Store current index to return to if cancelled
        current_index = self.photo_manager.current_index
        
        # Create pending action
        self.pending_action = PendingAction(
            action_type=action_type,
            photo=photo,
            description=description,
            action_func=action_func,
            previous_index=current_index
        )
        
        # Start countdown
        self.countdown_widget.start_countdown(self.pending_action)
        
        # Immediately move to next photo (bypassing the pending action check)
        if self.photo_manager.move_to_next():
            self._update_display()
        
        self._update_button_states()
    
    def _execute_pending_action(self):
        """Execute the pending action after countdown finishes or immediately when called."""
        if not self.pending_action:
            return
            
        # Stop the countdown timer and hide the widget
        self.countdown_widget.timer.stop()
        self.countdown_widget.hide()
            
        # Execute the action
        self.pending_action.action_func()
        
        # Clear pending action
        self.pending_action = None
        self._update_button_states()
    
    def _cancel_pending_action(self):
        """Cancel the pending action and return to previous photo."""
        if not self.pending_action:
            return
            
        # Return to the photo that had the pending action
        self.photo_manager.current_index = self.pending_action.previous_index
        self._update_display()
        
        # Clear pending action
        self.pending_action = None
        self._update_button_states()

    def _keep_all_files(self):
        """Keep all files for current photo - immediate action."""
        photo = self.photo_manager.get_current_photo()
        if photo:
            # If there's a pending action, execute it immediately before this action
            if self.pending_action:
                self._execute_pending_action()
            
            # Execute immediately - no countdown needed for non-destructive action
            self.photo_manager.keep_both_files(photo)
            
            # Move to next photo
            if self.photo_manager.move_to_next():
                self._update_display()
            self._update_button_states()

    def _skip_photo(self):
        """Skip current photo (mark as reviewed without action) - immediate action."""
        photo = self.photo_manager.get_current_photo()
        if photo:
            # If there's a pending action, execute it immediately before this action
            if self.pending_action:
                self._execute_pending_action()
            
            # Execute immediately - no countdown needed for non-destructive action
            photo.set_action(PhotoAction.SKIPPED)
            self.photo_manager._save_session_data()
            self.photo_manager.session_updated.emit()
            
            # Move to next photo
            if self.photo_manager.move_to_next():
                self._update_display()
            self._update_button_states()

    def _delete_raw_file(self):
        """Delete RAW file for current photo."""
        photo = self.photo_manager.get_current_photo()
        if not photo or not photo.has_raw:
            return

        # If there's a pending action, execute it immediately before starting new countdown
        if self.pending_action:
            self._execute_pending_action()

        def execute_delete_raw():
            self.photo_manager.delete_raw_only(photo)
        
        self._start_pending_action(
            "delete_raw",
            f"Deleting RAW file for {photo.base_name}",
            execute_delete_raw
        )

    def _delete_all_files(self):
        """Delete all files for current photo."""
        photo = self.photo_manager.get_current_photo()
        if not photo:
            return

        # If there's a pending action, execute it immediately before starting new countdown
        if self.pending_action:
            self._execute_pending_action()

        def execute_delete_all():
            if self.photo_manager.delete_both_files(photo):
                self.photo_manager.remove_current_photo_from_list()
                self._update_display()
                self._update_button_states()
        
        self._start_pending_action(
            "delete_all",
            f"Deleting ALL files for {photo.base_name}",
            execute_delete_all
        )

    def _next_photo(self):
        """Move to next photo."""
        # Don't allow manual navigation if there's a pending action
        if self.pending_action:
            return
            
        if self.photo_manager.move_to_next():
            self._update_display()
            self._update_button_states()

    def _previous_photo(self):
        """Move to previous photo."""
        # Don't allow manual navigation if there's a pending action
        if self.pending_action:
            return
            
        if self.photo_manager.move_to_previous():
            self._update_display()
            self._update_button_states()

    def _toggle_confirmation(self):
        """Toggle deletion confirmation setting."""
        self.confirm_deletions = self.confirm_action.isChecked()

    def _clear_image_cache(self):
        """Clear the image cache to free memory."""
        self.image_cache.clear()

    def _preload_adjacent_images(self):
        """Preload next and previous images for faster navigation."""
        current_photo = self.photo_manager.get_current_photo()
        if not current_photo:
            return

        # Preload next image
        if self.photo_manager.current_index < len(self.photo_manager.photo_pairs) - 1:
            next_photo = self.photo_manager.photo_pairs[self.photo_manager.current_index + 1]
            if next_photo.display_path:
                self._preload_image(next_photo.display_path)

        # Preload previous image
        if self.photo_manager.current_index > 0:
            prev_photo = self.photo_manager.photo_pairs[self.photo_manager.current_index - 1]
            if prev_photo.display_path:
                self._preload_image(prev_photo.display_path)

    def _preload_image(self, image_path: Path):
        """Preload an image into cache without displaying it."""
        cache_key = str(image_path)
        if cache_key in self.image_cache:
            return  # Already cached

        try:
            # Load quickly in background
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                # Apply orientation if needed
                if image_path.suffix.lower() in ['.jpg', '.jpeg']:
                    orientation = self._get_exif_orientation(image_path)
                    if orientation != 1:
                        pixmap = self._apply_orientation_transform(pixmap, orientation)

                # Add to cache if there's space
                if len(self.image_cache) < self.cache_size_limit:
                    self.image_cache[cache_key] = pixmap
        except:
            pass  # Ignore preload errors

    def _on_folder_dropped(self, folder_path: str):
        """Handle folder dropped onto the image area."""
        self.photo_manager.load_folder(folder_path)

    def _set_app_icon(self):
        """Set the application icon with proper multi-platform support."""
        assets_dir = Path(__file__).parent.parent / "assets"

        try:
            # Try platform-specific icon formats first
            if sys.platform == "darwin":  # macOS
                # Use the .icns file for best quality on macOS
                icns_path = assets_dir / "PhotoSift.icns"
                if icns_path.exists():
                    icon = QIcon(str(icns_path))
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        app = QApplication.instance()
                        if app:
                            app.setWindowIcon(icon)
                        return

                # Fallback to individual PNG files for macOS
                icon = QIcon()
                for size in [16, 32, 64, 128, 256, 512]:
                    png_path = assets_dir / f"icon-{size}.png"
                    if png_path.exists():
                        icon.addFile(str(png_path), QSize(size, size))

                if not icon.isNull():
                    self.setWindowIcon(icon)
                    app = QApplication.instance()
                    if app:
                        app.setWindowIcon(icon)
                    return

            else:  # Windows, Linux, and other platforms
                # Use individual PNG files for better control
                icon = QIcon()

                if sys.platform == "win32":  # Windows
                    sizes = [16, 20, 24, 32, 48, 64, 128, 256]
                else:  # Linux and others
                    sizes = [16, 24, 32, 48, 64, 128, 256]

                for size in sizes:
                    png_path = assets_dir / f"icon-{size}.png"
                    if png_path.exists():
                        icon.addFile(str(png_path), QSize(size, size))

                if not icon.isNull():
                    self.setWindowIcon(icon)
                    app = QApplication.instance()
                    if app:
                        app.setWindowIcon(icon)
                    return

            # Final fallback to the original 512px icon
            fallback_path = assets_dir / "icon-512.png"
            if fallback_path.exists():
                icon = QIcon(str(fallback_path))
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    app = QApplication.instance()
                    if app:
                        app.setWindowIcon(icon)

        except Exception as e:
            # Silent fallback - don't show errors for missing icons
            pass
