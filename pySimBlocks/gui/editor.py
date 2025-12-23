import sys
import os
from pathlib import Path
import shutil
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


    app = QApplication(sys.argv)
    window = MainWindow(project_path)

    def cleanup():
        temp_path = window.project.directory_path / ".temp"
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)

    app.aboutToQuit.connect(cleanup)

    window.resize(1100, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
