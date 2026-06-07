import os
import sys
import warnings

from PySide6.QtCore import Qt, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from polaris_studio.ui.main_window import PolarisMainWindow
from polaris_studio.ui.theme import apply_application_font, load_fonts


def load_stylesheet() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "theme.qss")
    resolved = os.path.abspath(path)
    if os.path.exists(resolved):
        with open(resolved, "r") as f:
            return f.read()
    return ""


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
    app.setApplicationVersion("1.0.1")

    load_fonts()
    apply_application_font(app)

    icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "icon", "icon.png")
    icon_path = os.path.abspath(icon_path)
    if os.path.exists(icon_path):
        from PySide6.QtGui import QIcon

        app.setWindowIcon(QIcon(icon_path))

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = PolarisMainWindow(icon_path)
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
