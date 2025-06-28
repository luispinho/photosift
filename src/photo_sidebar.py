"""
Photo Sidebar - A collapsible sidebar showing photo list with action indicators
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QFrame, QSizePolicy,
    QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont

from .photo_manager import PhotoManager, PhotoPair, PhotoAction


class ActionIndicatorIcon(QWidget):
    """Small colored circle indicating photo action status."""

    ACTION_COLORS = {
        PhotoAction.NONE: "#6b7280",          # Gray - unprocessed
        PhotoAction.KEEP_ALL: "#10b981",      # Green - keep all
        PhotoAction.DELETE_RAW: "#f59e0b",    # Orange - delete raw
        PhotoAction.DELETE_ALL: "#ef4444",   # Red - delete all
        PhotoAction.SKIPPED: "#8b5cf6",      # Purple - skipped
    }

    def __init__(self, action: PhotoAction = PhotoAction.NONE):
        super().__init__()
        self.action = action
        self.setFixedSize(12, 12)

    def set_action(self, action: PhotoAction):
        """Update the action and repaint."""
        self.action = action
        self.update()

    def paintEvent(self, event):
        """Paint the colored circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(self.ACTION_COLORS[self.action])
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color))

        # Draw filled circle
        painter.drawEllipse(1, 1, 10, 10)


