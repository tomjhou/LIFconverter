from readlif.reader import LifFile
import tkinter as tk
from tkinter import filedialog
import numpy as np
import time
import cv2
import os


class LifClass(LifFile):

    def __init__(self, file_path=""):

        if file_path == "":

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)  # Opened windows will be active. above all windows despite selection.

            file_path = filedialog.askopenfilename(filetypes=[("LIF files", "*.lif")])

            #            [filename, pathname] = uigetfile({'*.lif', 'Leica Image Format (*.lif)'})
            if file_path == "":
                raise 'No file selected, will quit\n'

        self.file_name = os.path.basename(file_path)
        self.file_path = file_path

        try:
            LifFile.__init__(self, file_path)
        except Exception as e:
            print(f'  Error encounterd while opening LIF file: {e}')
            print('  Please check whether file is corrupted.')

    def prompt_select_image(self):

        img_list = [i for i in self.get_iter_image()]
        print(f'\nChoose image to convert within file "{self.file_name}":')
        for n in range(len(img_list)):
            print(f'{n}: "{img_list[n].name}", width {img_list[n].dims.x} x height {img_list[n].dims.y}')
        answer = input('Select image (default = 0): ')
        if answer == '':
            answer = '0'

        return int(answer)

    # Convert one or more images in a single file
    def convert(self, n=-1):

        # Access a specific image directly
        # img_0 = new.get_image(0)
        # Create a list of images using a generator
        try:
            img_list = [i for i in self.get_iter_image()]
        except Exception as e:
            print(f'  Error while reading image list: {e}')
            print('  Unable to convert file, will skip')
            return

        xml_metadata = self.xml_root.findall("./Element/Children/Element/Data/Image")

        # Write metadata to XML file
        paths = os.path.splitext(self.file_path)
        xml_path = paths[0] + ".xml"

        with open(xml_path, 'w') as f:
            f.write(self.xml_header)

        if n < 0:
            # Convert all images in file
            print(f'Found {len(img_list)} images in file "{self.file_name}".')
            for n in range(len(img_list)):
                print(f'  Processing image {img_list[n].name}')
                self.convert_image(img_list[n], xml_metadata[n])
        else:
            # Convert single image
            self.convert_image(img_list[n], xml_metadata[n])

    # Convert a single image within this file.
    def convert_image(self, img, xml_metadata):

        if img.dims.m > 1:
            # This is a set of unmerged tiles. Just skip
            return

        # Determine whether this is a z-stack
        z_depth = img.dims.z

        xml_chans = xml_metadata.findall("./ImageDescription/Channels/ChannelDescription")
        n_chan = len(xml_chans)
        xml_scales = xml_metadata.findall("./Attachment/ChannelScalingInfo")

        bit_depth = img.bit_depth

        # bit_depth is a list with one element per channel.
        if len(bit_depth) > 1:
            bit_depth = bit_depth[0]

        if bit_depth == 16:
            pixel_type_string = "uint16"
            max_val = 65535
            # Must use unsigned ints, otherwise values above 50% will become negative and truncated to black.
            pixel_type = np.uint16
        elif bit_depth == 8:
            pixel_type_string = "uint8"
            max_val = 255
            pixel_type = np.uint8
        else:
            pixel_type_string = "uint16"
            max_val = 65535
            pixel_type = np.uint16

        img_green = None
        img_red = None
        img_blue = None
        img_cyan = None

        print(f'  Image size is: width {img.dims.x} x height {img.dims.y}')
        print(f'  Found {n_chan} color channels, bit depth is {bit_depth}')

        for m in range(n_chan):

            color = xml_chans[m].attrib["LUTName"]
            print(f'  Generating image for color {color}: ')
            if (n_chan - m) <= len(xml_scales):
                xml_scale = xml_scales[-(n_chan - m)]
                white_value = xml_scale.attrib["WhiteValue"]
                black_value = xml_scale.attrib["BlackValue"]
            else:
                # Some images, like snapshots, may not have ChannelScalingInfo. Just use defaults.
                white_value = 1
                black_value = 0

            white_value = float(white_value)
            black_value = float(black_value)

            start = time.time()

            if z_depth > 1:
                print(f'      Found z-stack of depth {z_depth}, will scan all images and select brightest value for '
                      f'each pixel (which may come from different z-planes).')
                for k in range(z_depth):
                    print('.', end="")
                    f = img.get_frame(z=k, t=0, c=m)
                    if k == 0:
                        ar = np.array(f)
                    else:
                        ar = np.maximum(ar, np.array(f))
                print()
            else:
                # Access a specific item
                f = img.get_frame(z=0, t=0, c=m)
                ar = np.array(f)

            # Iterate over different items
            # frame_list   = [i for i in img_0.get_iter_t(c=0, z=0)]
            # z_list       = [i for i in img_0.get_iter_z(t=0, c=0)]
            # channel_list = [i for i in img_0.get_iter_c(t=0, z=0)]

            d = ar.shape

            scale = 1.0 / (white_value - black_value)

            offset1 = round(black_value * max_val)    # Using round() because that seems to match LASX

            # Bin several rows together to speed up processing. This is more advantageous
            # if rows are small. As they get bigger, the advantage diminishes, and may even
            # reverse for unknown reasons (memory limit?)
            chunk_h = img.dims.x    #  * bit_depth / 8
            if chunk_h < 4000:
                chunk_v = 32
            elif chunk_h < 8000:
                chunk_v = 16
            elif chunk_h < 16000:
                chunk_v = 8
            elif chunk_h < 32000:
                chunk_v = 4
            else:
                chunk_v = 2

            row = 0

            # Rescale image intensity with respect to black_level and white_level.
            while row < d[0]:
                if row + chunk_v > d[0]:
                    # Final chunk may be smaller than the previous ones.
                    chunk_v = d[0] - row
                # Convert one chunk to float
                one_row = ar[row:row + chunk_v, ].astype(float)
                one_row = (one_row - offset1) * scale
                # Truncate underflow and overflow values.
                one_row[one_row < 0] = 0
                one_row[one_row > max_val] = max_val
                # Demote back to original data type and rewrite
                ar[row:row + chunk_v, ] = one_row.astype(pixel_type)
                row += chunk_v

            end = time.time()
            print(f'      Completed in {end - start} seconds.')

            if color == "Green":
                img_green = ar
            elif color == "Red":
                img_red = ar
            elif color == "Blue":
                img_blue = ar
            elif color == "Cyan":
                img_cyan = ar

        if img_red is None:
            img_red = np.zeros(d, dtype=pixel_type_string)
        if img_green is None:
            img_green = np.zeros(d, dtype=pixel_type_string)

        if img_cyan is not None:
            if img_blue is not None:
                # Have both blue and cyan channels. Merge cyan into main image, at reduced brightness
                if True:
                    # If we have both blue and cyan, then merge it into green and blue channels.
                    # Note: we have to temporarily promote datatype to 32-bit, or else numbers will overflow,
                    # and then demote back to original datatype.
                    img_cyan = img_cyan.astype(np.uint32) >> 1   # divide by two
                    img_green = img_green.astype(np.uint32) + img_cyan
                    img_blue = img_blue.astype(np.uint32) + img_cyan

                    img_green[img_green > max_val] = max_val
                    img_blue[img_blue > max_val] = max_val

                    # Have to "demote" type back down to original 8 or 16-bit.
                    img_green = img_green.astype(pixel_type)
                    img_blue = img_blue.astype(pixel_type)

        # Now merge channels into a single image, but first convert missing channels to zeros.
        if img_blue is None:
            # If there is no blue channel, then check whether we can substitute the cyan
            if img_cyan is not None:
                # Have cyan but not blue. Use cyan in place of blue.
                print('  No blue channel present, converting cyan channel to blue as replacement')
                img_blue = img_cyan
            else:
                # There is neither a blue nor cyan channel. Use zeros
                img_blue = np.zeros(d, dtype=pixel_type_string)

        # imwrite requires BGR order, backwards from usual RGB
        merged = np.dstack((img_blue, img_green, img_red))
        self.write_jpg(merged, img.name, "_RGB", bit_depth)

    def write_jpg(self, merged, img_name, suffix, source_bit_depth):

        # Split path into root and extension
        paths = os.path.splitext(self.file_path)
        new_path = paths[0] + "_" + img_name + suffix + ".jpg"
        print('  Writing RGB merged file: "' + os.path.basename(new_path) + '"')
        start = time.time()
        if source_bit_depth == 16:
            # JPG only supports 8-bit depth?
            merged = merged / 256
        cv2.imwrite(new_path, merged, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        end = time.time()
        print(f'    Completed in {end - start} seconds.')
