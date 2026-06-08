import os
import sys
import warnings

from PySide6.QtCore import Qt, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from polaris_studio.ui.main_window import PolarisMainWindow
from polaris_studio.ui.theme import apply_application_font, load_fonts


STYLESHEET = """
QMainWindow {
    background-color: #f6f7fb;
}

QMenuBar {
    font-family: "Inter";
    font-weight: 500;
    background-color: #ffffff;
    color: #172033;
    border-bottom: 1px solid #dfe4ee;
    padding: 3px 8px;
    font-size: 12px;
}

QMenuBar::item {
    padding: 6px 14px;
    background: transparent;
    border-radius: 6px;
    margin: 2px 4px;
}

QMenuBar::item:selected {
    background-color: #eef2f8;
}

QMenu {
    font-family: "Inter";
    background-color: #ffffff;
    border: 1px solid #d7deea;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 28px;
    border-radius: 6px;
    color: #1a1a1a;
}

QMenu::item:selected {
    background-color: #245bdb;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #e0e0e0;
    margin: 6px 10px;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dfe4ee;
    spacing: 8px;
    padding: 8px 14px;
}

QToolBar QToolButton {
    font-family: "Inter";
    font-weight: 600;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 7px 12px;
    color: #4b5568;
    font-size: 12px;
}

QToolBar QToolButton:hover {
    background-color: #eef2f8;
    border-color: #d7deea;
}

QToolBar QToolButton:checked {
    background-color: #e8f0ff;
    color: #1746b3;
    border-color: #9db7f4;
}

QDockWidget {
    background-color: #ffffff;
    border: none;
}

QDockWidget::title {
    font-family: "Inter";
    font-weight: 700;
    background-color: #ffffff;
    padding: 11px 14px;
    border-bottom: 1px solid #dfe4ee;
    color: #263248;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0px;
}

QStatusBar {
    font-family: "Inter";
    background-color: #ffffff;
    border-top: 1px solid #dfe4ee;
    color: #4b5568;
    font-size: 11px;
    padding: 6px 12px;
}

QTabBar {
    background-color: #ffffff;
}

QTabBar::tab {
    font-family: "Inter";
    font-weight: 500;
    background-color: #f5f5f5;
    color: #666666;
    border: none;
    border-right: 1px solid #e0e0e0;
    padding: 10px 24px;
    font-size: 13px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1a1a1a;
    border-bottom: 2px solid #5b4bd6;
}

QTabBar::tab:hover:!selected {
    background-color: #f0f0f0;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    font-family: "Inter";
    background-color: #fbfcfe;
    border: 1px solid #d5dce8;
    border-radius: 6px;
    padding: 7px 10px;
    color: #172033;
    font-size: 12px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #245bdb;
    background-color: #ffffff;
}

QPushButton {
    font-family: "Inter";
    font-weight: 600;
    background-color: #ffffff;
    border: 1px solid #d5dce8;
    border-radius: 6px;
    padding: 8px 16px;
    color: #172033;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #f4f7fb;
    border-color: #245bdb;
}

QPushButton#primaryButton {
    background-color: #245bdb;
    border: none;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #1d4ec3;
}

QTableView {
    font-family: "Inter";
    background-color: #ffffff;
    border: none;
    gridline-color: #f0f0f0;
    color: #1a1a1a;
    font-size: 13px;
    selection-background-color: #f5f3ff;
    selection-color: #1a1a1a;
}

QHeaderView::section {
    font-family: "Inter";
    font-weight: 600;
    background-color: #fcfcfc;
    color: #666666;
    border: none;
    border-right: 1px solid #e0e0e0;
    border-bottom: 1px solid #e0e0e0;
    padding: 10px;
    font-size: 11px;
    text-transform: uppercase;
}

QLabel#heading {
    font-family: "Outfit";
    font-weight: 800;
    font-size: 24px;
    color: #1a1a1a;
}

QLabel#serif {
    font-family: "Instrument Serif";
    font-size: 20px;
    color: #245bdb;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #d4d4d4;
    border-radius: 5px;
    min-height: 40px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #8b8b8b;
}
"""


def _qt_message_handler(mode, context, message) -> None:
    if "Point size <= 0" in message:
        return
    if "libpyside" in message and "Failed to disconnect" in message:
        return
    sys.stderr.write(f"{message}\n")


def _install_warnings_filter() -> None:
    warnings.filterwarnings(
        "ignore",
        message=r".*Failed to disconnect.*from signal.*",
        category=RuntimeWarning,
    )


def main() -> None:
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.programmersd21.polaris")

    qInstallMessageHandler(_qt_message_handler)
    _install_warnings_filter()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Polaris Studio")
    app.setOrganizationName("Polaris")
    app.setApplicationVersion("1.0.3")

    load_fonts()
    apply_application_font(app)

    icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "icon", "icon.png")
    icon_path = os.path.abspath(icon_path)
    if os.path.exists(icon_path):
        from PySide6.QtGui import QIcon

        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet(STYLESHEET)

    window = PolarisMainWindow(icon_path)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
