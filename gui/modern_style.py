"""
Modern UI Styling Module for AuroraFIM
Professional design system with dark/light themes, animations, and accessibility.
"""

from PySide6.QtGui import QFont, QPalette, QColor, QBrush, QLinearGradient, QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtWidgets import QApplication
import os


class ModernColors:
    """Modern color palettes for AuroraFIM."""
    
    class Dark:
        """Dark theme colors - Professional & Modern."""
        # Primary colors
        BACKGROUND = "#0B1220"
        SURFACE = "#111C2E"
        SURFACE_VARIANT = "#1A2940"
        
        # Text colors
        TEXT_PRIMARY = "#E6EDF7"
        TEXT_SECONDARY = "#B6C2D9"
        TEXT_TERTIARY = "#8090AA"
        
        # Accent colors
        PRIMARY = "#1D9BF0"
        PRIMARY_LIGHT = "#49B3F5"
        SUCCESS = "#22C55E"
        WARNING = "#F59E0B"
        ERROR = "#EF4444"
        INFO = "#38BDF8"
        
        # Semantic colors
        BORDER = "#233651"
        DIVIDER = "#2C4362"
        HOVER = "#1D2E48"
        
        # Gradient
        GRADIENT_PRIMARY = "#1D9BF0"
        GRADIENT_SECONDARY = "#137CC3"
    
    class Light:
        """Light theme colors - Clean & Bright."""
        # Primary colors
        BACKGROUND = "#F3F6FB"
        SURFACE = "#FFFFFF"
        SURFACE_VARIANT = "#EAF0F8"
        
        # Text colors
        TEXT_PRIMARY = "#0F172A"
        TEXT_SECONDARY = "#334155"
        TEXT_TERTIARY = "#64748B"
        
        # Accent colors
        PRIMARY = "#0F6CBD"
        PRIMARY_LIGHT = "#1D87E0"
        SUCCESS = "#15803D"
        WARNING = "#B45309"
        ERROR = "#B91C1C"
        INFO = "#0369A1"
        
        # Semantic colors
        BORDER = "#D5E0EE"
        DIVIDER = "#C0D0E5"
        HOVER = "#E7EEF8"
        
        # Gradient
        GRADIENT_PRIMARY = "#0F6CBD"
        GRADIENT_SECONDARY = "#0B5EA7"


