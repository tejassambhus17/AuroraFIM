# aurorafimpro/aurorafimpro/core/reporting.py
import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Adjust path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import config
except ImportError as e:
    print(f"Error importing config in core/reporting.py: {e}")

    class MockConfig:
        APP_NAME = "AuroraFIM Pro (Mock)"
        REPORTS_DIR_NAME = "mock_reports"
        BASE_DIR = "."
    config = MockConfig()

REPORTS_DIR = os.path.join(config.BASE_DIR, config.REPORTS_DIR_NAME)
if not os.path.exists(REPORTS_DIR):
    try:
        os.makedirs(REPORTS_DIR, exist_ok=True)
    except OSError as e:
        print(f"Error creating reports directory {REPORTS_DIR}: {e}")
        REPORTS_DIR = "."

STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name='Justify', alignment=4))
STYLES.add(ParagraphStyle(name='ReportTitle',
           parent=STYLES['h1'], alignment=1, fontSize=18))
STYLES.add(ParagraphStyle(name='SubTitle',
           parent=STYLES['h2'], alignment=1, fontSize=14))
STYLES.add(ParagraphStyle(name='SmallText',
           parent=STYLES['Normal'], fontSize=8))
STYLES.add(ParagraphStyle(name='TableHeader',
           parent=STYLES['Normal'], fontName='Helvetica-Bold', alignment=1))
STYLES.add(ParagraphStyle(name='TableCell',
           parent=STYLES['Normal'], fontSize=9))
STYLES.add(ParagraphStyle(name='TableCellRed',
           parent=STYLES['TableCell'], textColor=colors.red))
STYLES.add(ParagraphStyle(name='TableCellGreen',
           parent=STYLES['TableCell'], textColor=colors.green))
STYLES.add(ParagraphStyle(name='TableCellOrange',
           parent=STYLES['TableCell'], textColor=colors.orange))


