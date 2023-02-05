import tkinter as tk
import enum
from tkinter import ttk, filedialog
from functools import partial


PADDING_PIXELS = 5  # How much padding to put around GUI buttons
USE_TWO_BUTTON_COLUMNS = True  # If true, buttons are in 2 columns, otherwise will be in 1 column


class basic_flag:

    def __init__(self):
        self.flag = False

    def set(self):
        self.flag = True

    def check(self):
        x = self.flag
        self.flag = False
        return x


class basic_gui:

    root = None

    def __init__(self):

        root = tk.Tk()
        self.root = root
        self.button_list = []
        self.status_label_list = []

    def do_exit(self):

        self.root.quit()

    def set_enabled_status(self, enabled, exclude_last=2):
        if enabled:
            s = "enabled"
        else:
            s = "disabled"

        if exclude_last:
            # Exclude last n buttons, where n is specified in arguments
            bl = self.button_list[:-exclude_last]
        else:
            bl = self.button_list

        for b in bl:
            b["state"] = s

        self.root.update()

    def add_boxed_radio_button_column(self, parent_frame, button_names={},
                                      backing_var=None, command=None,
                                      side=None, fill=None,
                                      padx=0, pady=0, text=""):

        useLabelFrame = True

        if useLabelFrame:
            # Label frame is lighter and allows text label. We use it here just to match the appearance of format box
            frame = tk.LabelFrame(parent_frame, text=text)
        else:
            frame = tk.Frame(parent_frame, highlightbackground="black",
                             highlightthickness=1, relief="flat", borderwidth=5)

        frame.pack(side=side, fill=fill, padx=padx, pady=pady)

        self.add_radio_button_column(frame, button_names, backing_var, command)

    @staticmethod
    def add_radio_button_column(parent_frame, button_names, backing_var, command=None):

        for (text, value) in button_names.items():
            if isinstance(value, enum.Enum):
                # If enumerated type, then convert to string
                value = value.name
            tk.Radiobutton(parent_frame, text=text, variable=backing_var, value=value, command=command).\
                pack(side=tk.TOP, anchor='w', ipady=5)

    def add_boxed_button_column(self, parent_frame, button_names, side=None, fill=None):

        frame = tk.Frame(parent_frame, highlightbackground="black", highlightthickness=1, relief="flat", borderwidth=5)
        frame.pack(side=side, fill=fill, padx=2, pady=2)

        frame_inset = tk.Frame(frame)  #, highlightbackground="black", highlightthickness=1)
        frame_inset.pack(anchor=tk.CENTER, pady=10)
        return self.add_button_column(frame_inset, button_names)

    def add_button_column(self, parent_frame, button_names):

        inner_padding = 10

        button_list = []
        for (text, value) in button_names.items():
            butt = ttk.Button(parent_frame, text=text, command=partial(self.handle_button, value))
            butt.pack(fill=tk.X, padx=10, pady=5, ipadx=inner_padding, ipady=inner_padding)
            button_list.append(butt)

        return button_list

    def handle_button(self, cmd):
        # Disable buttons while conversion is taking place
        self.set_enabled_status(False)
        try:
            cmd()
        finally:
            self.set_enabled_status(True)

    def add_status_text_lines(self, parent_frame, values):

        frame = tk.Frame(parent_frame, borderwidth=5)
        frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        frame.columnconfigure(1, weight=1)

        label_list = []

        for x in range(len(values)):
            tk.Label(frame, text=values[x], anchor="e", justify=tk.RIGHT).grid(row=x, column=0, sticky=tk.E)
            lab = tk.Label(frame, borderwidth=1, anchor="w", relief="sunken")
            lab.grid(row=x, column=1, sticky=tk.W + tk.E)

            label_list.append(lab)

        return label_list


