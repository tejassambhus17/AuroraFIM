"""
Modern UI Components for AuroraFIM
Reusable components with modern design and animations.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer, QRect
from PySide6.QtSvg import QSvgWidget
import os


class ModernCard(QFrame):
    """Modern card component with shadow and rounded corners."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border-radius: 8px;
                border: 1px solid palette(dark);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.setLayout(layout)


class ModernButton(QPushButton):
    """Modern button with hover effects."""
    
    def __init__(self, text: str = "", icon: QIcon = None, parent=None):
        super().__init__(text, parent)
        if icon:
            self.setIcon(icon)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setMinimumWidth(80)


class StatusBadge(QLabel):
    """Status badge component with color indicators."""
    
    class Status:
        SECURE = ("#10B981", "Secure")       # Green
        VERIFYING = ("#F59E0B", "Verifying") # Amber
        COMPROMISED = ("#EF4444", "Compromised") # Red
        UNKNOWN = ("#6B7280", "Unknown")     # Gray
    
    def __init__(self, status: str = "unknown", parent=None):
        super().__init__(parent)
        self.set_status(status)
        self.setStyleSheet("""
            QLabel {
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }
        """)
    
    def set_status(self, status: str):
        """Set badge status."""
        statuses = {
            "secure": self.Status.SECURE,
            "verifying": self.Status.VERIFYING,
            "compromised": self.Status.COMPROMISED,
            "unknown": self.Status.UNKNOWN,
        }
        
        color, text = statuses.get(status.lower(), self.Status.UNKNOWN)
        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}22;
                color: {color};
                border: 1px solid {color};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }}
        """)


class SectionHeader(QLabel):
    """Section header with modern styling."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)
        self.setContentsMargins(0, 16, 0, 8)


class InfoBox(QFrame):
    """Information box with icon and text."""
    
    def __init__(self, title: str = "", message: str = "", box_type: str = "info", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: palette(alternate-base);
                border-radius: 6px;
                border-left: 4px solid {self._get_color(box_type)};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-weight: 600; font-size: 12px;")
            layout.addWidget(title_label)
        
        if message:
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet("font-size: 11px; color: palette(mid);")
            layout.addWidget(msg_label)
    
    @staticmethod
    def _get_color(box_type: str) -> str:
        """Get color for box type."""
        colors = {
            "info": "#3B82F6",      # Blue
            "success": "#10B981",   # Green
            "warning": "#F59E0B",   # Amber
            "error": "#EF4444",     # Red
        }
        return colors.get(box_type, colors["info"])


class FadeInEffect(QGraphicsOpacityEffect):
    """Fade in animation effect."""
    
    def __init__(self, widget: QWidget, duration: int = 300):
        super().__init__(widget)
        self.widget = widget
        self.setOpacity(0)
        self.widget.setGraphicsEffect(self)
        
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def start(self):
        """Start fade in animation."""
        self.animation.start()


class SlideInEffect:
    """Slide in animation effect."""
    
    def __init__(self, widget: QWidget, direction: str = "left", duration: int = 300):
        self.widget = widget
        self.direction = direction
        self.duration = duration
    
    def start(self):
        """Start slide in animation."""
        # Get current geometry
        widget_rect = self.widget.geometry()
        start_pos = self._get_start_position(widget_rect)
        end_pos = widget_rect.topLeft()
        
        # Create animation
        self.animation = QPropertyAnimation(self.widget, b"pos")
        self.animation.setDuration(self.duration)
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
    
    def _get_start_position(self, rect: QRect):
        """Get starting position based on direction."""
        if self.direction == "left":
            return rect.topLeft() + Qt.QPoint(-rect.width(), 0)
        elif self.direction == "right":
            return rect.topLeft() + Qt.QPoint(rect.width(), 0)
        elif self.direction == "top":
            return rect.topLeft() + Qt.QPoint(0, -rect.height())
        elif self.direction == "bottom":
            return rect.topLeft() + Qt.QPoint(0, rect.height())
        return rect.topLeft()


class AnimatedCounter(QLabel):
    """Number counter with animation."""
    
    def __init__(self, start: int = 0, end: int = 100, duration: int = 500, parent=None):
        super().__init__(str(start), parent)
        self.start_value = start
        self.end_value = end
        
        self.animation = QPropertyAnimation(self, b"counter_value")
        self.animation.setDuration(duration)
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def set_counter_value(self, value: int):
        """Set counter value."""
        self.setText(str(int(value)))
    
    counter_value = property(fget=lambda self: int(self.text()), 
                             fset=set_counter_value)
    
    def start_animation(self):
        """Start counter animation."""
        self.animation.start()


class StatCard(ModernCard):
    """Stat card displaying key information."""
    
    def __init__(self, title: str = "", value: str = "", 
                 subtitle: str = "", icon: QIcon = None, parent=None):
        super().__init__(parent)
        
        layout = self.layout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(24, 24))
            header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: palette(mid);")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        layout.addWidget(value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("font-size: 10px; color: palette(mid);")
            layout.addWidget(subtitle_label)


class DashboardView(QWidget):
    """Modern dashboard view layout."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        self.setLayout(self.main_layout)
    
    def add_section(self, title: str) -> QVBoxLayout:
        """Add a new section to dashboard."""
        section_layout = QVBoxLayout()
        
        # Section header
        header = SectionHeader(title)
        section_layout.addWidget(header)
        
        # Section content area
        content_frame = ModernCard()
        content_layout = content_frame.layout()
        section_layout.addWidget(content_frame)
        
        self.main_layout.addLayout(section_layout)
        return content_layout
    
    def add_stretch(self):
        """Add stretch to push content to top."""
        self.main_layout.addStretch()
