import tkinter as tk
from tkinter import filedialog
import struct  # Because image descriptor is a struct
import re  # for handling regular expressions
from dataclasses import dataclass, field


@dataclass
class Descriptor:
    name: str = ""
    channels: list = field(default_factory=list)
    dimensions: int = 0
    memory_size: int = 0
    memory_start_position: int = 0
    memory_block_id: int = 0
    black_level: float = 0.0
    white_level: float = 0.0


@dataclass
class DescriptorArray:
    image_info_list: list

    def __getitem__(self, key) -> Descriptor:
        return self.image_info_list[key]


class LifClass:

    def __init__(self, file_path=""):

        if file_path == "":

            root = tk.Tk()
            root.withdraw()

            file_path = filedialog.askopenfilename(filetypes=[("LIF files", "*.lif")])

            #            [filename, pathname] = uigetfile({'*.lif', 'Leica Image Format (*.lif)'})
            if file_path == "":
                print('No file selected, will quit\n')
                return

        self.file_path = file_path
        self.image_info_list = self.load_info()

    def load_image_interactive(self, n=-1):

        if len(self.image_info_list) == 1:
            # If only one image is present, then read that one.
            n = 0
        else:
            # If multiple images, then prompt user to choose
            print('\nAvailable images in this file:\n')
            for x in range(len(self.image_info_list)):
                print('{x}. {self.imageList(x).Name}')
            n = input('Choose image: ')

        if n < 0:
            print('Image %d is too low. Will read image 1.\n', n)
            n = 0
        elif n >= len(self.image_info_list):
            print('Image %d is too high. Will read image %d.\n', n, len(self.image_info_list))
            n = len(self.image_info_list) - 1

        print(f'  Reading image {n}: "{self.image_info_list[n].name}"')
        return self.load_image(n)

    # Read image info only
    def load_info(self):

        # Need to specify UTF-8 encoding or fread will be slow
        w = open(self.file_path, 'rb')  # , 'n', 'UTF-8') # n = native byte ordering. Windows is "little-endian".

        # Reading XML
        self.xmlHdrStr = self.ReadXMLPart(w)

        # Convert header to xmlList cell array
        self.xmlList = self.XMLtxt2cell(self.xmlHdrStr)

        n = self.GetNumImages()

        lif_version = self.GetLifVersion()  # lifVersion is double scalar

        img_list = self.GetImageDescriptionList()

        img_list = self.ReadObjectMemoryBlocks(w, lif_version, img_list)
        w.close()

        return img_list

    def load_image(self, n):

        img_raw_data = self.ReadAnImageData(n, self.file_path)
        img_struct = self.ReconstructImage(n, img_raw_data)

        #        dims = self.GetDimensionInfo(self.image_info_list[n].Dimensions)

        #        imgStruct.Type = dims[0]
        #        imgStruct.Size = dims[1]

        return img_struct

    def ReadXMLPart(self, w):

        x = struct.unpack('i', w.read(4))  # , '*uint32'), 'Invalid test value at Part: XML.')
        # x will be a tuple, so need to get 0th element
        if x[0] != 112:
            raise 'Error, first bytes not 112\n'

        xml_chunk_size = struct.unpack('i', w.read(4))
        xml_chunk_size = xml_chunk_size[0]
        x2 = w.read(1)
        if x2[0] != 42:
            print('Error, byte should be 42\n')
            return

        nc = struct.unpack('i', w.read(4))[0]
        if (nc * 2 + 1 + 4) != xml_chunk_size:
            print('Chunk size mismatch at Part: XML.')
            return

        xml_bytes = w.read(nc * 2)
        xml_byte_array = bytearray(nc)

        for x3 in range(nc):
            # Convert 16-bit to 8-bit
            xml_byte_array[x3] = xml_bytes[x3 * 2]

        xml_str = xml_byte_array.decode()

        self.ketPos = xml_str.find('>')

        return xml_str

    def XMLtxt2cell(self, c) -> list:

        r0 = r"""<(?:"[^"]*"|'[^']*'|[^'>])*>"""
        r1 = re.compile(r0)
        tags = r1.findall(c)
        n_tags = len(tags)
        tag_list = arr = [[None for i in range(5)] for j in range(n_tags)]  # cell(n_tags, 5)
        tag_rank = 0
        tag_count = 0
        for n in range(n_tags):
            current_tag = tags[n][1: -1]
            if current_tag[0] == '/':
                tag_rank = tag_rank - 1
                continue
            tag_rank = tag_rank + 1
            t = self.ParseTagString(current_tag)
            tag_list[tag_count][0] = tag_rank
            tag_list[tag_count][1] = t[0]
            tag_list[tag_count][2] = t[1]
            if tag_rank != 1:
                if tag_rank != tag_list[tag_count - 1][0]:
                    tag_rank_list = [x[0] for x in tag_list]
                    parent = LifClass.list_rev_index(tag_rank_list, tag_rank - 1)
                    tag_list[tag_count][3] = parent
                else:
                    tag_list[tag_count][3] = tag_list[tag_count - 1][3]

            else:
                # Top level tags have no parent
                tag_list[tag_count][3] = -1

            if current_tag[-1] == '/':
                tag_rank = tag_rank - 1

            tag_count = tag_count + 1

        tag_list = tag_list[0:tag_count]
        parent_list = [x[3] for x in tag_list]
        for n in range(tag_count):
            tag_list[n][4] = LifClass.list_find_all_index(parent_list, n)

        return tag_list

    def GetNumImages(self):
        img_index = self.SearchTag('ImageDescription')
        num_imgs = len(img_index)
        return num_imgs

    def GetLifVersion(self):
        index = self.SearchTag('LMSDataContainerHeader')
        value = self.GetAttributeVal(index, 'Version')
        lif_version = float(value[0])
        return lif_version

    def GetImageDescriptionList(self):

        #  For the image data type the description of the memory layout is defined
        #  in the image description XML node (<ImageDescription>).

        # <ImageDescription>
        img_index = self.SearchTag('ImageDescription')
        num_images = len(img_index)

        # <Memory Size="21495808" MemoryBlockID="MemBlock_233"/>
        mem_index = self.SearchTag('Memory')

        # <ChannelScalingInfo WhiteValue="" BlackValue="">
        scaling_index = self.SearchTag('ChannelScalingInfo')

        mem_sizes = [float(x) for x in self.GetAttributeVal(mem_index, 'Size')]
        mem_index = [x for i, x in enumerate(mem_index) if mem_sizes[i] > 0]
        mem_sizes = [x for i, x in enumerate(mem_sizes) if mem_sizes[i] > 0]
        if num_images != len(mem_index):
            raise 'Number of ImageDescription and Memory did not match.'

        # Matching ImageDescription with Memory
        img_parent_elm_index = [0] * num_images
        for n in range(num_images):
            img_parent_elm_index[n] = self.SearchTagParent(img_index[n], 'Element')

        mem_parent_elm_index = [0] * num_images
        for n in range(num_images):
            mem_parent_elm_index[n] = self.SearchTagParent(mem_index[n], 'Element')

        # There is one ViewerScaling entry for each channel. There can be multiple
        # channels per image.
        num_scales = len(scaling_index)
        scaling_parent_elm_index = [0] * num_scales
        for n in range(num_scales):
            scaling_parent_elm_index[n] = self.SearchTagParent(scaling_index[n], 'Element')

        # [img_parent_elm_index, sortIndex] = sort(img_parent_elm_index); img_index=img_index(sortIndex);
        # [mem_parent_elm_index, sortIndex] = sort(mem_parent_elm_index); mem_index=mem_index(sortIndex);mem_sizes=mem_sizes(sortIndex);
        if not (img_parent_elm_index == mem_parent_elm_index):
            raise 'Mismatch between ImageDescriptions and Memories in XML header of LIF file'

        descriptors = [Descriptor() for n in range(num_images)]

        descriptors[num_images - 1].memory_start_position = []
        total_channels = 0
        for n in range(num_images):
            descriptors[n].name = self.GetAttributeVal(img_parent_elm_index[n], 'Name')
            img_struct = self.MakeImageStruct(img_index[n])
            descriptors[n].channels = img_struct[0]
            descriptors[n].dimensions = img_struct[1]
            total_channels = total_channels + len(descriptors[n].channels)
            descriptors[n].memory_size = mem_sizes[n]
            descriptors[n].memory_block_id = self.GetAttributeVal(mem_index[n], 'MemoryBlockID')

        # Extract viewer scaling values
        for n in range(num_images):

            nchans = len(descriptors[n].channels)

            # Create empty arrays to contain black and white levels.
            # Initialize to 0 and 1
            descriptors[n].black_level = [0] * nchans
            descriptors[n].white_level = [1] * nchans

            start_search = img_parent_elm_index[n]
            if n < num_images - 1:
                end_search = img_parent_elm_index[n + 1]
            else:
                end_search = len(self.xmlList)

            scales = [x for x in scaling_index if (x > start_search) & (x < end_search)]

            if len(scales) > nchans:
                scales = scales[-nchans:-1]

            # Now find real values
            for ch in range(nchans):
                v = self.GetAttributeVal(scales[ch], "BlackValue")
                descriptors[n].black_level[ch] = float(v[0])
                v = self.GetAttributeVal(scales[ch], "WhiteValue")
                descriptors[n].white_level[ch] = float(v[0])

        return descriptors

    def ReadObjectMemoryBlocks(self, w, lif_version, img_lists):

        # get end of file and return current point
        cofp = w.tell()
        w.seek(0, 2)  # 2 is eof
        eofp = w.tell()
        w.seek(cofp, 0)  # 0 is beginning of file

        n_img_lists = len(img_lists)
        memory_list = self.make_2d_list(n_img_lists, 4)
        # ID(string), startPoint(uint64), size_of_memory, Index(double)
        for n in range(n_img_lists):
            memory_list[n][1] = img_lists[n].memory_block_id

        # read object memory blocks
        while w.tell() < eofp:

            x = struct.unpack('i', w.read(4))  # , '*uint32'), 'Invalid test value at Part: XML.')
            # x will be a tuple, so need to get 0th element
            if x[0] != 112:
                raise 'Error, first bytes not 112\n'

            mem_chunk_size = struct.unpack('i', w.read(4))
            mem_chunk_size = mem_chunk_size[0]
            x2 = w.read(1)[0]
            if x2 != 42:
                raise 'Error, byte should be 42\n'

            if lif_version == 1:  # Size of Memory (version dependent)
                size_of_memory = struct.unpack('I', w.read(4))[0]  # uint32
            elif lif_version == 2:
                size_of_memory = struct.unpack('Q', w.read(8))[0]  # uint64
            else:
                raise 'Unsupported LIF version. Update this program'

            x3 = w.read(1)[0]
            if x3 != 42:
                raise 'Error, byte should be 42\n'

            nc = struct.unpack('i', w.read(4))  # Number of MemoryID string
            nc = nc[0]

            xml_bytes = w.read(nc * 2)
            xml_byte_array = bytearray(nc)

            for x4 in range(nc):
                # Convert 16-bit to 8-bit
                xml_byte_array[x4] = xml_bytes[x4 * 2]

            if size_of_memory > 0:
                for n in range(n_img_lists):
                    if memory_list[n][1][0] == xml_byte_array.decode():  # % NEED CONSIDERATION !!!!!!
                        if img_lists[n].memory_size != size_of_memory:
                            raise 'Memory Size Mismatch.'
                        img_lists[n].memory_start_position = w.tell()
                        w.seek(size_of_memory, 1)  # ,'cof')
                        break

        return img_lists

    def ReadAnImageData(self, n, file_path):

        w = open(self.file_path, 'rb')  # , 'n', 'UTF-8') # n = native byte ordering. Windows is "little-endian".

        w.seek(self.image_info_list[n].memory_start_position,
               0)  # 0 is beginning of file, 1 is current file position, 2 is end of file
        img_raw_data = w.read(int(self.image_info_list[n].memory_size))  # , '*uint8');
        w.close()
        return img_raw_data

    def ReconstructImage(self, n, img_raw_data):
        # ===================================================================
        # imgInfo description
        # ===================================================================
        # <ChannelDescription>
        # DataType   [0, 1]               [Integer, Float]
        # ChannelTag [0, 1, 2, 3]         [GrayValue, Red, Green, Blue]
        # Resolution [Unsigned integer]   Bits per pixel if DataType is Float value can be 32 or 64 (float or double)
        # NameOfMeasuredQuantity [String] Name
        # Min        [Double] Physical Value of the lowest gray value (0). If DataType is Float the Minimal possible value (or 0).
        # Max        [Double] Physical Value of the highest gray value (e.g. 255) If DataType is Float the Maximal possible value (or 0).
        # Unit       [String] Physical Unit
        # LUTName    [String] Name of the Look Up Table (Gray value to RGB value)
        # IsLUTInverted [0, 1] Normal LUT Inverted Order
        # BytesInc   [Unsigned long (64 Bit)] Distance from the first channel in Bytes
        # BitInc     [Unsigned Integer]       Bit Distance for some RGB Formats (not used in LAS AF 1..0 ? 1.7)
        # <DimensionDescription>
        # DimID   [0, 1, 2, 3, 4, 5, 6, 7, 8] [Not valid, X, Y, Z, T, Lambda, Rotation, XT Slices, T Slices]
        # NumberOfElements [Unsigned Integer] Number of elements in this dimension
        # Origin           [Unsigned integer] Physical position of the first element (Left pixel side)
        # Length   [String] Physical Length from the first left pixel side to the last left pixel side (Not the right. A Pixel has no width!)
        # Unit     [String] Physical Unit
        # BytesInc [Unsigned long (64 Bit)] Distance from one Element to the next in this dimension
        # BitInc   [Unsigned Integer] Bit Distance for some RGB Formats (not used, i.e.: = 0 in LAS AF 1..0 ? 1.7)
        # ===================================================================
        # imgList info
        # ===================================================================
        # img

        # Get Dimension info
        dimension = [1] * 9
        image_info = self.image_info_list[n]
        for m in range(len(image_info.dimensions)):
            dimension[int(self.ListGetAttributes(image_info.dimensions[m], 'DimID', get_first_only=True)) - 1]\
                = int(self.ListGetAttributes(image_info.dimensions[m], 'NumberOfElements', get_first_only=True))

        # Separate to each channel image
        n_ch = len(image_info.channels)

        image_data = [None] * n_ch
        if n_ch > 1:
            b1 = self.ListGetAttributes(image_info.channels[1], 'BytesInc')
            b2 = self.ListGetAttributes(image_info.channels[0], 'BytesInc')
            tmp = int(b1[0]) - int(b2[0])
            img_raw_data = reshape(img_raw_data, tmp, [])
            for m in range(n_ch):
                tmp = img_raw_data[:, m:n_ch:end]
                image_data[m] = reshape(typecast(tmp[:], type(image_info.Channels[m])), dimension)
        else:
            image_data[1] = reshape(typecast(img_raw_data, type(image_info.Channels)), dimension)

        return image_data, image_info

    def GetAttributeVal(self, index, attribute_name):
        if type(index) == list:
            num_elt = len(index)
        else:
            index = [index]   # Make a list with one value
            num_elt = 1

        value = []
        for n in range(num_elt):
            current_cell = self.xmlList[index[n]][2]
            value = value + self.ListGetAttributes(current_cell, attribute_name)

        return value

    @staticmethod
    def ListGetAttributes(lst, attribute_name, get_first_only=False):
        v = []
        for m in range(len(lst)):
            if lst[m][0] == attribute_name:
                if get_first_only:
                    return lst[m][1]
                v.append(lst[m][1])

        if get_first_only:
            raise f'Attribute {attribute_name} not found'
        return v

    def SearchTag(self, tag_name):

        list_len = len(self.xmlList)
        index = []
        for n in range(list_len):
            if self.xmlList[n][1] == tag_name:
                index.append(n)

        return index

    # Searches parent tree of item # index, having name tagName
    def SearchTagParent(self, index, tag_name):

        pindex = self.xmlList[index][3]

        while pindex != 0:
            if self.xmlList[pindex][1] == tag_name:
                return pindex
            else:
                pindex = self.xmlList[pindex][3]

        raise 'Cannot Find the Parent Tag ' + tag_name

    def MakeImageStruct(self, iid):
        # ChannelDescription   DataType="0" ChannelTag="0" Resolution="8"
        #                      NameOfMeasuredQuantity="" Min="0.000000e+000" Max="2.550000e+002"
        #                      Unit="" LUTName="Red" IsLUTInverted="0" BytesInc="0"
        #                      BitInc="0"
        # DimensionDescription DimID="1" NumberOfElements="512" Origin="4.336809e-020"
        #                      Length="4.558820e-004" Unit="m" BitInc="0"
        #                      BytesInc="1"
        # Memory ?@?@?@?@?@?@?@  Size="21495808" MemoryBlockID="MemBlock_233"
        iid_children = self.xmlList[iid][4]
        for n in range(len(iid_children)):
            if self.xmlList[iid_children[n]][1] == 'Channels':
                id = self.xmlList[iid_children[n]][4]
                p = [self.xmlList[x][2] for x in id]
                nid = len(id)
                p1 = p
            elif self.xmlList[iid_children[n]][1] == 'Dimensions':
                id = self.xmlList[iid_children[n]][4]
                p = [self.xmlList[x][2] for x in id]
                p2 = p
            else:
                raise 'Undefined Tag'

        return p1, p2

    @staticmethod
    def make_2d_list(rows, cols):
        return [[None for i in range(cols)] for j in range(rows)]

    @staticmethod
    def list_rev_index(li, x):
        n = len(li)
        for i in range(n):
            if li[n - i - 1] == x:
                return n - i - 1
        return -1

    @staticmethod
    def list_find_all_index(li, x):
        n = len(li)
        l = []
        for i in range(n):
            if li[i] == x:
                l.append(i)
        return l

    @staticmethod
    def ParseTagString(tag):

        r1 = re.compile(r'^\w+')
        na = r1.search(tag)  # , '^\w+', 'match', 'split')
        name = na[0]
        r2 = re.compile(r'\w+=".*?"')
        attributes_cell = r2.findall(tag)  # , '\w+=".*?"', 'match')
        if len(attributes_cell) == 0:
            attributes = None
        else:
            n_attributes = len(attributes_cell)
            attributes = [[None for i in range(2)] for j in range(n_attributes)]  # cell(n_attributes, 2)
            for n in range(n_attributes):
                curr_attrib = attributes_cell[n]
                quote_position = LifClass.list_find_all_index(curr_attrib, '"')
                attributes[n][0] = curr_attrib[0:quote_position[0] - 1]
                if quote_position[1] - quote_position[0] == 1:
                    attributes[n][1] = ''
                else:
                    attributes[n][1] = curr_attrib[quote_position[0] + 1:quote_position[1]]

        return name, attributes
