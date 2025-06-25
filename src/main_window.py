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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSignal as Signal, QUrl, QSize
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QAction, QTransform, QDragEnterEvent, QDropEvent, QIcon, QPainter, QFont, QColor
from PIL import Image, ImageOps

from .photo_manager import PhotoManager, PhotoPair


class FileStatusWidget(QWidget):
    """Modern visual file status indicator showing JPEG and RAW presence."""
    
    def __init__(self):
        super().__init__()
        self.has_jpeg = False
        self.has_raw = False
        self.setFixedSize(140, 32)
        self.setStyleSheet("background: transparent;")
        self.setToolTip("File format indicators")
    
    def update_status(self, has_jpeg: bool, has_raw: bool):
        """Update the file status and trigger a repaint."""
        self.has_jpeg = has_jpeg
        self.has_raw = has_raw
        self.update()  # Trigger paintEvent
        
        # Update tooltip based on current status
        if has_jpeg and has_raw:
            self.setToolTip("Both JPEG and RAW files present")
        elif has_jpeg:
            self.setToolTip("JPEG file only")
        elif has_raw:
            self.setToolTip("RAW file only")
        else:
            self.setToolTip("No files present")
    
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
        indicator_height = self.height()
        
        # JPEG indicator
        jpeg_rect = self.rect().adjusted(0, 0, -indicator_width - spacing, 0)
        if self.has_jpeg:
            # Active state - filled with modern green and subtle shadow
            # First draw a subtle shadow/glow
            shadow_rect = jpeg_rect.adjusted(-1, 1, 1, 1)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(16, 185, 129, 30))  # Semi-transparent green
            painter.drawRoundedRect(shadow_rect, 6, 6)
            
            # Then draw the main indicator
            painter.setBrush(QColor("#10b981"))  # Emerald green
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
            # First draw a subtle shadow/glow
            shadow_rect = raw_rect.adjusted(-1, 1, 1, 1)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(245, 158, 11, 30))  # Semi-transparent amber
            painter.drawRoundedRect(shadow_rect, 6, 6)
            
            # Then draw the main indicator
            painter.setBrush(QColor("#f59e0b"))  # Amber
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


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.photo_manager = PhotoManager()
        self.current_pixmap: Optional[QPixmap] = None
        self.confirm_deletions = True  # Default to requiring confirmation
        
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
        info_layout.setContentsMargins(12, 8, 12, 8)
        
        # File name label
        self.filename_label = QLabel("No file loaded")
        self.filename_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e0e0e0; background: transparent; border: none;")
        info_layout.addWidget(self.filename_label)
        
        info_layout.addStretch()
        
        # File status widget (modern visual indicator)
        self.file_status_widget = FileStatusWidget()
        info_layout.addWidget(self.file_status_widget)
        
        main_layout.addWidget(info_panel)
        
        # Image display area
        self.image_label = ImageLabel()
        main_layout.addWidget(self.image_label)
        
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
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Open a folder to begin")
        
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
        QShortcut(QKeySequence("R"), self, self._delete_raw_file)
        QShortcut(QKeySequence("D"), self, self._delete_all_files)
        
        # Navigation shortcuts
        QShortcut(QKeySequence("Left"), self, self._previous_photo)
        QShortcut(QKeySequence("Right"), self, self._next_photo)
        QShortcut(QKeySequence("Space"), self, self._next_photo)
    
    def _connect_signals(self):
        """Connect PhotoManager signals to UI updates."""
        self.photo_manager.photos_loaded.connect(self._on_photos_loaded)
        self.photo_manager.photo_deleted.connect(self._on_photo_deleted)
        self.photo_manager.error_occurred.connect(self._on_error)
        
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
    
    def _update_display(self):
        """Update the photo display and info."""
        photo = self.photo_manager.get_current_photo()
        
        if photo:
            # Update filename
            self.filename_label.setText(photo.base_name)
            
            # Update file status widget
            self.file_status_widget.update_status(photo.has_jpeg, photo.has_raw)
            
            # Update counter
            current, total = self.photo_manager.get_photo_count()
            self.counter_label.setText(f"{current} / {total}")
            
            # Load and display image
            self._load_image(photo.display_path)
            
            # Preload adjacent images for faster navigation
            QTimer.singleShot(100, self._preload_adjacent_images)
        else:
            self._clear_display()
    
    def _clear_display(self):
        """Clear the display when no photo is available."""
        self.filename_label.setText("No file loaded")
        self.file_status_widget.update_status(False, False)
        self.counter_label.setText("0 / 0")
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
        
        # Action buttons
        self.keep_all_btn.setEnabled(has_photos)
        self.delete_raw_btn.setEnabled(has_photos and photo.has_raw if photo else False)
        self.delete_all_btn.setEnabled(has_photos)
        
        # Navigation buttons
        current, total = self.photo_manager.get_photo_count()
        self.prev_btn.setEnabled(current > 1)
        self.next_btn.setEnabled(current < total)
    
    def _keep_all_files(self):
        """Keep all files for current photo."""
        photo = self.photo_manager.get_current_photo()
        if photo:
            self.photo_manager.keep_both_files(photo)
            self._next_photo()
    
    def _delete_raw_file(self):
        """Delete RAW file for current photo."""
        photo = self.photo_manager.get_current_photo()
        if not photo or not photo.has_raw:
            return
        
        if self._confirm_deletion(f"Delete RAW file for {photo.base_name}?"):
            if self.photo_manager.delete_raw_only(photo):
                self._next_photo()
    
    def _delete_all_files(self):
        """Delete all files for current photo."""
        photo = self.photo_manager.get_current_photo()
        if not photo:
            return
        
        if self._confirm_deletion(f"Delete ALL files for {photo.base_name}?"):
            if self.photo_manager.delete_both_files(photo):
                self.photo_manager.remove_current_photo_from_list()
                self._update_display()
                self._update_button_states()
    
    def _confirm_deletion(self, message: str) -> bool:
        """Show confirmation dialog if enabled."""
        if not self.confirm_deletions:
            return True
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        return reply == QMessageBox.StandardButton.Yes
    
    def _next_photo(self):
        """Move to next photo."""
        if self.photo_manager.move_to_next():
            self._update_display()
            self._update_button_states()
    
    def _previous_photo(self):
        """Move to previous photo."""
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
