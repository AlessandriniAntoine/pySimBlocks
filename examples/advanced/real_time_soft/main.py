"""Point d'entrée de l'application Emio — réécrit avec RealTimeSession."""

import parameters as prm

from camera_process import CameraProcess
from diagram_process import DiagramProcess
from gui_process import GUIProcess

from pySimBlocks.real_time import RealTimeSession


def main():
    session = RealTimeSession("project.yaml")

    # Blocs du diagram — taille réelle (le yaml ne déclare pas de 'size')
    session.declare_shared("Camera", prm.nb_markers * 2)  # 6 × float64
    session.declare_shared("Ref_cl", 2)                   # 2 × float64
    session.declare_shared("Ref_ol", 2)                   # 2 × float64
    session.declare_shared("Cmd",    2)                   # 2 × float64
    session.declare_shared("Mode",   1, dtype="i")        # 1 × int32

    # Champs inter-process non liés au diagram
    session.declare_shared("Start",  1, dtype="b")        # 1 × bool  (GUI → Camera)
    session.declare_shared("Update", 1, dtype="b")        # 1 × bool  (GUI → Diagram)

    camera  = CameraProcess()
    diagram = DiagramProcess()
    gui     = GUIProcess()

    session.add(camera, diagram, gui)

    session.connect("frame_ready",   src=camera, dst=diagram)
    session.connect("measure_ready", src=camera, dst=diagram)

    session.run()


if __name__ == "__main__":
    main()
