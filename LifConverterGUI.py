import os
import tkinter as tk
from tkinter import ttk, filedialog
from functools import partial

from LifClass import LifClass
from basic_gui import basic_gui, basic_flag

PADDING_PIXELS = 5  # How much padding to put around GUI buttons
USE_TWO_BUTTON_COLUMNS = True  # If true, buttons are in 2 columns, otherwise will be in 1 column


class gui(basic_gui):
    root = None
    stopFlag = basic_flag()
    lif_object: LifClass = None
    output_folder = None

    def __init__(self):

        super().__init__()
        self.var_recursive = tk.BooleanVar(self.root)
        self.var_write_xml_metadata = tk.BooleanVar(self.root)
        self.var_rotate180 = tk.BooleanVar(self.root, True)
        self.skip_string_var = tk.StringVar(self.root, "skip")
        self.format_string_var = tk.StringVar(self.root, LifClass.Options.Format.jpg.name)
        self.conversion_options = LifClass.Options()
        self.file_path = None

    def do_open_output_folder(self):

        if self.output_folder is not None:
            os.startfile(self.output_folder)

    def do_update_enabled_status_from_gui(self):
        enabled = (self.format_string_var.get() != "none") or (self.var_write_xml_metadata.get())
        self.set_enabled_status(enabled)

    def get_options_from_gui(self):

        v = self.format_string_var.get()
        self.conversion_options.convert_format = LifClass.Options.Format[v]

        self.conversion_options.overwrite_existing = (self.skip_string_var.get() == "all")
        self.conversion_options.write_xml_metadata = self.var_write_xml_metadata.get()
        self.conversion_options.rotate180 = self.var_rotate180.get()

    def get_file_list(self, folder_path):

        final_list = []

        files = os.scandir(folder_path)

        f_list = list(files)

        recursive = self.var_recursive.get()

        for f in f_list:
            if f.is_dir():
                if recursive:
                    final_list = final_list + self.get_file_list(f)
                continue

            if not f.is_file():
                continue

            path_ext = os.path.splitext(f)
            if path_ext[1] != '.lif':
                # Exclude files that are not .lif
                continue

            final_list.append(f)

        return final_list

    def start_convert_folder(self):

        # self.root.attributes('-topmost', True)  # Opened windows will be above all windows
        folder_path = filedialog.askdirectory()

        if folder_path == '':
            print('\nNo folder chosen.\n')
            self.set_status_text(0, "No folder chosen")
            return

        self.output_folder = folder_path

        file_list = self.get_file_list(folder_path)

        self.get_options_from_gui()

        num_files_done = 0
        num_images_done = 0
        num_images_skipped = 0
        num_images_error = 0
        num_xml = 0

        num_files = len(file_list)

        try:
            for x in range(num_files):

                if self.stopFlag.check():
                    raise LifClass.UserCanceled

                f = file_list[x]
                print(f'\nProcessing file "{f.name}"')
                self.set_status_text(0, f'({x + 1} of {num_files}) {f.name}')
                self.set_status_text(1, ("Folder:", os.path.dirname(f.path)))

                self.root.update()
                self.lif_object = LifClass(f.path, conversion_options=self.conversion_options, root_window=self.root)
                self.lif_object.convert()
                num_files_done += 1
                num_images_done += self.lif_object.num_images_converted
                num_images_skipped += self.lif_object.num_images_skipped
                num_images_error += self.lif_object.num_images_error
                num_xml += self.lif_object.num_xml_written
        except LifClass.UserCanceled:
            # Add any final images converted before cancellation
            if self.lif_object is not None:
                num_images_done += self.lif_object.num_images_converted
                num_images_skipped += self.lif_object.num_images_skipped
                num_images_error += self.lif_object.num_images_error
                num_xml += self.lif_object.num_xml_written
        except Exception as e:
            print('Unexpected exception ' + str(e))

        print(f'\nConverted {num_images_done} images in {num_files_done} LIF files. ', end='')
        if num_xml > 0:
            print(f'Wrote {num_xml} XML files. ', end='')
        print(f'Skipped {num_images_skipped} images, encountered errors in {num_images_error} images/files\n')

    def start_convert_file(self):

        file_path = filedialog.askopenfilename(filetypes=[("LIF files", "*.lif")])
        if file_path == "":
            self.set_status_text(0, "User canceled")
            return

        base_name = os.path.basename(file_path)
        self.output_folder = os.path.dirname(file_path)
        print(f'\nProcessing file "{base_name}"')
        self.set_status_text(0, base_name)
        # Update GUI now because opening/converting lif file might take a long time
        self.root.update()

        self.get_options_from_gui()
        # If converting just one file, then always overwrite
        self.conversion_options.overwrite_existing = True
        try:
            self.lif_object = LifClass(file_path, conversion_options=self.conversion_options, root_window=self.root)
            self.lif_object.convert()
        except LifClass.UserCanceled:
            self.set_status_text(0, "User canceled")
        else:
            print(f'\nConverted {self.lif_object.num_images_converted} images. ', end='')
            if self.lif_object.num_xml_written > 0:
                print(f'Wrote {self.lif_object.num_xml_written} XML files. ', end='')
            print(
                f'Skipped {self.lif_object.num_images_skipped} images, encountered errors in {self.lif_object.num_images_error} images/files\n')

    def start_convert_image(self):

        self.get_options_from_gui()
        try:
            self.lif_object = LifClass(conversion_options=self.conversion_options, root_window=self.root)
            self.set_status_text(0, self.lif_object.file_base_name)
            self.root.update()
            n = self.lif_object.prompt_select_image()
            self.lif_object.convert(n)
        except LifClass.UserCanceled:
            self.set_status_text(0, text="User canceled")
        else:
            print(f'\nConverted {self.lif_object.num_images_converted} images')

    def operation_end(self):
        # Re-enable the "stop conversion" button
        self.set_widget_state(self.button_list[-2], True)
        # Re-enable remaining buttons
        super().operation_end()

    def run_gui(self):

        #
        #  -------------------------------  <-- start of frame1, parent = root
        #  ||---------------------------||  <-- start of frame1b, parent = frame1
        #  ||           |   Radio       ||
        #  ||  Buttons  |   Buttons     ||
        #  ||           |               ||
        #  ||---------------------------||  <-- end of frame1b
        #  ||---------------------------||
        #  ||  frame 1a checkboxes      ||  <-- frame1a, parent = frame1
        #  ||---------------------------||
        #  ||---------------------------||  <-- end of frame1
        #  ||  Status text boxes            ||

        # Create GUI
        self.root.title(string="Jhou lab LIF converter")

        frame1 = tk.Frame(self.root)
        frame1.pack(side=tk.TOP, anchor='w', padx=15, pady=10)

        frame1b = tk.Frame(frame1, borderwidth=5)
        frame1b.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Dictionary to create multiple buttons
        values = {"Convert single LIF file": self.start_convert_file,
                  "Convert folder": self.start_convert_folder,}

        self.button_list = self.add_boxed_button_column(frame1b, values, side=tk.LEFT, fill=tk.X)

        # Radio buttons for output options
        values = {"JPG (smallest files, highly recommended)": LifClass.Options.Format.jpg,
                  "TIFF": LifClass.Options.Format.tiff,
                  "None (use if extracting XML header)": LifClass.Options.Format.none}

        (f, elt) = self.add_boxed_radio_button_column(frame1b, values, backing_var=self.format_string_var,
                                                      side=tk.TOP, fill=tk.X,
                                                      padx=15, pady=8,
                                                      command=self.do_update_enabled_status_from_gui,
                                                      text="Output options")

        cb = ttk.Checkbutton(f, text="Rotate 180 degrees?", variable=self.var_rotate180)
        cb.pack(before=elt, side=tk.TOP, anchor=tk.NW, padx=10, pady=(6, 3))

        # Radio buttons for folder options
        values = {"Skip already converted files (recommended)": "skip",
                  "Convert all (overwrites old output)": "all"}

        (f, elt) = self.add_boxed_radio_button_column(frame1b, values, backing_var=self.skip_string_var,
                                                      side=tk.TOP, fill=tk.X,
                                                      padx=15, pady=8,
                                                      text="Folder convert options")

        cb = ttk.Checkbutton(f, text="Include sub-folders?", variable=self.var_recursive)
        cb.pack(before=elt, side=tk.TOP, anchor=tk.NW, padx=10, pady=(6, 3))

        frame1a = tk.Frame(frame1, borderwidth=5)
        frame1a.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=5)

        ttk.Checkbutton(frame1a, text="Extract XML header (if you don't know what this is, you probably don't need it)",
                        variable=self.var_write_xml_metadata,
                        command=self.do_update_enabled_status_from_gui). \
            pack(side=tk.TOP, anchor=tk.NW)

        values = ["Current file:",
                  "Status:"]

        self.add_status_text_lines(self.root, values)

        b = tk.Button(self.root, text="Open output folder", command=self.do_open_output_folder)
        b.pack(side=tk.TOP, padx=15, pady=(1, 10), ipadx=20, ipady=10)

        # Place in top left corner of screen
        self.root.geometry("+%d+%d" % (PADDING_PIXELS, PADDING_PIXELS))

        # Force window to show, otherwise winfo_geometry() will return zero
        frame1.update()
        print("Created main window with geometry " + self.root.winfo_geometry())

        print("\nDon't close this window, as it will report useful messages during conversion.")

        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        super().run_gui()

        print("Finished")


print('Creating GUI object')
obj = gui()
print('Launching GUI')
obj.run_gui()
