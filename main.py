from LifClass import LifClass
import tkinter as tk
from tkinter import filedialog
import os

print('\nSelect what to convert:')
print('1. All .LIF files in one folder')
print('2. Single .LIF file')
print('3. Single image within single .LIF file')
answer_source = input('Make selection (default = 1): ')
if answer_source == '':
    answer_source = '1'

print('\nSelect format to conver to:')
print('1. JPG (90% quality, much smaller files, highly recommended)')
print('2. TIFF (larger files, but compression is lossless. Only use if higher quality is absolutely necessary. Not tested for files >4GB')
answer_format = input('Make selection (default = 1): ')
if answer_format == '':
    answer_format = '1'

if answer_format == '1':
    convert_format = LifClass.Format.jpg
elif answer_format == '2':
    convert_format = LifClass.Format.tiff
else:
    convert_format = LifClass.Format.jpg

answer_metadata = input('\nWrite each LIF file\'s metadata to XML file? (y/n, default = n):')
if answer_metadata == '':
    answer_metadata = 'n'

WriteMetadata = (answer_metadata == 'y')

if answer_source == '1':
    root = tk.Tk()  # pointing root to Tk() to use it as Tk() in program.
    root.withdraw()  # Hides small tkinter window.
    root.attributes('-topmost', True)  # Opened windows will be active. above all windows despite of selection.
    folder_path = filedialog.askdirectory()

    if folder_path != '':
        files = os.scandir(folder_path)

        for f in files:
            if f.is_dir():
                continue

            path_ext = os.path.splitext(f)
            if path_ext[1] != '.lif':
                continue

            print(f'\nProcessing file {f.name}')
            l1 = LifClass(f.path)
            r = l1.convert(write_xml_metadata=WriteMetadata, convert_format=convert_format)

        print(f'\nCompleted conversion of {r[0]} images in {r[1]} LIF files in folder\n')
    else:
        print('\nNo folder chosen.\n')

elif answer_source == '2':

    l1 = LifClass()
    l1.convert(write_xml_metadata=WriteMetadata, convert_format=convert_format)

elif answer_source == '3':

    l1 = LifClass()
    n = l1.prompt_select_image()
    l1.convert(n, write_xml_metadata=WriteMetadata, convert_format=convert_format)

else:
    print('No valid option selected. Will not do anything')



