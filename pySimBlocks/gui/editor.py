# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it  
#  under the terms of the GNU Lesser General Public License as published by   
#  the Free Software Foundation, either version 3 of the License, or (at your 
#  option) any later version.                                                
#
#  This program is distributed in the hope that it will be useful, but WITHOUT    
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.                                                  
#
#  You should have received a copy of the GNU Lesser General Public License   
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.     
# ******************************************************************************
#  Authors: see Authors.txt                                                
# ******************************************************************************

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
