import tkinter as tk

class EmioRealTimeGUI:
    def __init__(self, root, shared_ref, shared_start, shared_update):
        self.root = root
        self.root.title('Emio Real Time Control')
        self.root.geometry("500x350")

        # shared Variables
        self.shared_ref = shared_ref
        self.shared_start = shared_start
        self.shared_update = shared_update

        # app variable
        self.start = False
        self.active = True

        # Information Frame
        info_frame = tk.Frame(root)
        info_frame.pack()
        info = ["Start", "Active"]
        info_values = ["False", "True"]
        self.label_info = {}
        for i, item in enumerate(info):
            self.label_info[item] = tk.Label(info_frame, text=f"{item}: {info_values[i]}", font=("Arial", 12))
            self.label_info[item].pack(side="left", padx=5, pady=5)

        # Reference Sliders
        ref_label_frame = tk.Frame(root)
        ref_label_frame.pack()
        ref_slider_frame = tk.Frame(root)
        ref_slider_frame.pack()

        self.label_ref1 = tk.Label(ref_label_frame, text='Ref 1: 0.00 (mm)')
        self.label_ref1.pack(side="left", padx=3, pady=5)
        self.slider_ref1 = tk.Scale(ref_slider_frame, from_=-100, to=100, orient='horizontal', command=self.slider_ref1_action)
        self.slider_ref1.pack(side="left", padx=3, pady=5)
        self.slider_ref1.set(0)

        self.label_ref2 = tk.Label(ref_label_frame, text='Ref 2: 0.00 (mm)')
        self.label_ref2.pack(side="left", padx=3, pady=5)
        self.slider_ref2 = tk.Scale(ref_slider_frame, from_=-100, to=100, orient='horizontal', command=self.slider_ref2_action)
        self.slider_ref2.pack(side="left", padx=3, pady=5)
        self.slider_ref2.set(0)

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        self.start_button = tk.Button(button_frame, text="Start", command=self.start_action)
        self.start_button.pack(side='left', padx=3)

        self.active_button = tk.Button(button_frame, text="Active", command=self.active_action)
        self.active_button.pack(side='right', padx=3)


    def slider_ref1_action(self, val):
        command = float(val)
        self.label_ref1.config(text=f'Ref 1: {command:.2f} (mm)')
        with self.shared_ref.get_lock():
            if self.active:
                self.shared_ref[0] = command
                self.shared_update.value = True

    def slider_ref2_action(self, val):
        command = float(val)
        self.label_ref2.config(text=f'Ref 2: {command:.2f} (mm)')
        with self.shared_ref.get_lock():
            if self.active:
                self.shared_ref[1] = command
                self.shared_update.value = True

    def start_action(self):
        self.start = not self.start
        with self.shared_start.get_lock():
            self.shared_start.value = self.start
        if self.start:
            self.label_info["Start"].config(text="Start: True")
            with self.shared_ref.get_lock():
                self.shared_ref[0] = self.slider_ref1.get()
                self.shared_ref[1] = self.slider_ref2.get()
                self.shared_update.value = True
        else:
            self.label_info["Start"].config(text="Start: False")

    def active_action(self):
        self.active = not self.active
        if self.active:
            self.label_info["Active"].config(text="Active: True")
            self.shared_ref[0] = self.slider_ref1.get()
            self.shared_ref[1] = self.slider_ref2.get()
            self.shared_update.value = True
        else:
            self.label_info["Active"].config(text="Active: False")

    def close_app(self):
        self.root.destroy()