class ReportGenerator:
    def __init__(self, report_data: dict, audit_summary: dict = None):
        self.report_data = report_data
        self.audit_summary = audit_summary or {}
        self.story = []

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        abs_reports_dir = os.path.abspath(REPORTS_DIR)
        if not os.path.exists(abs_reports_dir):
            try:
                os.makedirs(abs_reports_dir, exist_ok=True)
            except OSError:
                print(
                    f"Warning: Could not ensure reports directory {abs_reports_dir}. Using current.")
                abs_reports_dir = "."
        self.filename = os.path.join(
            abs_reports_dir, f"AuroraFIM_Audit_Report_{timestamp_str}.pdf")

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        header_text = f"{getattr(config, 'APP_NAME', 'FIM Report')} - Audit Report"
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, doc.height + doc.topMargin -
                          0.5 * inch, header_text)
        footer_text = f"Page {doc.page} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        canvas.setFont('Helvetica', 9)
        canvas.drawString(inch, 0.75 * inch, footer_text)
        canvas.restoreState()

    def build_pdf(self) -> str | None:
        try:
            doc = SimpleDocTemplate(self.filename, pagesize=letter,
                                    rightMargin=72, leftMargin=72,
                                    topMargin=72, bottomMargin=72)
            self._add_title_and_summary()
            self._add_discrepancies_table()
            doc.build(self.story, onFirstPage=self._header_footer,
                      onLaterPages=self._header_footer)
            print(f"Report generated successfully: {self.filename}")
            return self.filename
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _add_title_and_summary(self):
        self.story.append(Paragraph(
            f"{getattr(config, 'APP_NAME', 'FIM Report')} Audit Report", STYLES['ReportTitle']))
        self.story.append(Spacer(1, 0.2 * inch))

        report_time_str = self.audit_summary.get("timestamp")
        report_time_display = "N/A"
        if report_time_str:
            try:
                report_datetime = datetime.fromisoformat(report_time_str)
                report_time_display = report_datetime.strftime(
                    '%Y-%m-%d %H:%M:%S %Z')
            except ValueError:
                report_time_display = report_time_str

        self.story.append(
            Paragraph(f"Audit Performed On: {report_time_display}", STYLES['SubTitle']))
        self.story.append(Spacer(1, 0.2 * inch))
        summary_text = [
            f"<b>Total Files in Baseline:</b> {self.audit_summary.get('files_in_baseline', 'N/A')}",
            f"<b>Files Checked from Baseline:</b> {self.audit_summary.get('files_checked_from_baseline', 'N/A')}",
            f"<b>Mismatches (Modified/Removed):</b> {self.audit_summary.get('mismatches_found', 'N/A')}",
            f"<b>New Files Detected:</b> {self.audit_summary.get('new_files_detected', 'N/A')}",
            f"<b>Scan Errors:</b> {self.audit_summary.get('scan_errors', 'N/A')}",
        ]
        for item in summary_text:
            self.story.append(Paragraph(item, STYLES['Normal']))
        self.story.append(Spacer(1, 0.3 * inch))

    def _add_discrepancies_table(self):
        discrepancies = self.report_data.get('discrepancies', [])
        if not discrepancies:
            self.story.append(
                Paragraph("No discrepancies found in this report period.", STYLES['Normal']))
            return

        self.story.append(Paragraph("Detected Discrepancies:", STYLES['h2']))
        self.story.append(Spacer(1, 0.1 * inch))
        data = [[Paragraph(h, STYLES['TableHeader']) for h in [
            "Timestamp", "File Path", "Event Type", "Details"]]]

        for event in discrepancies:
            ts_float = event.get(
                "event_timestamp", event.get("timestamp", 0.0))
            ts_str = datetime.fromtimestamp(ts_float).strftime(
                '%Y-%m-%d %H:%M:%S') if ts_float else "N/A"
            path = event.get("file_path", event.get("path", "N/A"))
            event_type = event.get(
                "event_type", event.get("change_type", "N/A"))

            details_str = ""
            if "MODIFIED" in event_type.upper():
                # CORRECTED SECTION: Handle None before slicing
                expected_hash_val = event.get(
                    'baseline_hash', event.get('expected_hash'))
                actual_hash_val = event.get('actual_hash')

                expected_hash_display = f"{expected_hash_val[:12]}..." if isinstance(
                    expected_hash_val, str) else "N/A"
                actual_hash_display = f"{actual_hash_val[:12]}..." if isinstance(
                    actual_hash_val, str) else "N/A"

                details_str = f"Exp. Hash: {expected_hash_display}\nAct. Hash: {actual_hash_display}"
            elif event.get("details"):
                details_str = str(event.get("details"))
            elif "REMOVED" in event_type.upper():
                details_str = "File removed."
            elif "NEW" in event_type.upper() or "CREATED" in event_type.upper():
                actual_hash_val = event.get('actual_hash')
                actual_hash_display = f"{actual_hash_val[:12]}..." if isinstance(
                    actual_hash_val, str) else "N/A"
                details_str = f"New. Hash: {actual_hash_display}"

            event_cell_style = STYLES['TableCell']
            if "ERROR" in event_type:
                event_cell_style = STYLES['TableCellRed']
            elif "MODIFIED" in event_type or "REMOVED" in event_type:
                event_cell_style = STYLES['TableCellOrange']
            elif "NEW" in event_type or "CREATED" in event_type:
                event_cell_style = STYLES['TableCellGreen']

            data.append([
                Paragraph(ts_str, STYLES['TableCell']), Paragraph(
                    path, STYLES['TableCell']),
                Paragraph(event_type, event_cell_style), Paragraph(
                    details_str, STYLES['TableCell'])
            ])

        table = Table(data, colWidths=[1.5*inch, 2.8*inch, 1.5*inch, 1.7*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR',
                                                           (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN',
                                                  (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0),
             'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('GRID',
                                                             (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1),
             6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1),
             6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        self.story.append(table)


if __name__ == '__main__':
    print(f"Report output directory (from test block): {REPORTS_DIR}")
    mock_discrepancies = [
        {"event_timestamp": time.time() - 3600, "file_path": "/var/log/secure.log", "event_type": "MODIFIED_HASH",
         "baseline_hash": "abc123def456789", "actual_hash": "def123abc456789"},
        {"event_timestamp": time.time() - 1800, "file_path": "/etc/passwd",
         "event_type": "REMOVED"},
        {"event_timestamp": time.time() - 700, "file_path": "/tmp/newfile.txt",
         "event_type": "NEW_FILE_DETECTED", "actual_hash": None},  # Test None actual_hash
        {"event_timestamp": time.time() - 600, "file_path": "/tmp/another_mod.txt", "event_type": "MODIFIED_HASH",
         "baseline_hash": None, "actual_hash": "newhash123"},  # Test None baseline_hash
    ]
    mock_summary = {"timestamp": datetime.now().isoformat(
    ), "files_in_baseline": 100, "mismatches_found": 2}

    report_gen = ReportGenerator(
        report_data={'discrepancies': mock_discrepancies}, audit_summary=mock_summary)
    pdf_file = report_gen.build_pdf()
    if pdf_file:
        print(f"Mock report generated: {pdf_file}")
    else:
        print("Mock report generation failed.")
