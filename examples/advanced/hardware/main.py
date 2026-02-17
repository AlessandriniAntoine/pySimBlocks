import time
import multiprocessing

import parameters as prm
from block_diagram import process_block_diagram
from camera import process_camera
from gui_emio import process_gui


def main():

    # shared variables
    shared_markers_pos = multiprocessing.Array("d", 2 * prm.nb_markers * [0.])
    shared_ref_ol = multiprocessing.Array("d", 2 * [0.0])
    shared_ref_cl = multiprocessing.Array("d", 2 * [0.0])

    # shared bool
    shared_start = multiprocessing.Value("b", False)
    shared_control_mode = multiprocessing.Value("i", 0)
    shared_update = multiprocessing.Value("b", False)

    # shared event
    event_frame = multiprocessing.Event()
    event_measure = multiprocessing.Event()

    # Create processes
    p1 = multiprocessing.Process(target=process_camera, args=(
        shared_markers_pos, shared_start, 
        event_frame, event_measure))

    p2 = multiprocessing.Process(target=process_gui, args=(
        shared_ref_ol, shared_ref_cl, 
        shared_start, shared_control_mode, shared_update))

    p3 = multiprocessing.Process(target=process_block_diagram, args=(
        shared_markers_pos, shared_ref_ol, shared_ref_cl, 
        shared_control_mode, shared_update, event_frame, event_measure))

    p1.start()
    p2.start()
    p3.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        p1.terminate()
        p2.terminate()
        p3.terminate()

        p1.join()
        p2.join()
        p3.join()


if __name__ == "__main__":
    main()
