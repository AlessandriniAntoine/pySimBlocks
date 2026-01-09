import os
import psutil
from pathlib import Path
import time
import numpy as np
import tkinter as tk
import multiprocessing
import cv2 as cv
import json

from pySimBlocks.core import Model, Simulator
from pySimBlocks.project.load_project_config import load_simulation_config
from pySimBlocks.real_time import RealTimeRunner

from emioapi import EmioMotors
from emioapi._depthcamera import DepthCamera
from gui_emio import EmioRealTimeGUI


nb_markers = 3
data_path = Path(__file__).parent / "data"

############################################################################
# Camera helpers
#############################################################################
def setup_camera():
    json_path = data_path / "cameraparameter.json"
    with json_path.open('r') as fp:
        json_parameters = json.load(fp)
    camera = DepthCamera(
        show_video_feed=True,
        tracking=True,
        compute_point_cloud=False,
        parameter=json_parameters)
    camera.set_fps(60)
    camera.set_depth_min(0)
    camera.set_depth_max(1000)
    camera.open()
    return camera

def pixel_to_mm(points, depth):
    ppx, ppy = 319.475, 240.962
    fx, fy = 382.605, 382.605
    points[:, 0] = ((points[:, 0] - ppx) / fx) * depth
    points[:, 1] = ((points[:, 1] - ppy) / fy) * depth
    points = np.column_stack((points[:, 2], -points[:, 1], points[:, 0]))
    return points.copy()

def camera_to_sofa_order(points):
    i_ymax = np.argmax(points[:, 1])
    i_rest = [i for i in range(nb_markers) if i != i_ymax]
    i_sorted_z = sorted(i_rest, key=lambda i: points[i, 2])
    new_order = [i_sorted_z[1], i_sorted_z[0], i_ymax]
    return points[new_order].flatten()

def process_frame(camera):
    camera.process_frame()
    if len(camera.trackers_pos) == nb_markers:
        pos = np.array(camera.trackers_camera).reshape(nb_markers, 3).copy() # if front camera
        pos = pixel_to_mm(pos, 249) # if front camera
        markers_pos = camera_to_sofa_order(pos)
        return markers_pos
    return np.zeros((3 * nb_markers))

############################################################################
# Motors helpers
#############################################################################
def setup_motors(init_angles=[0, 0, 0, 0]):
    motors = EmioMotors()
    while not motors.open():
        print("Waiting for motors to open...")
        time.sleep(1)
    print("Motors opened successfully.")
    motors.position_p_gain = [2000, 800, 2000, 800]
    motors.position_i_gain = [0, 0, 0, 0]
    motors.position_d_gain = [50, 0, 50, 0]
    time.sleep(1)
    motors.angles = init_angles
    return motors

def send_motors_command(motors, command, init_angles=np.array([0, 0, 0, 0])):
    motors.angles = [command[0] + init_angles[0], init_angles[1],
                     command[1] + init_angles[2], init_angles[3]]

def get_motors_position(motors, init_angles=np.array([0, 0, 0, 0])):
    motors_pos = np.array(motors.angles) - init_angles
    return motors_pos[[0, 2]]

############################################################################
# pySimBlocks helpers
#############################################################################
def setup_runner():
    sim_cfg, model_cfg = load_simulation_config("parameters.yaml")
    model = Model( name="model", model_yaml="model.yaml", model_cfg=model_cfg)
    sim = Simulator(model, sim_cfg)
    runner = RealTimeRunner(
        sim,
        input_blocks=["Camera", "Reference", "Start"],
        output_blocks=["Motor"],
        target_dt=1/60
    )
    runner.initialize()
    return runner

############################################################################
# Process
#############################################################################
def process_camera(shared_markers_pos, event_measure, event_command):
    """Update tracker position."""
    p = psutil.Process(os.getpid())
    p.cpu_affinity([0])
    p.nice(0)
    camera = setup_camera()

    while True:
        # get frame from camera
        ret = camera.get_frame()
        event_command.set() # ask to send command

        if ret:
            pos = process_frame(camera)
            with shared_markers_pos.get_lock():
                shared_markers_pos[:] = pos

        event_measure.set() # signal that measurement is ready

        k = cv.waitKey(1)
        if k == ord('q'):
            camera.quit()
            break

def process_slider(shared_ref, shared_start, shared_update):
    p = psutil.Process(os.getpid())
    p.cpu_affinity([1])
    p.nice(0)
    root = tk.Tk()
    app = EmioRealTimeGUI(root, shared_ref, shared_start, shared_update)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()

def process_main(shared_markers_pos, shared_ref, shared_start, shared_update, event_measure, event_command):
    """Main control loop."""
    p = psutil.Process(os.getpid())
    p.cpu_affinity([2])
    p.nice(0)

    init_angles = np.array([0.7, 0, 0.7, 0])
    motors = setup_motors(init_angles)
    runner = setup_runner()

    # Initialize variables
    markers_pos = np.zeros((nb_markers * 3,))
    measure = np.zeros((nb_markers * 2,))
    init_measure = np.zeros((nb_markers * 2,))
    motors_pos = np.zeros((2,))
    command = np.zeros((2,))
    ref = np.zeros((2,))

    start = False
    t = time.time()
    dt_list = []

    while True:
        t2 = time.time()
        dt_measured = t2 - t
        t = t2
        dt_list.append(dt_measured)
        print(f"dt main loop: {dt_measured*1000:.2f} ms, mean: {np.mean(dt_list)*1000:.2f} ms")

        # On event, read current pos and send previous command
        event_command.wait()
        event_command.clear()
        motors_pos = get_motors_position(motors, init_angles)
        send_motors_command(motors, command, init_angles)

        # On event (camera ready), read markers position
        event_measure.wait()
        event_measure.clear()
        with shared_markers_pos.get_lock():
            markers_pos = np.array(shared_markers_pos[:])
        raw_measure = markers_pos[[1, 2, 4, 5, 7, 8]]

        if start:
            measure = raw_measure - init_measure
            # Update pySimBlocks inputs
            with shared_update.get_lock():
                if shared_update.value:
                    with shared_ref.get_lock():
                        ref = np.array(shared_ref[:])

            outs = runner.tick(
                inputs={
                    "Camera": measure.reshape((nb_markers * 2, 1)),
                    "Reference": ref.reshape((2, 1)),
                    "Start": np.array([[1]])
                },
                dt=dt_measured,
                pace=False
            )
            command = outs["Motor"].flatten()

        else:
            init_measure = raw_measure.copy()

        with shared_start.get_lock():
            start = shared_start.value



def main():

    # shared variables
    shared_markers_pos = multiprocessing.Array("d", 3 * nb_markers * [0.])
    shared_ref = multiprocessing.Array("d", 2 * [0.0])
    shared_start = multiprocessing.Value("b", False)
    shared_update = multiprocessing.Value("b", False)
    event_measure = multiprocessing.Event()
    event_command = multiprocessing.Event()

    # Create processes
    p1 = multiprocessing.Process(target=process_camera, args=(shared_markers_pos, event_measure, event_command))
    p2 = multiprocessing.Process(target=process_main, args=(shared_markers_pos, shared_ref, shared_start, shared_update, event_measure, event_command))
    p3 = multiprocessing.Process(target=process_slider, args=(shared_ref, shared_start, shared_update))

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


def createScene(root):
    """Create the scene for the direct control application."""
    main()

if __name__ == "__main__":
    main()
