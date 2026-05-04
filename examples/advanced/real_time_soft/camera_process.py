"""CameraProcess — capte les frames et mesures du depth camera.

Réécrit avec l'API RealTimeProcess. La logique métier (setup_camera,
process_frame, pixel_to_mm, camera_to_sofa_order) est inchangée.

Ce process est un producteur : il a sa propre boucle bloquante (run())
et signale les autres via self.emit().
"""


import numpy as np
import parameters as prm
# from emioapi._depthcamera import DepthCamera
import time




from pySimBlocks.real_time import RealTimeProcess

class DepthCamera:
    def __init__(self, *args, **kwargs):
        self.t0 = time.perf_counter()


    def set_fps(self, fps):
        pass

    def set_depth_min(self, depth_min):
        pass

    def set_depth_max(self, depth_max):
        pass

    def open(self):
        pass

    def get_frame(self):
        return True

    def process_frame(self):
        while (time.perf_counter() - self.t0) < prm.dt:
            pass
        self.t0 = time.perf_counter()

    @property
    def trackers_pos(self):
        return np.random.rand(prm.nb_markers, 3) * 10

    @property
    def trackers_camera(self):
        return np.random.rand(prm.nb_markers * 3) * 10


class CameraProcess(RealTimeProcess):
    emits = ["frame_ready", "measure_ready"]

    def setup(self):
        self._camera = _setup_camera()
        self._init_pos = np.zeros(2 * prm.nb_markers)
        self._last_pos = np.zeros(2 * prm.nb_markers)
        self._started = False

    def run(self):
        """Boucle producteur — cadencée par la caméra."""
        self.setup()

        while True:
            ret = self._camera.get_frame()
            # Signal immédiat : la frame est prête, le moteur peut être envoyé
            self.emit("frame_ready")

            if not ret:
                raise RuntimeError("Camera frame not received")

            pos = _process_frame(self._camera, self._last_pos)
            self._last_pos = pos

            if self._started:
                self.shared.Camera = pos - self._init_pos
                self.emit("measure_ready")
            else:
                # Stocke la position initiale, attend le GO de la GUI
                self._init_pos = pos
                self._started = bool(self.shared.Start[0])

# ---------------------------------------------------------------------------
# Helpers (inchangés depuis camera.py original)
# ---------------------------------------------------------------------------

def _setup_camera() -> DepthCamera:
    camera = DepthCamera(
        show_video_feed=True,
        tracking=True,
        compute_point_cloud=False,
    )
    camera.set_fps(60)
    camera.set_depth_min(0)
    camera.set_depth_max(1000)
    camera.open()
    return camera


def _pixel_to_mm(points, depth):
    ppx, ppy = 319.475, 240.962
    fx, fy = 382.605, 382.605
    points[:, 0] = ((points[:, 0] - ppx) / fx) * depth
    points[:, 1] = ((points[:, 1] - ppy) / fy) * depth
    points = np.column_stack((points[:, 2], -points[:, 1], points[:, 0]))
    return points.copy()


def _camera_to_sofa_order(points):
    i_ymax = np.argmax(points[:, 1])
    i_rest = [i for i in range(prm.nb_markers) if i != i_ymax]
    i_sorted_z = sorted(i_rest, key=lambda i: points[i, 2])
    new_order = [i_sorted_z[1], i_sorted_z[0], i_ymax]
    return points[new_order].flatten()


def _process_frame(camera, last_pos: np.ndarray) -> np.ndarray:
    indices = [1, 2, 4, 5, 7, 8]
    camera.process_frame()
    if len(camera.trackers_pos) == prm.nb_markers:
        pos = np.array(camera.trackers_camera).reshape(prm.nb_markers, 3).copy()
        pos = pos.astype(np.float64)
        pos = _pixel_to_mm(pos, 249)
        markers_pos = _camera_to_sofa_order(pos)
        return markers_pos[indices]
    return last_pos


if __name__ == "__main__":
    # Test rapide du process (sans session ni diagram)
    proc = CameraProcess()
    proc.setup()
    for _ in range(5):
        proc.run()
