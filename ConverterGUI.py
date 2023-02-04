from LifClass import LifClass
import tkinter as tk
from tkinter import ttk, filedialog
import os


PADDING_PIXELS = 5  # How much padding to put around GUI buttons
USE_TWO_BUTTON_COLUMNS = True  # If true, buttons are in 2 columns, otherwise will be in 1 column


class gui:

    root = None

    def __init__(self):

        root = tk.Tk()
        self.root = root
        self.var_skip_converted = tk.BooleanVar(root)
        self.var_skip_converted.set(True)
        self.var_write_xml_metadata = tk.BooleanVar(root)
        self.tk_status_text_label = None
        self.format_string_var = tk.StringVar(root, "jpg")
        self.conversion_options = LifClass.Options()
        self.file_path = None

    def do_exit(self):

        self.root.quit()

    def do_open_folder(self):

        self.file_path = filedialog.askdirectory()
        self.tk_status_text_label.config(text=self.file_path)

    def do_open_file(self):

        self.file_path = filedialog.askopenfilename()
        self.tk_status_text_label.config(text=self.file_path)

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

        self.conversion_options.overwrite_existing = not self.var_skip_converted.get()
        self.conversion_options.write_xml_metadata = self.var_write_xml_metadata.get()

    def run_gui(self):

        # Create GUI
        self.root.title(string="Choose")

        frame1 = tk.Frame(self.root, highlightbackground="black", highlightthickness=1, relief="flat", borderwidth=5)
        frame1.pack(side=tk.TOP, fill=tk.X, padx=15, pady=10)

        # Internal padding (makes buttons larger). As opposed to padx and pady, which are EXTERNAL padding values
        # that add more space between buttons
        ipadding = 10

        # Checkbox and save info

        frame1a = tk.Frame(frame1, borderwidth=5)
        frame1a.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)

        ttk.Checkbutton(frame1a, text="Skip files that are already converted (recommended)",
                        variable=self.var_skip_converted).pack(side=tk.TOP, anchor=tk.NW)

        ttk.Checkbutton(frame1a, text="Write XML metadata to .txt file (not usually necessary)",
                        variable=self.var_write_xml_metadata).pack(side=tk.TOP, anchor=tk.NW)

        frame1c = tk.Frame(frame1, borderwidth=5)
        frame1c.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        butt = ttk.Button(frame1c, text="Choose data folder", command=self.start_convert_folder)
        butt.pack(fill=tk.X, padx=10, pady=5, ipadx=ipadding, ipady=ipadding)

        butt = ttk.Button(frame1c, text="Choose single .LIF file", command=self.start_convert_file)
        butt.pack(fill=tk.X, padx=10, pady=5, ipadx=ipadding, ipady=ipadding)

        butt = ttk.Button(frame1c, text="Stop conversion", command=self.do_exit)
        butt.pack(fill=tk.X, padx=10, pady=5, ipadx=ipadding, ipady=ipadding)

        butt = ttk.Button(frame1c, text="Exit", command=self.do_exit)
        butt.pack(fill=tk.X, padx=10, pady=5, ipadx=ipadding, ipady=ipadding)

        frame1d = tk.Frame(frame1, borderwidth=5)
        frame1d.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        tk.Label(frame1d, text="Current file: ").pack(side=tk.LEFT)
        self.tk_status_text_label = tk.Label(frame1d, borderwidth=1, anchor="w", relief="sunken")
        self.tk_status_text_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        frame2 = tk.Frame(self.root, highlightbackground="black", highlightthickness=1, relief="flat", borderwidth=5)
        frame2.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)

        if not USE_TWO_BUTTON_COLUMNS:
            ttk.Label(frame2, text="Choose program:").pack(fill=tk.X, pady=5)

        # Dictionary to create multiple buttons
        values = {"JPG": "jpg",
                  "TIFF": "tiff",
                  "None": "none"}

        # Loop is used to create multiple Radiobuttons
        # rather than creating each button separately
        for (text, value) in values.items():
            tk.Radiobutton(frame2, text=text, variable=self.format_string_var, value=value).pack(side=tk.LEFT, ipady=5)

        # Place in top left corner of screen
        self.root.geometry("+%d+%d" % (PADDING_PIXELS, PADDING_PIXELS))

        # Force window to show, otherwise winfo_geometry() will return zero
        frame1.update()
        print("Created main window with geometry " + self.root.winfo_geometry())

        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        tk.mainloop()

        print("Finished")

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
                self.tk_status_text_label.config(text=f'({x}/{num_files}) {f.name}')
                self.root.update()
                l1 = LifClass(f.path, conversion_options=self.conversion_options)
                r = l1.convert()
                num_files_done += r[0]
                num_images_done += r[1]

            print(f'\nCompleted conversion of {num_images_done} images in {num_files_done} LIF files in folder\n')
        else:
            print('\nNo folder chosen.\n')
            self.tk_status_text_label.config(text="No folder chosen")

    def start_convert_file(self):

        self.get_options()
        try:
            l1 = LifClass(conversion_options=self.conversion_options)
            self.tk_status_text_label.config(text=l1.file_base_name)
            self.root.update()
            l1.convert()
        except LifClass.UserCanceled:
            self.tk_status_text_label.config(text="User canceled")

    def start_convert_image(self):

        self.get_options()
        try:
            l1 = LifClass(conversion_options=self.conversion_options)
            self.tk_status_text_label.config(text=l1.file_base_name)
            self.root.update()
            n = l1.prompt_select_image()
            l1.convert(n)
        except LifClass.UserCanceled:
            self.tk_status_text_label.config(text="User canceled")


obj = gui()
obj.run_gui()
