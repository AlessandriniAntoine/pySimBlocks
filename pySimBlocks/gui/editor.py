import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from pySimBlocks.gui.main_window import MainWindow

# ============================================================
# Entry point
# ============================================================
def main():
    if len(sys.argv) > 1:
        project_dir = os.path.abspath(sys.argv[1])
    else:
        project_dir = os.getcwd()
    project_path = Path(project_dir).resolve()
    run_app(project_path)


def run_app(project_path: Path):
    app = QApplication(sys.argv)
    window = MainWindow(project_path)
    app.aboutToQuit.connect(window.cleanup)
    window.resize(1100, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
