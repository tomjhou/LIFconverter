import tkinter as tk
import enum
from tkinter import ttk, filedialog
from functools import partial
import ctypes
import threading
from typing import Optional

PADDING_PIXELS = 5  # How much padding to put around GUI buttons
USE_TWO_BUTTON_COLUMNS = True  # If true, buttons are in 2 columns, otherwise will be in 1 column


class basic_flag:

    def __init__(self, root_window=None):
        self.flag = False
        self.root_window = root_window

    def set(self):
        self.flag = True

    def check(self):
        if self.root_window is not None:
            self.root_window.update()
        if self.flag:
            print('Stop flag triggered')
            self.flag = False
            return True
        else:
            return False


class basic_gui:

    class ThreadRunning(Exception):
        # Custom exception class, no code needed.
        # Raise this exception to prevent button handler
        # from calling session_end code if operation is running on background thread
        pass

    class thread_with_exception(threading.Thread):
        def __init__(self, *args, **kwargs):
            threading.Thread.__init__(self, *args, **kwargs)
            self.name = "conversion_thread_678"

        def get_id(self):

            # returns id of the respective thread
            if hasattr(self, '_thread_id'):
                return self._thread_id
            for id, thread in threading._active.items():
                if thread is self:
                    return id

            return None

        def raise_exception(self):
            thread_id = self.get_id()
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                             ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print('Exception raise failure')

    root = None
    lock1 = threading.Lock()
    current_thread: Optional[thread_with_exception] = None

    def __init__(self):

        root = tk.Tk()
        self.root = root
        self.button_list = []
        self.status_label_list = []

    def do_cancel(self):
        self.lock1.acquire()
        if self.current_thread is not None:
            # Disable cancel button while awaiting cancellation
            self.set_widget_state(self.button_cancel, False)
            self.set_widget_text(self.button_cancel, "Cancel pending...")
            self.current_thread.raise_exception()
        self.lock1.release()

    def do_exit(self):
        self.root.quit()

    @staticmethod
    def set_widget_state(widget, state: bool):
        if widget is None:
            return
        if state:
            widget["state"] = "enabled"
        else:
            widget["state"] = "disabled"

    @staticmethod
    def set_widget_text(widget, text):
        if widget is None:
            return
        widget["text"] = text

    def set_enabled_status(self, enabled: bool):
        for b in self.button_list:
            self.set_widget_state(b, enabled)

    def add_boxed_radio_button_column(self, parent_frame, button_names=None,
                                      backing_var=None, command=None,
                                      side=None, fill=None,
                                      padx=0, pady=0, text=""):

        if button_names is None:
            button_names = {}
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
            tk.Radiobutton(parent_frame, text=text, variable=backing_var, value=value, command=command). \
                pack(side=tk.TOP, anchor='w', ipady=5)

    def add_boxed_button_column(self, parent_frame, button_names, side=None, fill=None):

        frame = tk.Frame(parent_frame, highlightbackground="black", highlightthickness=1, relief="flat", borderwidth=5)
        frame.pack(side=side, fill=fill, padx=2, pady=2)

        frame_inset = tk.Frame(frame)  # , highlightbackground="black", highlightthickness=1)
        frame_inset.pack(anchor=tk.CENTER, pady=10)
        return self.add_button_column(frame_inset, button_names)

    def add_button_column(self, parent_frame, button_names):

        inner_padding = 10

        button_list = []
        button_index = 0
        for (text, value) in button_names.items():
            butt = ttk.Button(parent_frame, text=text, command=partial(self.handle_button, value))
            butt.pack(fill=tk.X, padx=10, pady=5, ipadx=inner_padding, ipady=inner_padding)
            button_list.append(butt)
            button_index += 1

        butt = ttk.Button(parent_frame, text="Cancel", command=partial(self.do_cancel))
        butt.pack(fill=tk.X, padx=10, pady=5, ipadx=inner_padding, ipady=inner_padding)
        self.button_cancel = butt

        butt = ttk.Button(parent_frame, text="Exit", command=partial(self.do_exit))
        butt.pack(fill=tk.X, padx=10, pady=5, ipadx=inner_padding, ipady=inner_padding)
        self.button_exit = butt

        return button_list

    def operation_end(self):
        # Call this at end of operation to re-enable buttons
        self.set_enabled_status(True)

    def handle_button(self, cmd):
        # Disable buttons while conversion is taking place
        self.set_enabled_status(False)
        self.current_thread = self.thread_with_exception(target=partial(self._threaded_worker, cmd))
        # Start conversion in background
        self.current_thread.start()

    def _threaded_worker(self, cmd):
        try:
            cmd()
        except Exception as e:
            print('Conversion exception: ' + str(e))
        finally:
            self.lock1.acquire()
            print('Conversion ended')
            self.operation_end()
            self.set_widget_state(self.button_cancel, True)
            self.set_widget_text(self.button_cancel, "Cancel")
            self.current_thread = None
            self.lock1.release()

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

    def run_gui(self):
        """
            Runs GUI loop. This function will not return until cancel is requested
        """
        tk.mainloop()
