from abc import ABC, abstractmethod

from pySimBlocks.gui.model import ProjectState
from pySimBlocks.gui.graphics import BlockItem
from pySimBlocks.gui.services.yaml_tools import save_yaml
from pySimBlocks.project.generate_run_script import generate_python_content


class ProjectSaver(ABC):
    
    @abstractmethod
    def save(self, project_state: ProjectState, 
             block_items: dict[str, BlockItem] | None = None):
        pass

    @abstractmethod
    def export(self, project_state: ProjectState, 
               block_items: dict[str, BlockItem] | None = None):
        pass

class ProjectSaverYaml(ProjectSaver):

    def save(self, 
             project_state: ProjectState, 
             block_items: dict[str, BlockItem] | None = None
    ):        
        save_yaml(project_state, block_items if block_items is not None else {})


    def export(self, 
               project_state: ProjectState,
               block_items: dict[str, BlockItem] | None = None
    ):
        save_yaml(project_state, block_items if block_items is not None else {})
        run_py = project_state.directory_path / "run.py"
        run_py.write_text(
            generate_python_content(
                model_yaml_path="model.yaml", parameters_yaml_path="parameters.yaml"
            )
        )
