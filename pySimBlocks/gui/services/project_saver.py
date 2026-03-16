# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
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

from abc import ABC, abstractmethod

from pySimBlocks.gui.models import ProjectState
from pySimBlocks.gui.graphics import BlockItem
from pySimBlocks.gui.services.yaml_tools import save_yaml
from pySimBlocks.project.generate_run_script import generate_python_content


class ProjectSaver(ABC):
    """Define the interface for project persistence services."""


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    @abstractmethod
    def save(self, project_state: ProjectState, 
             block_items: dict[str, BlockItem] | None = None):
        """Persist the current project state.

        Args:
            project_state: Project state to save.
            block_items: Optional GUI block items used to persist layout data.
        """
        pass

    @abstractmethod
    def export(self, project_state: ProjectState, 
               block_items: dict[str, BlockItem] | None = None):
        """Export the current project state into runnable project artifacts.

        Args:
            project_state: Project state to export.
            block_items: Optional GUI block items used to persist layout data.
        """
        pass

class ProjectSaverYaml(ProjectSaver):
    """Save and export projects using the YAML project format."""


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def save(self, 
             project_state: ProjectState, 
             block_items: dict[str, BlockItem] | None = None
    ):
        """Write the project YAML file to disk.

        Args:
            project_state: Project state to save.
            block_items: Optional GUI block items used to persist layout data.
        """
        save_yaml(
            project_state,
            block_items if block_items is not None else {},
        )


    def export(self, 
               project_state: ProjectState,
               block_items: dict[str, BlockItem] | None = None
    ):
        """Export the project YAML file and generated run script.

        Args:
            project_state: Project state to export.
            block_items: Optional GUI block items used to persist layout data.

        Raises:
            ValueError: If the project directory is not defined.
        """
        if project_state.directory_path is None:
            raise ValueError("Project directory is not set.")

        save_yaml(
            project_state,
            block_items if block_items is not None else {},
        )
        run_py = project_state.directory_path / "run.py"
        run_py.write_text(
            generate_python_content(project_yaml_path="project.yaml")
        )
        