class PhotoListItem(QWidget):
    """Custom widget for photo list items with action indicator and name."""

    clicked = pyqtSignal(str)  # Emits photo base_name when clicked

    def __init__(self, photo: PhotoPair):
        super().__init__()
        self.photo = photo
        self.is_current = False
        self._setup_ui()

    def _setup_ui(self):
        """Set up the item UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Action indicator
        self.action_indicator = ActionIndicatorIcon(self.photo.action)
        layout.addWidget(self.action_indicator)

        # Photo name
        self.name_label = QLabel(self.photo.base_name)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.name_label, 1)

        # File status (JPEG, RAW, or both)
        status_text = ""
        if self.photo.has_jpeg and self.photo.has_raw:
            status_text = "J+R"
        elif self.photo.has_jpeg:
            status_text = "JPG"
        elif self.photo.has_raw:
            status_text = "RAW"

        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self.status_label)

        self._update_style()

    def update_action(self, action: PhotoAction):
        """Update the action indicator."""
        self.photo.action = action
        self.action_indicator.set_action(action)

    def set_current(self, is_current: bool):
        """Mark this item as the current photo."""
        self.is_current = is_current
        self._update_style()

    def _update_style(self):
        """Update the item styling based on current state."""
        if self.is_current:
            bg_color = "#2a2a2a"  # Subtle background
            border_color = "#404040"  # Subtle border
            text_color = "#ffffff"
            status_color = "#e0e0e0"
        else:
            bg_color = "transparent"
            border_color = "transparent"
            text_color = "#e0e0e0"
            status_color = "#9ca3af"

        self.setStyleSheet(f"""
            PhotoListItem {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                margin: 1px;
                padding: 4px;
            }}
            PhotoListItem:hover {{
                background-color: {"#374151" if not self.is_current else "#2a2a2a"};
                border-color: {"#4b5563" if not self.is_current else "#404040"};
            }}
        """)

        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 12px;
                font-weight: {"bold" if self.is_current else "normal"};
                background: transparent;
                border: none;
            }}
        """)

        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {status_color};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)

    def mousePressEvent(self, event):
        """Handle mouse clicks with button-like feedback."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.photo.base_name)
        super().mousePressEvent(event)


class PhotoSidebar(QWidget):
    """Collapsible sidebar showing photo list with action indicators and filtering."""

    photo_selected = pyqtSignal(str)  # Emits photo base_name when selected

    def __init__(self, photo_manager: PhotoManager):
        super().__init__()
        self.photo_manager = photo_manager
        self.photo_items: List[PhotoListItem] = []
        self.current_filter = None  # Start with "All Photos" (None means show all)
        self.is_collapsed = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the sidebar UI."""
        self.setFixedWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar content frame
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-right: 1px solid #404040;
            }
        """)
        layout.addWidget(self.content_frame)

        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # Header with collapse button
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("Photos")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #e0e0e0;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        content_layout.addWidget(header_frame)

        # Filter controls
        filter_frame = QFrame()
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(4)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("""
            QLabel {
                color: #9ca3af;
                font-size: 11px;
                background: transparent;
                border: none;
            }
        """)
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Photos", "ALL")  # Special string for all photos
        self.filter_combo.addItem("Unprocessed", PhotoAction.NONE)
        self.filter_combo.addItem("Keep All", PhotoAction.KEEP_ALL)
        self.filter_combo.addItem("Delete RAW", PhotoAction.DELETE_RAW)
        self.filter_combo.addItem("Delete All", PhotoAction.DELETE_ALL)
        self.filter_combo.addItem("Skipped", PhotoAction.SKIPPED)

        self.filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                color: #e0e0e0;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #e0e0e0;
            }
            QComboBox QAbstractItemView {
                background-color: #374151;
                color: #e0e0e0;
                selection-background-color: #2563eb;
                border: 1px solid #4b5563;
            }
        """)
        self.filter_combo.setToolTip("Filter photos by action status")
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)

        content_layout.addWidget(filter_frame)

        # Photo list scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4b5563;
            }
        """)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch()

        scroll_area.setWidget(self.list_widget)
        content_layout.addWidget(scroll_area, 1)

    def _connect_signals(self):
        """Connect photo manager signals."""
        self.photo_manager.photos_loaded.connect(self._on_photos_loaded)
        self.photo_manager.session_updated.connect(self._on_session_updated)

    def _toggle_collapse(self):
        """Toggle sidebar collapse state."""
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.setFixedWidth(32)
            self.content_frame.hide()
            self.collapse_btn.setText("▶")
            self.collapse_btn.setParent(self)
            self.collapse_btn.move(4, 8)
            self.collapse_btn.show()
        else:
            self.setFixedWidth(280)
            self.content_frame.show()
            self.collapse_btn.setText("◀")

    def _on_photos_loaded(self, count: int):
        """Handle photos loaded signal."""
        self._populate_photo_list()

    def _on_session_updated(self):
        """Handle session update signal."""
        self._update_action_indicators()

    def _populate_photo_list(self):
        """Populate the photo list."""
        # Clear existing items
        for item in self.photo_items:
            item.setParent(None)
        self.photo_items.clear()

        # Add new items
        for photo in self.photo_manager.photo_pairs:
            item = PhotoListItem(photo)
            item.clicked.connect(self._on_photo_clicked)
            self.photo_items.append(item)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)

        self._apply_filter()
        self._update_current_photo()

    def _on_photo_clicked(self, base_name: str):
        """Handle photo item click."""
        self.photo_selected.emit(base_name)

    def _on_filter_changed(self):
        """Handle filter change."""
        index = self.filter_combo.currentIndex()
        data = self.filter_combo.itemData(index)

        if data == "ALL":  # All Photos
            self.current_filter = None
        elif data == PhotoAction.NONE:  # Unprocessed
            self.current_filter = PhotoAction.NONE
        else:
            self.current_filter = data

        self._apply_filter()

    def _apply_filter(self):
        """Apply the current filter to the photo list."""
        for item in self.photo_items:
            if self.current_filter is None:
                # Show all
                item.show()
            elif self.current_filter == PhotoAction.NONE:
                # Show only unprocessed
                item.setVisible(item.photo.action == PhotoAction.NONE)
            else:
                # Show specific action
                item.setVisible(item.photo.action == self.current_filter)

    def _update_action_indicators(self):
        """Update action indicators for all items."""
        for item in self.photo_items:
            item.update_action(item.photo.action)
        self._apply_filter()

    def _scroll_to_current(self):
        """Scroll to make the current photo visible in the list."""
        current_photo = self.photo_manager.get_current_photo()
        if not current_photo:
            return

        # Find the current photo item
        current_item = None
        for item in self.photo_items:
            if item.photo.base_name == current_photo.base_name and item.isVisible():
                current_item = item
                break

        if current_item:
            # Use QTimer to ensure the layout is updated before scrolling
            QTimer.singleShot(10, lambda: self._scroll_to_widget(current_item))

    def _scroll_to_widget(self, widget):
        """Scroll to make a specific widget visible."""
        # Find the scroll area
        scroll_area = None
        parent = self.list_widget.parent()
        while parent and not isinstance(parent, QScrollArea):
            parent = parent.parent()

        if isinstance(parent, QScrollArea):
            scroll_area = parent

            # Calculate the position to scroll to
            widget_pos = widget.mapTo(self.list_widget, widget.rect().topLeft())
            widget_height = widget.height()
            viewport_height = scroll_area.viewport().height()

            # Get current scroll position
            scrollbar = scroll_area.verticalScrollBar()
            current_value = scrollbar.value()

            # Calculate target scroll position (center the widget in view)
            target_y = widget_pos.y() - (viewport_height - widget_height) // 2
            target_value = max(0, min(target_y, scrollbar.maximum()))

            # Smooth scroll to target
            scrollbar.setValue(target_value)

    def _update_current_photo(self):
        """Update which photo is marked as current."""
        current_photo = self.photo_manager.get_current_photo()
        for item in self.photo_items:
            item.set_current(current_photo and item.photo.base_name == current_photo.base_name)
        self._scroll_to_current()

    def set_current_photo(self, base_name: str, auto_scroll: bool = False):
        """Set the current photo by base name.

        Args:
            base_name: The base name of the photo to set as current
            auto_scroll: Whether to automatically scroll to the photo (only for session resume)
        """
        for item in self.photo_items:
            item.set_current(item.photo.base_name == base_name)

        if auto_scroll:
            self._scroll_to_current()
