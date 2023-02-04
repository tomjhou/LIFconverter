from LifClass import LifClass
import tkinter as tk
from tkinter import ttk, filedialog
import os
from functools import partial

from basic_gui import basic_gui


PADDING_PIXELS = 5  # How much padding to put around GUI buttons
USE_TWO_BUTTON_COLUMNS = True  # If true, buttons are in 2 columns, otherwise will be in 1 column


class gui(basic_gui):

    root = None

    def __init__(self):

        super().__init__()
        self.skip_string_var = tk.StringVar(self.root, "skip")
        self.var_write_xml_metadata = tk.BooleanVar(self.root)
        self.format_string_var = tk.StringVar(self.root, "jpg")
        self.conversion_options = LifClass.Options()
        self.file_path = None

    def do_open_folder(self):

        self.file_path = filedialog.askdirectory()
        self.status_label_list[0].config(text=self.file_path)

    def do_open_file(self):

        self.file_path = filedialog.askopenfilename()
        self.status_label_list[0].config(text=self.file_path)

    def do_update_enabled_status_from_gui(self):
        enabled = (self.format_string_var.get() != "none") or (self.var_write_xml_metadata.get())
        self.set_enabled_status(enabled)

    def get_options(self):

        v = self.format_string_var.get()
        if v == "jpg":
            self.conversion_options.convert_format = LifClass.Options.Format.jpg
        elif v == "tiff":
            self.conversion_options.convert_format = LifClass.Options.Format.tiff
        elif v == "none":
            self.conversion_options.convert_format = LifClass.Options.Format.none
        else:
            self.conversion_options.convert_format = LifClass.Options.Format.jpg

        self.conversion_options.overwrite_existing = (self.skip_string_var.get() == "all")
        self.conversion_options.write_xml_metadata = self.var_write_xml_metadata.get()

    def start_convert_folder(self):

        # self.root.attributes('-topmost', True)  # Opened windows will be above all windows
        folder_path = filedialog.askdirectory()

        if folder_path != '':

            self.get_options()
            files = os.scandir(folder_path)

            f_list = list(files)

            num_files_done = 0
            num_images_done = 0

            x = 0
            for f in f_list:
                if not f.is_file():
                    continue

                path_ext = os.path.splitext(f)
                if path_ext[1] != '.lif':
                    continue

                x += 1

            num_files = x

            x = 0
            for f in f_list:
                if not f.is_file():
                    continue

                path_ext = os.path.splitext(f)
                if path_ext[1] != '.lif':
                    continue

                x += 1

                print(f'\nProcessing file {f.name}')
                self.status_label_list[0].config(text=f'({x}/{num_files}) {f.name}')
                self.root.update()
                l1 = LifClass(f.path, conversion_options=self.conversion_options)
                r = l1.convert()
                num_files_done += r[0]
                num_images_done += r[1]

            print(f'\nCompleted conversion of {num_images_done} images in {num_files_done} LIF files in folder\n')
        else:
            print('\nNo folder chosen.\n')
            self.status_label_list[0].config(text="No folder chosen")

    def start_convert_file(self):

        self.get_options()
        try:
            l1 = LifClass(conversion_options=self.conversion_options)
            self.status_label_list[0].config(text=l1.file_base_name)
            self.root.update()
            l1.convert()
        except LifClass.UserCanceled:
            self.status_label_list[0].config(text="User canceled")

    def start_convert_image(self):

        self.get_options()
        try:
            l1 = LifClass(conversion_options=self.conversion_options)
            self.status_label_list[0].config(text=l1.file_base_name)
            self.root.update()
            n = l1.prompt_select_image()
            l1.convert(n)
        except LifClass.UserCanceled:
            self.status_label_list[0].config(text="User canceled")

    def run_gui(self):

        #
        #  -------------------------------  <-- start of frame1, parent = root
        #  ||---------------------------||  <-- start of frame1b, parent = frame1
        #  ||           |  frame1f      ||
        #  || frame1c   |  frame1e      ||
        #  ||           |               ||
        #  ||---------------------------||  <-- end of frame1b
        #  ||---------------------------||
        #  ||  frame 1a checkboxes      ||  <-- frame1a, parent = frame1
        #  ||---------------------------||
        #  ||---------------------------||  <-- end of frame1
        #  ||-------------------------------||
        #  ||  frame1d Current filename     ||  <-- frame1d, parent = root
        #  ||-------------------------------||

        # Create GUI
        self.root.title(string="Jhou lab LIF converter")

        frame1 = tk.Frame(self.root)
        frame1.pack(side=tk.TOP, anchor='w', padx=15, pady=10)  #, fill=tk.X)

        frame1b = tk.Frame(frame1, borderwidth=5)
        frame1b.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Dictionary to create multiple buttons
        values = {"Convert data folder": self.start_convert_folder,
                  "Convert single .LIF file": self.start_convert_file,
                  "Exit": self.do_exit}

        self.button_list = self.add_boxed_button_column(frame1b, values)

        # Dictionary to create multiple radio buttons
        values = {"JPG (smallest files, recommended)": "jpg",
                  "TIFF (slightly higher quality, but much bigger file)": "tiff",
                  "None (use if only extracting XML header)": "none"}

        self.add_boxed_radio_button_column(frame1b, values, backing_var=self.format_string_var,
                                           command=self.do_update_enabled_status_from_gui,
                                           text="Conversion format")

        # Dictionary to create multiple buttons
        values = {"Skip files already converted (recommended)": "skip",
                  "Convert all files (will overwrites existing files)": "all"}

        self.add_boxed_radio_button_column(frame1b, values, backing_var=self.skip_string_var)

        frame1a = tk.Frame(frame1, borderwidth=5)
        frame1a.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=5)

        ttk.Checkbutton(frame1a, text="Write metadata to .xml file (if you don't know what this is, you probably don't need it)",
                        variable=self.var_write_xml_metadata,
                        command=self.do_update_enabled_status_from_gui).\
            pack(side=tk.TOP, anchor=tk.NW)

        values = ["Current file:",
                  "Current image:"]

        self.status_label_list = self.add_status_text_lines(self.root, values)

        # Place in top left corner of screen
        self.root.geometry("+%d+%d" % (PADDING_PIXELS, PADDING_PIXELS))

        # Force window to show, otherwise winfo_geometry() will return zero
        frame1.update()
        print("Created main window with geometry " + self.root.winfo_geometry())

        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        tk.mainloop()

        print("Finished")


obj = gui()
obj.run_gui()
