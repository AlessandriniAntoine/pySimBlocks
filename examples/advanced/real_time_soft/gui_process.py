"""GUIProcess — interface tkinter pour le contrôle temps réel Emio.

Réécrit avec l'API RealTimeProcess. La logique GUI (sliders, boutons,
labels) est inchangée. Seuls les accès shared mémoire changent :
    avant : with shared_ref_ol.get_lock(): shared_ref_ol[0] = ...
    après : self.shared.Ref_ol = np.array([...])
"""

import tkinter as tk

import numpy as np
import parameters as prm

from pySimBlocks.real_time import RealTimeProcess


class GUIProcess(RealTimeProcess):
    # Pas d'events émis ni reçus — la GUI lit/écrit uniquement via shared.
    emits   = []
    listens = []

    def setup(self):
        pass  # rien à initialiser avant mainloop

    def run(self):
        """Boucle producteur — cadencée par tkinter."""
        self.setup()
        root = tk.Tk()
        app = _EmioRealTimeGUI(root, self.shared)
        root.protocol("WM_DELETE_WINDOW", app.close_app)
        root.mainloop()


# ---------------------------------------------------------------------------
# GUI Class — logique inchangée, shared proxy injecté
# ---------------------------------------------------------------------------

class _EmioRealTimeGUI:
    MOTOR_SCALE = np.pi / 2 / 100  # slider [-100..100] -> radians

    def __init__(self, root, shared):
        self.root = root
        self.root.title("Emio Real Time Control")
        self.root.geometry("500x350")

        self.shared = shared

        # local state
        self.start        = False
        self.active       = True
        self.control_mode = prm.ControlMode.OPEN_LOOP

        # ------- Information Frame -------
        info_frame = tk.Frame(root)
        info_frame.pack()
        self.label_info = {}
        for item, value in [("Start", "False"), ("Active", "True"), ("Control", "Open Loop")]:
            lbl = tk.Label(info_frame, text=f"{item}: {value}", font=("Arial", 12))
            lbl.pack(side="left", padx=5, pady=5)
            self.label_info[item] = lbl

        self._build_sliders()
        self._build_buttons()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_sliders(self):
        self.label_motors  = []
        self.sliders_motor = []
        self.label_ref     = []
        self.sliders_ref   = []

        motor_label_frame  = tk.Frame(self.root); motor_label_frame.pack()
        motor_slider_frame = tk.Frame(self.root); motor_slider_frame.pack()
        ref_label_frame    = tk.Frame(self.root); ref_label_frame.pack()
        ref_slider_frame   = tk.Frame(self.root); ref_slider_frame.pack()

        for i in range(2):
            self.label_motors.append(
                self._make_label(motor_label_frame, f"Motor {i+1}: 0.00 (rad)"))
            self.sliders_motor.append(
                self._make_slider(motor_slider_frame,
                    command=lambda val, idx=i: self._motor_action(val, idx)))

            self.label_ref.append(
                self._make_label(ref_label_frame, f"Ref {i+1}: 0.00 (mm)"))
            self.sliders_ref.append(
                self._make_slider(ref_slider_frame,
                    command=lambda val, idx=i: self._ref_action(val, idx)))

        control_label_frame  = tk.Frame(self.root); control_label_frame.pack()
        control_slider_frame = tk.Frame(self.root); control_slider_frame.pack()

        self.label_control = self._make_label(
            control_label_frame, "Desired Control Mode: Open Loop")
        self.slider_control = self._make_slider(
            control_slider_frame,
            command=self._slider_control_action,
            from_=0, to=1)

    def _build_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        for name, action in [
            ("Start",          self._start_action),
            ("Switch Control", self._control_mode_action),
            ("Active",         self._active_action),
        ]:
            tk.Button(button_frame, text=name, command=action).pack(side="left", padx=3)

    # ------------------------------------------------------------------
    # Slider actions
    # ------------------------------------------------------------------

    def _motor_action(self, val, index: int):
        if not self.start:
            self.sliders_motor[index].set(0)
            return
        cmd = float(val) * self.MOTOR_SCALE
        self.label_motors[index].config(text=f"Motor {index+1}: {cmd:.2f} (rad)")
        if self.active:
            self._push_commands(prm.ControlMode.OPEN_LOOP)

    def _ref_action(self, val, index: int):
        if not self.start:
            self.sliders_ref[index].set(0)
            return
        cmd = float(val)
        self.label_ref[index].config(text=f"Ref {index+1}: {cmd:.2f} (mm)")
        if self.active:
            self._push_commands(prm.ControlMode.STATE_FEEDBACK)

    def _slider_control_action(self, val):
        if not self.start:
            self.slider_control.set(0)
            return
        self.control_mode = prm.ControlMode(int(val))
        self.label_control.config(
            text=f"Desired Control Mode: {self.control_mode.label}")

    # ------------------------------------------------------------------
    # Button actions
    # ------------------------------------------------------------------

    def _start_action(self):
        if not self.start:
            self.start = True
            self.label_info["Start"].config(text="Start: True")
            self.shared.Start = np.array([1.0])
            self._push_commands(prm.ControlMode.OPEN_LOOP)

    def _active_action(self):
        if not self.start:
            return
        self.active = not self.active
        self.label_info["Active"].config(text=f"Active: {self.active}")
        if self.active:
            self._push_commands(prm.ControlMode(int(self.shared.Mode[0])))

    def _control_mode_action(self):
        if not self.start:
            return
        self.shared.Mode   = np.array([float(int(self.control_mode))])
        self.shared.Update = np.array([1.0])
        label = ("Open Loop" if self.control_mode == prm.ControlMode.OPEN_LOOP
                 else self.control_mode.short)
        self.label_info["Control"].config(text=f"Control: {label}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def close_app(self):
        self.root.destroy()

    def _make_slider(self, frame, command, from_=-100, to=100):
        s = tk.Scale(frame, from_=from_, to=to,
                     orient="horizontal", command=command)
        s.set(0)
        s.pack(side="left", padx=3, pady=5)
        return s

    def _make_label(self, frame, text):
        lbl = tk.Label(frame, text=text)
        lbl.pack(side="left", padx=3, pady=5)
        return lbl

    def _push_commands(self, mode: prm.ControlMode):
        if mode == prm.ControlMode.OPEN_LOOP:
            pos = [float(self.sliders_motor[i].get()) for i in range(2)]
            self.shared.Ref_ol = np.array([pos[0] * self.MOTOR_SCALE,
                                           pos[1] * self.MOTOR_SCALE])
        else:
            ref = [float(self.sliders_ref[i].get()) for i in range(2)]
            self.shared.Ref_cl = np.array([ref[0], ref[1]])

        self.shared.Update = np.array([1.0])
