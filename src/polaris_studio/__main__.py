import os
import sys

from PySide6.QtCore import Qt
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


def main() -> None:
    # Windows: set AppUserModelID so taskbar shows the correct icon
    import sys as _sys

    if _sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.programmersd21.polaris")

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Polaris Studio")
    app.setOrganizationName("Polaris")
    app.setApplicationVersion("1.0.0")

    load_fonts()
    apply_application_font(app)

    # App icon - shows in taskbar and window title bar
    icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "icon", "icon.png")
    icon_path = os.path.abspath(icon_path)
    if os.path.exists(icon_path):
        from PySide6.QtGui import QIcon

        app.setWindowIcon(QIcon(icon_path))

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = PolarisMainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
