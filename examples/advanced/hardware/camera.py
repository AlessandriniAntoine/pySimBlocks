import json

import cv2 as cv
import numpy as np
import parameters as prm
from emioapi._depthcamera import DepthCamera


# ------------------------------------------------------------------------------
# Process
# ------------------------------------------------------------------------------
def process_camera(shared_markers_pos, shared_start, 
                   event_frame, event_measure):
    """Update tracker position."""
    camera = setup_camera()

    init_pos = np.zeros((2 * prm.nb_markers))
    pos = np.zeros((2 * prm.nb_markers))
    start = False

    while True:
        # get frame from camera
        ret = camera.get_frame()
        event_frame.set()

        if not ret:
            raise RuntimeError("Camera frame not received")

        pos = process_frame(camera, pos)

        if start:
            pos -= init_pos
            with shared_markers_pos.get_lock():
                shared_markers_pos[:] = pos
            event_measure.set()

        else:
            init_pos = pos
            with shared_start.get_lock():
                start = shared_start.value

        k = cv.waitKey(1)
        if k == ord('q'):
            camera.quit()
            break


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def setup_camera():
    json_path = prm.data_path / "cameraparameter.json"
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

# -------------------------------------------------------
def pixel_to_mm(points, depth):
    ppx, ppy = 319.475, 240.962
    fx, fy = 382.605, 382.605
    points[:, 0] = ((points[:, 0] - ppx) / fx) * depth
    points[:, 1] = ((points[:, 1] - ppy) / fy) * depth
    points = np.column_stack((points[:, 2], -points[:, 1], points[:, 0]))
    return points.copy()

# -------------------------------------------------------
def camera_to_sofa_order(points):
    i_ymax = np.argmax(points[:, 1])
    i_rest = [i for i in range(prm.nb_markers) if i != i_ymax]
    i_sorted_z = sorted(i_rest, key=lambda i: points[i, 2])
    new_order = [i_sorted_z[1], i_sorted_z[0], i_ymax]
    return points[new_order].flatten()

# -------------------------------------------------------
def process_frame(camera, last_pos):
    indices = [1, 2, 4, 5, 7, 8]
    camera.process_frame()
    if len(camera.trackers_pos) == prm.nb_markers:
        pos = np.array(camera.trackers_camera).reshape(prm.nb_markers, 3).copy()
        pos = pos.astype(np.float64)
        pos = pixel_to_mm(pos, 249)
        markers_pos = camera_to_sofa_order(pos)
        return markers_pos[indices]
    return last_pos
