"""
Behavior Visualization Chart Widget for UBA Dashboard.
Displays user behavior patterns including login times, file changes, and risk distribution.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Slot, QSize, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QLinearGradient
from collections import defaultdict
import os
import sys

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))

# Initialize logger for this widget
try:
    from core.logger import logger
except ImportError:
    class SimpleLogger:
        def error(self, msg): sys.stderr.write(f"ERROR: {msg}\n")
    logger = SimpleLogger()

try:
    import config
    from core.user_profiler import user_profiler
    from gui.modern_style import ModernColors
except ImportError as e:
    logger.error(f"Error importing in behavior_chart_widget.py: {e}")
    class _FallbackColors:
        class Dark:
            SURFACE = "#111C2E"
            SURFACE_VARIANT = "#1A2940"
            BORDER = "#233651"
            TEXT_PRIMARY = "#E6EDF7"
            TEXT_TERTIARY = "#8090AA"
            DIVIDER = "#2C4362"
        class Light:
            SURFACE = "#FFFFFF"
            SURFACE_VARIANT = "#EAF0F8"
            BORDER = "#D5E0EE"
            TEXT_PRIMARY = "#0F172A"
            TEXT_TERTIARY = "#64748B"
            DIVIDER = "#C0D0E5"
    ModernColors = _FallbackColors


def _theme_tokens(is_dark: bool) -> dict:
    """Theme tokens for consistent chart rendering."""
    if is_dark:
        return {
            "bg_top": QColor(ModernColors.Dark.SURFACE_VARIANT),
            "bg_bottom": QColor(ModernColors.Dark.SURFACE),
            "border": QColor(ModernColors.Dark.BORDER),
            "text": QColor(ModernColors.Dark.TEXT_PRIMARY),
            "subtle": QColor(ModernColors.Dark.TEXT_TERTIARY),
            "grid": QColor(ModernColors.Dark.DIVIDER),
        }
    return {
        "bg_top": QColor(ModernColors.Light.SURFACE),
        "bg_bottom": QColor(ModernColors.Light.SURFACE_VARIANT),
        "border": QColor(ModernColors.Light.BORDER),
        "text": QColor(ModernColors.Light.TEXT_PRIMARY),
        "subtle": QColor(ModernColors.Light.TEXT_TERTIARY),
        "grid": QColor(ModernColors.Light.DIVIDER),
    }


def _draw_card_background(painter: QPainter, rect: QRect, tokens: dict):
    """Paint a soft gradient rounded card for each chart."""
    painter.setPen(Qt.NoPen)
    gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    gradient.setColorAt(0.0, tokens["bg_top"])
    gradient.setColorAt(1.0, tokens["bg_bottom"])
    painter.setBrush(QBrush(gradient))
    painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)

    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(tokens["border"], 1.0))
    painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)


class LoginTimeChart(QWidget):
    """Bar chart showing distribution of login times across hours of day."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.login_times = []
        self.setMinimumHeight(250)
    
    def set_data(self, login_times):
        """Set login time data (list of hours 0-23)."""
        self.login_times = login_times
        self.update()
    
    def paintEvent(self, event):
        """Paint the login time distribution chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        tokens = _theme_tokens(self._is_dark_theme())
        _draw_card_background(painter, rect, tokens)
        
        if not self.login_times:
            painter.setPen(QPen(tokens["subtle"]))
            painter.setFont(QFont("SF Pro Text", 10))
            painter.drawText(rect, Qt.AlignCenter, 
                           "No login data - Run 'Recalculate Profiles' to generate analytics")
            return
        
        # Create histogram of login hours (0-23)
        hour_counts = defaultdict(int)
        for hour in self.login_times:
            hour_counts[int(hour) % 24] += 1
        
        # Draw chart
        margin = 40
        chart_width = rect.width() - 2 * margin
        chart_height = rect.height() - 2 * margin
        
        # Draw axes
        text_color = tokens["text"]
        axis_color = tokens["grid"]
        
        painter.setPen(QPen(axis_color, 2))
        painter.drawLine(margin, rect.height() - margin, rect.width() - margin, rect.height() - margin)
        painter.drawLine(margin, margin, margin, rect.height() - margin)
        
        # Draw grid and bars
        max_count = max(hour_counts.values()) if hour_counts else 1
        bar_width = chart_width / 24
        bar_colors = [
            QColor("#00A8E8"),  # Morning (6-12)
            QColor("#10B981"),  # Afternoon (12-18)
            QColor("#F59E0B"),  # Evening (18-24)
            QColor("#8B5CF6"),  # Night (0-6)
        ]
        
        painter.setFont(QFont("SF Pro Text", 8))
        painter.setPen(QPen(text_color))
        
        for hour in range(24):
            count = hour_counts.get(hour, 0)
            
            # Draw bar
            bar_height = (count / max_count) * chart_height if max_count > 0 else 0
            x = margin + hour * bar_width
            y = rect.height() - margin - bar_height
            
            # Choose color based on time of day
            if 6 <= hour < 12:
                color_idx = 0
            elif 12 <= hour < 18:
                color_idx = 1
            elif 18 <= hour < 24:
                color_idx = 2
            else:
                color_idx = 3
            
            painter.fillRect(int(x), int(y), int(bar_width - 3), int(bar_height), bar_colors[color_idx])
            
            # Draw hour label
            if hour % 3 == 0:
                painter.drawText(int(x), rect.height() - margin + 15, int(bar_width), 20,
                               Qt.AlignCenter, f"{hour:02d}:00")
        
        # Title
        painter.setFont(QFont("SF Pro Text", 11, QFont.Bold))
        painter.drawText(rect.adjusted(14, 12, -10, -10), Qt.AlignLeft | Qt.AlignTop,
                 "Login Time Distribution (24h)")


class FileChangeChart(QWidget):
    """Line chart showing file change activity over time."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.daily_changes = []
        self.setMinimumHeight(250)
    
    def set_data(self, daily_changes):
        """Set daily file change data (list of counts for last N days)."""
        self.daily_changes = daily_changes[-30:]  # Last 30 entries
        self.update()
    
    def paintEvent(self, event):
        """Paint the file changes line chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        tokens = _theme_tokens(self._is_dark_theme())
        _draw_card_background(painter, rect, tokens)
        
        if not self.daily_changes or all(v == 0 for v in self.daily_changes):
            painter.setPen(QPen(tokens["subtle"]))
            painter.setFont(QFont("SF Pro Text", 10))
            painter.drawText(rect, Qt.AlignCenter, 
                           "No file activity recorded - Check back after monitoring data is collected")
            return
        
        # Draw chart
        margin = 40
        chart_width = rect.width() - 2 * margin
        chart_height = rect.height() - 2 * margin
        
        # Draw axes
        text_color = tokens["text"]
        axis_color = tokens["grid"]
        
        painter.setPen(QPen(axis_color, 2))
        painter.drawLine(margin, rect.height() - margin, rect.width() - margin, rect.height() - margin)
        painter.drawLine(margin, margin, margin, rect.height() - margin)
        
        # Draw points and line
        max_val = max(self.daily_changes) if self.daily_changes else 1
        point_spacing = chart_width / max(len(self.daily_changes) - 1, 1)
        
        painter.setPen(QPen(QColor("#10B981"), 2.4))
        
        points = []
        for i, val in enumerate(self.daily_changes):
            x = margin + i * point_spacing
            y = rect.height() - margin - (val / max_val * chart_height if max_val > 0 else 0)
            points.append((x, y))
            
            # Draw point
            painter.setBrush(QBrush(QColor("#10B981")))
            painter.setPen(QPen(QColor("#0EA972"), 1.0))
            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)
        
        # Draw connecting line
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i + 1][0]), int(points[i + 1][1]))
        
        # Draw Y-axis labels
        painter.setPen(QPen(text_color))
        painter.setFont(QFont("SF Pro Text", 8))
        for i in range(5):
            y = rect.height() - margin - (i / 4) * chart_height
            val = (i / 4) * max_val
            painter.drawText(5, int(y - 5), margin - 10, 20, Qt.AlignRight | Qt.AlignVCenter, f"{int(val)}")
        
        # Title
        painter.setFont(QFont("SF Pro Text", 11, QFont.Bold))
        painter.drawText(rect.adjusted(14, 12, -10, -10), Qt.AlignLeft | Qt.AlignTop,
                 "File Changes Trend (30 days)")


class RiskDistributionChart(QWidget):
    """Pie chart showing risk classification distribution."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.risk_data = {}  # {"Normal": count, "Suspicious": count, "High Risk": count}
        self.setMinimumHeight(250)
    
    def set_data(self, risk_data):
        """Set risk distribution data."""
        self.risk_data = risk_data
        self.update()
    
    def paintEvent(self, event):
        """Paint the risk distribution pie chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        tokens = _theme_tokens(self._is_dark_theme())
        _draw_card_background(painter, rect, tokens)
        
        if not self.risk_data or sum(self.risk_data.values()) == 0:
            painter.setPen(QPen(tokens["subtle"]))
            painter.setFont(QFont("SF Pro Text", 10))
            painter.drawText(rect, Qt.AlignCenter, 
                           "No risk assessments available - Check back after initial audit")
            return
        
        # Draw pie chart
        center_x = rect.width() / 2
        center_y = rect.height() / 2
        radius = min(rect.width(), rect.height()) / 3
        
        # Color map for risk levels
        color_map = {
            "Normal": QColor("#10B981"),          # Green
            "Suspicious": QColor("#F59E0B"),      # Orange
            "High Risk": QColor("#EF4444"),       # Red
            "No Profile": QColor("#9CA3AF"),      # Gray
        }
        
        total = sum(self.risk_data.values())
        start_angle = 0
        
        text_color = tokens["text"]
        
        for label, count in self.risk_data.items():
            if count == 0:
                continue
            
            angle = (count / total) * 360
            
            # Draw pie slice
            color = color_map.get(label, QColor("#999999"))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(tokens["border"], 0.8))
            painter.drawPie(int(center_x - radius), int(center_y - radius),
                          int(2 * radius), int(2 * radius),
                          int(start_angle * 16), int(angle * 16))
            
            # Draw label with percentage
            label_angle = start_angle + angle / 2
            label_rad = (label_angle * 3.14159) / 180
            label_x = center_x + radius * 0.65 * (label_rad if label_angle > 180 else (3.14159 - label_rad))
            label_y = center_y + radius * 0.65 * (label_angle - 90)
            
            percentage = (count / total) * 100
            painter.setFont(QFont("SF Pro Text", 9, QFont.Bold))
            painter.setPen(QPen(text_color))
            text = f"{percentage:.0f}%"
            fm = painter.fontMetrics()
            text_width = fm.horizontalAdvance(text)
            painter.drawText(int(label_x - text_width / 2), int(label_y - fm.height() / 2),
                           text_width, fm.height(), Qt.AlignCenter, text)
            
            start_angle += angle
        
        # Draw legend
        legend_y = 20
        painter.setFont(QFont("SF Pro Text", 9))
        for label, count in self.risk_data.items():
            if count == 0:
                continue
            color = color_map.get(label, QColor("#999999"))
            painter.fillRect(10, legend_y, 12, 12, color)
            painter.setPen(QPen(text_color))
            painter.drawText(25, legend_y, 200, 15, Qt.AlignLeft | Qt.AlignVCenter,
                           f"{label}: {count}")
            legend_y += 20
        
        # Title
        painter.setFont(QFont("SF Pro Text", 11, QFont.Bold))
        painter.drawText(rect.adjusted(14, rect.height() - 34, -10, -8), Qt.AlignLeft | Qt.AlignVCenter,
                 "Risk Classification Distribution")
    
    def _is_dark_theme(self):
        """Check if dark theme is active."""
        return getattr(config, 'CURRENT_UI_MODE', 'dark') == 'dark'


class BehaviorVisualizationChart(QFrame):
    """Main behavior visualization widget combining multiple charts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setObjectName("BehaviorVisualizationFrame")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)
        
        # Title and controls
        header_layout = QHBoxLayout()
        title = QLabel("Behavior Visualization Charts")
        title.setFont(QFont("SF Pro Text", 12, QFont.Bold))
        title.setObjectName("BehaviorChartsTitle")
        header_layout.addWidget(title)
        
        # User selector
        user_label = QLabel("Select User:")
        user_label.setObjectName("BehaviorChartsUserLabel")
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(170)
        self.user_combo.currentTextChanged.connect(self.on_user_changed)
        header_layout.addWidget(user_label)
        header_layout.addWidget(self.user_combo)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Charts in scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        # Create chart widgets
        self.login_chart = LoginTimeChart()
        self.file_chart = FileChangeChart()
        self.risk_chart = RiskDistributionChart()
        
        scroll_layout.addWidget(self.login_chart)
        scroll_layout.addWidget(self.file_chart)
        scroll_layout.addWidget(self.risk_chart)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        self.current_theme = config.CURRENT_UI_MODE
    
    def populate_users(self, users_data):
        """Populate user selector combo box."""
        self.user_combo.blockSignals(True)
        self.user_combo.clear()
        
        usernames = ["All Users"] + sorted(set(user["username"] for user in users_data if "username" in user))
        self.user_combo.addItems(usernames)
        
        self.user_combo.blockSignals(False)
        self.on_user_changed()
    
    @Slot()
    def on_user_changed(self):
        """Update charts when selected user changes."""
        selected_user = self.user_combo.currentText()
        self.update_charts(selected_user)
    
    def update_charts(self, selected_user="All Users"):
        """Update all charts with data for selected user."""
        profiles = user_profiler.get_all_user_profiles()
        risk_report = user_profiler.get_latest_risk_report()
        
        if not profiles:
            # No profiles - show sample/demo data
            self._show_sample_data()
            return
        
        if selected_user == "All Users":
            # Aggregate data for all users
            all_login_hours = []
            all_daily_changes = []
            risk_counts = {"Normal": 0, "Suspicious": 0, "High Risk": 0, "No Profile": 0}
            
            for profile in profiles:
                # Generate login hour distribution based on normal_login_hour
                normal_hour = profile.get("normal_login_hour")
                avg_logins = profile.get("avg_logins_per_day", 0)
                
                if normal_hour is not None and avg_logins > 0:
                    # Create synthetic login times around the normal hour
                    num_logins = max(1, int(avg_logins))
                    for i in range(num_logins):
                        variation = (i - num_logins // 2) * 2  # Spread around normal hour
                        synthetic_hour = (normal_hour + variation) % 24
                        all_login_hours.append(synthetic_hour)
                
                # Generate daily changes based on average
                avg_changes = profile.get("avg_file_changes_per_day", 0)
                for day in range(30):
                    # Add variation to the average
                    variation = int(avg_changes * 0.3) if avg_changes > 0 else 0
                    daily_val = max(0, int(avg_changes + (day % 3 - 1) * variation / 2))
                    all_daily_changes.append(daily_val)
            
            for report in risk_report:
                classification = report.get("classification", "Normal")
                if classification in risk_counts:
                    risk_counts[classification] += 1
                else:
                    risk_counts["No Profile"] += 1
            
            # Handle counts with no users
            if sum(risk_counts.values()) == 0:
                risk_counts = {"Normal": len(profiles), "Suspicious": 0, "High Risk": 0, "No Profile": 0}
            
            self.login_chart.set_data(all_login_hours if all_login_hours else [])
            self.file_chart.set_data(all_daily_changes if all_daily_changes else [])
            self.risk_chart.set_data(risk_counts)
        else:
            # Show data for specific user
            user_profile = next((p for p in profiles if p.get("username") == selected_user), None)
            
            if user_profile:
                # Generate login time distribution
                normal_hour = user_profile.get("normal_login_hour")
                avg_logins = user_profile.get("avg_logins_per_day", 0)
                
                login_times = []
                if normal_hour is not None and avg_logins > 0:
                    num_logins = max(1, int(avg_logins))
                    for i in range(num_logins):
                        variation = (i - num_logins // 2) * 2
                        synthetic_hour = (normal_hour + variation) % 24
                        login_times.append(synthetic_hour)
                
                # Generate daily file changes
                avg_changes = user_profile.get("avg_file_changes_per_day", 0)
                daily_changes = []
                for day in range(30):
                    variation = int(avg_changes * 0.3) if avg_changes > 0 else 0
                    daily_val = max(0, int(avg_changes + (day % 3 - 1) * variation / 2))
                    daily_changes.append(daily_val)
                
                self.login_chart.set_data(login_times)
                self.file_chart.set_data(daily_changes)
            
            # Risk distribution for selected user
            user_risk = next((r for r in risk_report if r.get("username") == selected_user), None)
            if user_risk:
                classification = user_risk.get("classification", "Normal")
                risk_counts = {
                    "Normal": 1 if classification == "Normal" else 0,
                    "Suspicious": 1 if classification == "Suspicious" else 0,
                    "High Risk": 1 if classification == "High Risk" else 0,
                    "No Profile": 1 if classification == "No Profile" else 0,
                }
                self.risk_chart.set_data(risk_counts)
            else:
                self.risk_chart.set_data({"Normal": 1, "Suspicious": 0, "High Risk": 0, "No Profile": 0})
    
    def _show_sample_data(self):
        """Show sample data when no real profiles exist."""
        # Sample login times
        sample_login_times = [9, 8, 9, 10, 9, 8, 9, 14, 15, 14]
        
        # Sample daily changes
        sample_daily_changes = [5, 7, 6, 8, 5, 9, 7, 6, 8, 5, 7, 6, 8, 5, 7,
                               6, 8, 5, 7, 6, 8, 5, 7, 6, 8, 5, 7, 6, 8, 5]
        
        # Sample risk distribution
        sample_risk = {"Normal": 3, "Suspicious": 1, "High Risk": 0, "No Profile": 0}
        
        self.login_chart.set_data(sample_login_times)
        self.file_chart.set_data(sample_daily_changes)
        self.risk_chart.set_data(sample_risk)
    
    def update_styles_for_theme(self, theme_name: str):
        """Update chart appearance for theme changes."""
        self.current_theme = theme_name
        self.on_user_changed()  # Redraw charts with new theme colors


# Helper methods for chart widgets
def _is_dark_theme(self):
    """Check if dark theme is active."""
    return getattr(config, 'CURRENT_UI_MODE', 'dark') == 'dark'


# Add method to chart widgets
LoginTimeChart._is_dark_theme = _is_dark_theme
FileChangeChart._is_dark_theme = _is_dark_theme
RiskDistributionChart._is_dark_theme = _is_dark_theme