class ModernStylesheet:
    """Generate modern stylesheets for AuroraFIM."""

    @staticmethod
    def get_palette(dark_mode: bool = True) -> QPalette:
        """Build a Qt palette to align native widgets with stylesheet colors."""
        c = ModernColors.Dark if dark_mode else ModernColors.Light
        p = QPalette()
        p.setColor(QPalette.Window, QColor(c.BACKGROUND))
        p.setColor(QPalette.WindowText, QColor(c.TEXT_PRIMARY))
        p.setColor(QPalette.Base, QColor(c.SURFACE))
        p.setColor(QPalette.AlternateBase, QColor(c.SURFACE_VARIANT))
        p.setColor(QPalette.ToolTipBase, QColor(c.SURFACE))
        p.setColor(QPalette.ToolTipText, QColor(c.TEXT_PRIMARY))
        p.setColor(QPalette.Text, QColor(c.TEXT_PRIMARY))
        p.setColor(QPalette.Button, QColor(c.SURFACE))
        p.setColor(QPalette.ButtonText, QColor(c.TEXT_PRIMARY))
        p.setColor(QPalette.Highlight, QColor(c.PRIMARY))
        p.setColor(QPalette.HighlightedText, QColor("#FFFFFF" if dark_mode else "#F8FAFC"))
        p.setColor(QPalette.BrightText, QColor(c.ERROR))
        return p
    
    @staticmethod
    def get_dark_stylesheet() -> str:
        """Get dark theme stylesheet."""
        return f"""
        /* Main Window & Dialog */
        QMainWindow, QDialog {{
            background-color: {ModernColors.Dark.BACKGROUND};
            color: {ModernColors.Dark.TEXT_PRIMARY};
        }}
        
        /* Central Widget */
        QWidget {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
        }}

        QAbstractScrollArea {{
            background-color: {ModernColors.Dark.SURFACE};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 12px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 12px;
            background-color: {ModernColors.Dark.BACKGROUND};
            padding: 10px;
        }}
        
        QTabBar::tab {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_SECONDARY};
            padding: 10px 18px;
            margin-right: 6px;
            border: none;
            border-radius: 10px;
            border-bottom: 2px solid transparent;
            font-weight: 500;
            font-size: 12px;
        }}
        
        QTabBar::tab:hover {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
            color: {ModernColors.Dark.TEXT_PRIMARY};
        }}
        
        QTabBar::tab:selected {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
            color: {ModernColors.Dark.PRIMARY};
            border-bottom: 2px solid {ModernColors.Dark.PRIMARY};
            font-weight: 700;
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {ModernColors.Dark.SURFACE};
            border-bottom: 1px solid {ModernColors.Dark.BORDER};
            spacing: 10px;
            padding: 10px;
        }}
        
        QToolButton {{
            background-color: transparent;
            color: {ModernColors.Dark.TEXT_PRIMARY};
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid transparent;
            font-weight: 500;
            font-size: 11px;
        }}
        
        QToolButton:hover {{
            background-color: {ModernColors.Dark.HOVER};
            border: 1px solid {ModernColors.Dark.BORDER};
        }}
        
        QToolButton:pressed {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border-top: 1px solid {ModernColors.Dark.BORDER};
        }}
        
        QStatusBar::item {{
            border: none;
            padding: 4px 8px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {ModernColors.Dark.PRIMARY};
            color: white;
            border: none;
            padding: 9px 16px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 12px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {ModernColors.Dark.PRIMARY_LIGHT};
        }}
        
        QPushButton:pressed {{
            background-color: {ModernColors.Dark.GRADIENT_SECONDARY};
        }}

        QPushButton#UbaRecalculateButton {{
            background-color: {ModernColors.Dark.WARNING};
        }}

        QPushButton#UbaRecalculateButton:hover {{
            background-color: #f7b843;
        }}

        QPushButton#UbaRefreshButton {{
            background-color: {ModernColors.Dark.INFO};
        }}

        QPushButton#UbaRefreshButton:hover {{
            background-color: #5cc7f2;
        }}
        
        QPushButton:disabled {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
            color: {ModernColors.Dark.TEXT_TERTIARY};
        }}
        
        /* Line Edits */
        QLineEdit, QPlainTextEdit {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 11px;
            selection-background-color: {ModernColors.Dark.PRIMARY};
        }}
        
        QLineEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {ModernColors.Dark.PRIMARY};
            outline: none;
        }}
        
        QLineEdit:hover, QPlainTextEdit:hover {{
            border: 1px solid {ModernColors.Dark.DIVIDER};
        }}
        
        /* Combo Box */
        QComboBox {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 11px;
        }}
        
        QComboBox:focus {{
            border: 1px solid {ModernColors.Dark.PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            background-color: transparent;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            width: 8px;
            height: 8px;
        }}
        
        /* Table Widget */
        QTableWidget, QTableView {{
            background-color: {ModernColors.Dark.BACKGROUND};
            alternate-background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            gridline-color: {ModernColors.Dark.BORDER};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 12px;
        }}

        /* Dashboard Cards */
        #RiskSummaryFrame,
        #BehaviorVisualizationFrame,
        #IntegrityBadgeFrame,
        #QuickActionsFrame,
        #RecentEventsFrame {{
            background-color: {ModernColors.Dark.SURFACE};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 14px;
        }}

        #RiskSummaryTitle,
        #RecentEventsTitleLabel,
        #QuickActionsTitle,
        #IntegrityStatusLabel {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            font-weight: 700;
            letter-spacing: 0.3px;
        }}

        #UbaDashboardTitle,
        #UbaBaselineTitle,
        #BehaviorChartsTitle {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            font-weight: 700;
        }}

        #UbaRecalculateButton,
        #UbaRefreshButton {{
            padding-left: 14px;
            padding-right: 14px;
        }}

        #WelcomeUserBadge {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 600;
            background-color: transparent;
            border: none;
            padding: 0px;
        }}

        #LoginDialog,
        #CreateUserDialog {{
            background-color: {ModernColors.Dark.SURFACE};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 14px;
        }}

        #LoginTitle,
        #CreateUserTitle {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            font-weight: 800;
            font-size: 20px;
        }}

        #LoginSubtitle,
        #CreateUserSubtitle {{
            color: {ModernColors.Dark.TEXT_SECONDARY};
            font-size: 12px;
        }}

        #PrimaryActionButton {{
            background-color: {ModernColors.Dark.PRIMARY};
        }}

        #PrimaryActionButton:hover {{
            background-color: {ModernColors.Dark.PRIMARY_LIGHT};
        }}

        #SecondaryActionButton {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
        }}

        #SecondaryActionButton:hover {{
            background-color: {ModernColors.Dark.HOVER};
        }}

        #DangerActionButton {{
            background-color: {ModernColors.Dark.ERROR};
        }}

        #DangerActionButton:hover {{
            background-color: #f06565;
        }}

        #SectionSubtitle {{
            color: {ModernColors.Dark.TEXT_TERTIARY};
            font-size: 11px;
        }}

        #FormLabel {{
            color: {ModernColors.Dark.TEXT_SECONDARY};
            background: transparent;
            font-weight: 600;
        }}

        #DialogInput {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 8px;
            padding: 8px 10px;
        }}

        #DialogInput:focus {{
            border: 1px solid {ModernColors.Dark.PRIMARY};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {ModernColors.Dark.PRIMARY};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {ModernColors.Dark.SURFACE_VARIANT};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            padding: 8px;
            border-right: 1px solid {ModernColors.Dark.BORDER};
            border-bottom: 1px solid {ModernColors.Dark.BORDER};
            font-weight: 600;
            font-size: 11px;
        }}
        
        /* Labels */
        QLabel {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            font-size: 11px;
        }}
        
        /* Group Box */
        QGroupBox {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
            font-weight: 600;
            font-size: 12px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }}
        
        /* Scrollbar */
        QScrollBar:vertical {{
            background-color: {ModernColors.Dark.BACKGROUND};
            width: 10px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {ModernColors.Dark.DIVIDER};
            border-radius: 5px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {ModernColors.Dark.BORDER};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            background: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {ModernColors.Dark.BACKGROUND};
            height: 10px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {ModernColors.Dark.DIVIDER};
            border-radius: 5px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {ModernColors.Dark.BORDER};
        }}
        
        /* Menu & Context Menu */
        QMenu {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
            padding: 4px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {ModernColors.Dark.PRIMARY};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {ModernColors.Dark.DIVIDER};
            margin: 4px 0;
        }}
        
        /* Dialog */
        QDialog {{
            background-color: {ModernColors.Dark.SURFACE};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 12px;
        }}

        QMessageBox {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
        }}

        QMessageBox QLabel {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            background: transparent;
        }}

        QMessageBox QPushButton {{
            min-width: 90px;
        }}
        
        /* Checkbox */
        QCheckBox {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            spacing: 6px;
            font-size: 11px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 1px solid {ModernColors.Dark.BORDER};
            background-color: {ModernColors.Dark.SURFACE};
        }}
        
        QCheckBox::indicator:hover {{
            border: 1px solid {ModernColors.Dark.PRIMARY};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {ModernColors.Dark.PRIMARY};
            border: 1px solid {ModernColors.Dark.PRIMARY};
        }}
        
        /* Radio Button */
        QRadioButton {{
            color: {ModernColors.Dark.TEXT_PRIMARY};
            spacing: 6px;
            font-size: 11px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 1px solid {ModernColors.Dark.BORDER};
            background-color: {ModernColors.Dark.SURFACE};
        }}
        
        QRadioButton::indicator:hover {{
            border: 1px solid {ModernColors.Dark.PRIMARY};
        }}
        
        QRadioButton::indicator:checked {{
            border: 4px solid {ModernColors.Dark.PRIMARY};
            background-color: {ModernColors.Dark.SURFACE};
        }}
        
        /* Spin Box */
        QSpinBox, QDoubleSpinBox {{
            background-color: {ModernColors.Dark.SURFACE};
            color: {ModernColors.Dark.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Dark.BORDER};
            border-radius: 4px;
            padding: 6px;
            font-size: 11px;
        }}
        """
    
    @staticmethod
    def get_light_stylesheet() -> str:
        """Get light theme stylesheet."""
        return f"""
        /* Main Window & Dialog */
        QMainWindow, QDialog {{
            background-color: {ModernColors.Light.BACKGROUND};
            color: {ModernColors.Light.TEXT_PRIMARY};
        }}
        
        /* Central Widget */
        QWidget {{
            color: {ModernColors.Light.TEXT_PRIMARY};
        }}

        QAbstractScrollArea {{
            background-color: {ModernColors.Light.SURFACE};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 12px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 12px;
            background-color: {ModernColors.Light.BACKGROUND};
            padding: 10px;
        }}
        
        QTabBar::tab {{
            background-color: {ModernColors.Light.SURFACE};
            color: {ModernColors.Light.TEXT_SECONDARY};
            padding: 10px 18px;
            margin-right: 6px;
            border: none;
            border-radius: 10px;
            border-bottom: 2px solid transparent;
            font-weight: 500;
            font-size: 12px;
        }}
        
        QTabBar::tab:hover {{
            background-color: {ModernColors.Light.SURFACE_VARIANT};
            color: {ModernColors.Light.TEXT_PRIMARY};
        }}
        
        QTabBar::tab:selected {{
            background-color: {ModernColors.Light.SURFACE};
            color: {ModernColors.Light.PRIMARY};
            border-bottom: 2px solid {ModernColors.Light.PRIMARY};
            font-weight: 700;
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {ModernColors.Light.SURFACE};
            border-bottom: 1px solid {ModernColors.Light.BORDER};
            spacing: 10px;
            padding: 10px;
        }}
        
        QToolButton {{
            background-color: transparent;
            color: {ModernColors.Light.TEXT_PRIMARY};
            padding: 8px 14px;
            border-radius: 8px;
            border: 1px solid transparent;
            font-weight: 500;
            font-size: 11px;
        }}
        
        QToolButton:hover {{
            background-color: {ModernColors.Light.SURFACE_VARIANT};
            border: 1px solid {ModernColors.Light.BORDER};
        }}
        
        QToolButton:pressed {{
            background-color: {ModernColors.Light.HOVER};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {ModernColors.Light.SURFACE};
            color: {ModernColors.Light.TEXT_PRIMARY};
            border-top: 1px solid {ModernColors.Light.BORDER};
        }}
        
        QStatusBar::item {{
            border: none;
            padding: 4px 8px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {ModernColors.Light.PRIMARY};
            color: white;
            border: none;
            padding: 9px 16px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 12px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {ModernColors.Light.PRIMARY_LIGHT};
        }}
        
        QPushButton:pressed {{
            background-color: {ModernColors.Light.GRADIENT_SECONDARY};
        }}

        QPushButton#UbaRecalculateButton {{
            background-color: {ModernColors.Light.WARNING};
        }}

        QPushButton#UbaRecalculateButton:hover {{
            background-color: #d97706;
        }}

        QPushButton#UbaRefreshButton {{
            background-color: {ModernColors.Light.INFO};
        }}

        QPushButton#UbaRefreshButton:hover {{
            background-color: #0284c7;
        }}
        
        QPushButton:disabled {{
            background-color: {ModernColors.Light.SURFACE_VARIANT};
            color: {ModernColors.Light.TEXT_TERTIARY};
        }}
        
        /* Line Edits */
        QLineEdit, QPlainTextEdit {{
            background-color: white;
            color: {ModernColors.Light.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 11px;
            selection-background-color: {ModernColors.Light.PRIMARY};
        }}
        
        QLineEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {ModernColors.Light.PRIMARY};
            outline: none;
        }}
        
        QLineEdit:hover, QPlainTextEdit:hover {{
            border: 1px solid {ModernColors.Light.DIVIDER};
        }}
        
        /* Table Widget */
        QTableWidget, QTableView {{
            background-color: white;
            alternate-background-color: {ModernColors.Light.SURFACE};
            color: {ModernColors.Light.TEXT_PRIMARY};
            gridline-color: {ModernColors.Light.BORDER};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 12px;
        }}

        /* Dashboard Cards */
        #RiskSummaryFrame,
        #BehaviorVisualizationFrame,
        #IntegrityBadgeFrame,
        #QuickActionsFrame,
        #RecentEventsFrame {{
            background-color: white;
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 14px;
        }}

        #RiskSummaryTitle,
        #RecentEventsTitleLabel,
        #QuickActionsTitle,
        #IntegrityStatusLabel {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            font-weight: 700;
            letter-spacing: 0.3px;
        }}

        #UbaDashboardTitle,
        #UbaBaselineTitle,
        #BehaviorChartsTitle {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            font-weight: 700;
        }}

        #UbaRecalculateButton,
        #UbaRefreshButton {{
            padding-left: 14px;
            padding-right: 14px;
        }}

        #WelcomeUserBadge {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 600;
            background-color: transparent;
            border: none;
            padding: 0px;
        }}

        #LoginDialog,
        #CreateUserDialog {{
            background-color: {ModernColors.Light.SURFACE};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 14px;
        }}

        #LoginTitle,
        #CreateUserTitle {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            font-weight: 800;
            font-size: 20px;
        }}

        #LoginSubtitle,
        #CreateUserSubtitle {{
            color: {ModernColors.Light.TEXT_SECONDARY};
            font-size: 12px;
        }}

        #PrimaryActionButton {{
            background-color: {ModernColors.Light.PRIMARY};
        }}

        #PrimaryActionButton:hover {{
            background-color: {ModernColors.Light.PRIMARY_LIGHT};
        }}

        #SecondaryActionButton {{
            background-color: {ModernColors.Light.SURFACE_VARIANT};
            color: {ModernColors.Light.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Light.BORDER};
        }}

        #SecondaryActionButton:hover {{
            background-color: {ModernColors.Light.HOVER};
        }}

        #DangerActionButton {{
            background-color: {ModernColors.Light.ERROR};
        }}

        #DangerActionButton:hover {{
            background-color: #d93636;
        }}

        #SectionSubtitle {{
            color: {ModernColors.Light.TEXT_TERTIARY};
            font-size: 11px;
        }}

        #FormLabel {{
            color: {ModernColors.Light.TEXT_SECONDARY};
            background: transparent;
            font-weight: 600;
        }}

        #DialogInput {{
            background-color: {ModernColors.Light.SURFACE_VARIANT};
            color: {ModernColors.Light.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 8px;
            padding: 8px 10px;
        }}

        #DialogInput:focus {{
            border: 1px solid {ModernColors.Light.PRIMARY};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {ModernColors.Light.PRIMARY};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {ModernColors.Light.SURFACE_VARIANT};
            color: {ModernColors.Light.TEXT_PRIMARY};
            padding: 8px;
            border-right: 1px solid {ModernColors.Light.BORDER};
            border-bottom: 1px solid {ModernColors.Light.BORDER};
            font-weight: 600;
            font-size: 11px;
        }}

        QScrollBar:vertical {{
            background-color: transparent;
            width: 10px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {ModernColors.Light.DIVIDER};
            border-radius: 5px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {ModernColors.Light.TEXT_TERTIARY};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            background: none;
        }}

        QScrollBar:horizontal {{
            background-color: transparent;
            height: 10px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {ModernColors.Light.DIVIDER};
            border-radius: 5px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {ModernColors.Light.TEXT_TERTIARY};
        }}
        
        /* Labels */
        QLabel {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            font-size: 11px;
        }}
        
        /* Group Box */
        QGroupBox {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 6px;
            margin-top: 8px;
            padding-top: 16px;
            font-weight: 600;
            font-size: 12px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }}
        
        /* Menu */
        QMenu {{
            background-color: white;
            color: {ModernColors.Light.TEXT_PRIMARY};
            border: 1px solid {ModernColors.Light.BORDER};
            padding: 4px;
            border-radius: 4px;
        }}

        /* Dialog */
        QDialog {{
            background-color: {ModernColors.Light.SURFACE};
            border: 1px solid {ModernColors.Light.BORDER};
            border-radius: 12px;
        }}

        QMessageBox {{
            background-color: {ModernColors.Light.SURFACE};
            color: {ModernColors.Light.TEXT_PRIMARY};
        }}

        QMessageBox QLabel {{
            color: {ModernColors.Light.TEXT_PRIMARY};
            background: transparent;
        }}

        QMessageBox QPushButton {{
            min-width: 90px;
        }}
        
        QMenu::item:selected {{
            background-color: {ModernColors.Light.PRIMARY};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {ModernColors.Light.DIVIDER};
            margin: 4px 0;
        }}
        """
    
    @staticmethod
    def apply_modern_theme(app: QApplication, dark_mode: bool = True):
        """Apply modern theme to application."""
        stylesheet = (ModernStylesheet.get_dark_stylesheet() 
                     if dark_mode 
                     else ModernStylesheet.get_light_stylesheet())
        app.setFont(ModernFont.body_regular())
        app.setPalette(ModernStylesheet.get_palette(dark_mode=dark_mode))
        app.setStyleSheet(stylesheet)


class ModernFont:
    """Modern font configuration."""
    
    FONT_FAMILY = "Segoe UI" if os.name == 'nt' else "SF Pro Text"
    
    @staticmethod
    def get_font(size: int = 11, bold: bool = False, italic: bool = False) -> QFont:
        """Create a modern font."""
        font = QFont(ModernFont.FONT_FAMILY, size)
        font.setBold(bold)
        font.setItalic(italic)
        return font
    
    @staticmethod
    def heading_large() -> QFont:
        """Large heading font."""
        return ModernFont.get_font(18, bold=True)
    
    @staticmethod
    def heading_medium() -> QFont:
        """Medium heading font."""
        return ModernFont.get_font(14, bold=True)
    
    @staticmethod
    def heading_small() -> QFont:
        """Small heading font."""
        return ModernFont.get_font(12, bold=True)
    
    @staticmethod
    def body_regular() -> QFont:
        """Regular body font."""
        return ModernFont.get_font(11)
    
    @staticmethod
    def body_small() -> QFont:
        """Small body font."""
        return ModernFont.get_font(9)
    
    @staticmethod
    def monospace(size: int = 10) -> QFont:
        """Monospace font for code."""
        font = QFont("Courier New" if os.name == 'nt' else "Courier", size)
        return font
