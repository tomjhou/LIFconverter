from readlif.reader import LifFile
import tkinter as tk
from tkinter import filedialog
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
import time
import cv2
import os


class LifClass(LifFile):

    def __init__(self, file_path=""):

        if file_path == "":

            root = tk.Tk()
            root.withdraw()

            file_path = filedialog.askopenfilename(filetypes=[("LIF files", "*.lif")])

            #            [filename, pathname] = uigetfile({'*.lif', 'Leica Image Format (*.lif)'})
            if file_path == "":
                raise 'No file selected, will quit\n'

        self.file_path = file_path
        LifFile.__init__(self, file_path)

    def convert(self):

        # Access a specific image directly
        # img_0 = new.get_image(0)
        # Create a list of images using a generator
        img_list = [i for i in self.get_iter_image()]

        is_z_stack = False

        xml_images = self.xml_root.findall("./Element/Children/Element")
        for n in range(len(img_list)):

            if img_list[n].dims.m > 1:
                # This is a set of unmerged tiles. Just skip
                continue

            # Determine whether this is a z-stack
            is_z_stack = img_list[n].dims.z > 1

            xml_img = xml_images[n].find("./Data/Image")
            xml_chans = xml_img.findall("./ImageDescription/Channels/ChannelDescription")
            n_chan = len(xml_chans)
            xml_scales = xml_img.findall("./Attachment/ChannelScalingInfo")

            bit_depth = img_list[n].bit_depth

            # bit_depth is a list with one element per channel.
            if len(bit_depth) > 1:
                bit_depth = bit_depth[0]

            if bit_depth == 16:
                pixel_type_string = "uint16"
                max_val = 65535
                pixel_type = np.int16
            elif bit_depth == 8:
                pixel_type_string = "uint8"
                max_val = 255
                pixel_type = np.int8
            else:
                pixel_type_string = "uint16"
                max_val = 65535
                pixel_type = np.int16

            img_green = None
            img_red = None
            img_blue = None

            for m in range(n_chan):

                color = xml_chans[m].attrib["LUTName"]
                print(f'Generating image for color {color}: ')
                xml_scale = xml_scales[-(n_chan - m)]
                white_value = xml_scale.attrib["WhiteValue"]
                black_value = xml_scale.attrib["BlackValue"]

                white_value = float(white_value)
                black_value = float(black_value)

                start = time.time()

                # Access a specific item
                f = img_list[n].get_frame(z=0, t=0, c=m)
                # Iterate over different items
                # frame_list   = [i for i in img_0.get_iter_t(c=0, z=0)]
                # z_list       = [i for i in img_0.get_iter_z(t=0, c=0)]
                # channel_list = [i for i in img_0.get_iter_c(t=0, z=0)]

                ar = np.array(f)

                d = ar.shape

                scale = 1.0 / (white_value - black_value)

                offset1 = black_value * max_val

                # Rescale image intensity with respect to black_level and white_level
                for row in range(d[0]):
                    one_row = ar[row,].astype(float)
                    one_row = (one_row - offset1) * scale
                    one_row[one_row < 0] = 0
                    one_row[one_row > 255] = 255
                    ar[row,] = one_row.astype(pixel_type)

                end = time.time()
                print(f'  Completed in {end - start} seconds.')

                # plt.imshow(ar)  # , interpolation='nearest')

                if color == "Green":
                    img_green = ar
                elif color == "Red":
                    img_red = ar
                elif color == "Blue":
                    img_blue = ar

            # Now merge channels into a single image
            if img_blue is None:
                img_blue = np.zeros(d, dtype=pixel_type_string)
            if img_red is None:
                img_red = np.zeros(d, dtype=pixel_type_string)
            if img_green is None:
                img_green = np.zeros(d, dtype=pixel_type_string)

            # imwrite requires BGR order
            merged = np.dstack((img_blue, img_green, img_red))

            paths = os.path.splitext(img_list[n].filename)
            new_path = paths[0] + "_" + img_list[n].name + "_merged.jpg"
            print('Writing merged file: ' + new_path)
            start = time.time()
            cv2.imwrite(new_path, merged, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            end = time.time()
            print(f'  Completed in {end - start} seconds.')





