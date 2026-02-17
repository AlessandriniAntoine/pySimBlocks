import tkinter as tk

import numpy as np
import parameters as prm


# -------------------------------------------------------------------------------
# Process
# -------------------------------------------------------------------------------
def process_gui(shared_ref_ol, shared_ref_cl, shared_start,
                shared_control_mode, shared_update):
    root = tk.Tk()
    app = EmioRealTimeGUI(root, shared_ref_ol, shared_ref_cl, 
                          shared_start, shared_control_mode, shared_update)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()

# -------------------------------------------------------------------------------
# GUI Class
# -------------------------------------------------------------------------------
class EmioRealTimeGUI:
    MOTOR_SCALE = np.pi / 2 / 100  # slider [-100..100] -> radians

    def __init__(self, root, shared_ref_ol, shared_ref_cl, 
                 shared_start, shared_control_mode, shared_update):
        self.root = root
        self.root.title('Emio Real Time Control')
        self.root.geometry("500x350")

        # ------- Variables -------
        # shared
        self.shared_ref_ol = shared_ref_ol
        self.shared_ref_cl = shared_ref_cl
        self.shared_start = shared_start
        self.shared_control_mode = shared_control_mode
        self.shared_update = shared_update

        # local
        self.start = False
        self.active = True
        self.control_mode = prm.ControlMode.OPEN_LOOP

        # ------- Information Frame -------
        info_frame = tk.Frame(root)
        info_frame.pack()
        info = ["Start", "Active", "Control"]
        info_values = ["False", "True", "Open Loop"]
        self.label_info = {}
        for i, item in enumerate(info):
            self.label_info[item] = tk.Label(
                    info_frame, 
                    text=f"{item}: {info_values[i]}", font=("Arial", 12))
            self.label_info[item].pack(side="left", padx=5, pady=5)

        # ------- Control Frame -------
        self.build_sliders()
        self.build_buttons()


    # --------------------------------------------------------------------------
    # Build methods
    # --------------------------------------------------------------------------
    def build_sliders(self):
        self.label_motors = []
        self.sliders_motor = []
        motor_label_frame = tk.Frame(self.root)
        motor_label_frame.pack()
        motor_slider_frame = tk.Frame(self.root)
        motor_slider_frame.pack()

        self.label_ref = []
        self.sliders_ref = []        
        ref_label_frame = tk.Frame(self.root)
        ref_label_frame.pack()
        ref_slider_frame = tk.Frame(self.root)
        ref_slider_frame.pack()

        for i in range(2):
            self.label_motors.append(
                self._build_label(motor_label_frame, text=f"Motor {i + 1}: 0.00 (rad)")
            )
            self.sliders_motor.append(
                self._build_slider(
                    motor_slider_frame,
                    command=lambda val, idx=i: self._motor_action(val, idx),
                )
            )

            self.label_ref.append(
                self._build_label(ref_label_frame, text=f"Ref {i + 1}: 0.00 (mm)")
            )
            self.sliders_ref.append(
                self._build_slider(
                    ref_slider_frame,
                    command=lambda val, idx=i: self._ref_action(val, idx),
                )
            )

        control_label_frame = tk.Frame(self.root)
        control_label_frame.pack()
        control_slider_frame = tk.Frame(self.root)
        control_slider_frame.pack()

        self.label_control = self._build_label(
            control_label_frame, text="Desired Control Mode: Open Loop"
 
        )
        self.slider_control = self._build_slider(
            control_slider_frame,
            command=self.slider_control_action,
            from_=0, to=1
        )

    # ----------------------------------------------------------
    def build_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        buttons = [
            ("Start", self.start_action),
            ("Switch Control", self.control_mode_action),
            ("Active", self.active_action),
        ]
        for name, action in buttons:
            tk.Button(button_frame, text=name, command=action).pack(side="left", padx=3)


    # --------------------------------------------------------------------------
    # Slider actions
    # --------------------------------------------------------------------------
    def _motor_action(self, val, index: int):
        if not self.start:
            self.sliders_motor[index].set(0)
            return
        cmd = float(val) * self.MOTOR_SCALE  # radians
        self.label_motors[index].config(text=f"Motor {index + 1}: {cmd:.2f} (rad)")
        if self.active:
            mode = prm.ControlMode(0)
            self._push_current_commands(mode)

    # ----------------------------------------------------------
    def _ref_action(self, val, index: int):
        if not self.start:
            self.sliders_ref[index].set(0)
            return
        cmd = float(val)  # mm
        self.label_ref[index].config(text=f"Ref {index + 1}: {cmd:.2f} (mm)")
        if self.active:
            mode = prm.ControlMode(1)
            self._push_current_commands(mode)

    # ----------------------------------------------------------
    def slider_control_action(self, val):
        if not self.start:
            self.slider_control.set(0)
            return
        self.control_mode = prm.ControlMode(int(val))
        self.label_control.config(text=f"Desired Control Mode: {self.control_mode.label}")

    # --------------------------------------------------------------------------
    # Button actions
    # --------------------------------------------------------------------------
    def start_action(self):
        if not self.start:
            self.start = True
            self.label_info["Start"].config(text="Start: True")
            with self.shared_start.get_lock():
                self.shared_start.value = self.start
            mode = prm.ControlMode(0)
            self._push_current_commands(mode)

    # ----------------------------------------------------------
    def active_action(self):
        if not self.start:
            return
        self.active = not self.active
        self.label_info["Active"].config(text=f"Active: {self.active}")

        if self.active:
            with self.shared_control_mode.get_lock():
                mode = prm.ControlMode(int(self.shared_control_mode.value)) 
            self._push_current_commands(mode)

    # ----------------------------------------------------------
    def control_mode_action(self):
        if not self.start:
            return
        with self.shared_control_mode.get_lock():
            self.shared_control_mode.value = int(self.control_mode)
        with self.shared_update.get_lock():
            self.shared_update.value = True

        if self.control_mode == prm.ControlMode.OPEN_LOOP:
            self.label_info["Control"].config(text="Control: Open Loop")
        else:
            self.label_info["Control"].config(text=f"Control: {self.control_mode.short}")

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def close_app(self):
        self.root.destroy()

    # ----------------------------------------------------------
    def _build_slider(self, frame, command, from_=-100, to=100):
        slider = tk.Scale(frame, from_=from_, to=to, orient="horizontal", command=command)
        slider.set(0)
        slider.pack(side="left", padx=3, pady=5)
        return slider

    # ----------------------------------------------------------
    def _build_label(self, frame, text):
        label = tk.Label(frame, text=text)
        label.pack(side="left", padx=3, pady=5)
        return label

    # ----------------------------------------------------------
    def _push_current_commands(self, mode):
        if mode == prm.ControlMode.OPEN_LOOP:
            pos = [float(self.sliders_motor[i].get()) for i in range(2)]
            with self.shared_ref_ol.get_lock():
                self.shared_ref_ol[0] = pos[0] * self.MOTOR_SCALE
                self.shared_ref_ol[1] = pos[1] * self.MOTOR_SCALE
        else:
            ref = [float(self.sliders_ref[i].get()) for i in range(2)]
            with self.shared_ref_cl.get_lock():
                self.shared_ref_cl[0] = ref[0]
                self.shared_ref_cl[1] = ref[1]

        with self.shared_update.get_lock():
            self.shared_update.value = True
