from LifClass import LifClass
import tkinter as tk
from tkinter import filedialog
import os

print('\nSelect what to convert:')
print('1. All .LIF files in one folder')
print('2. Single .LIF file')
print('3. Single image within single .LIF file')
answer = input('Make selection (default = 1): ')
if answer == '':
    answer = '1'

answer2 = input('\nWrite each LIF file\'s metadata to XML file? (y/n, default = n):')
if answer2 == '':
    answer2 = 'n'

WriteMetadata = (answer2 == 'y')

if answer == '1':
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
            r = l1.convert(write_xml_metadata=WriteMetadata)

        print(f'\nCompleted conversion of {r[0]} images in {r[1]} LIF files in folder\n')
    else:
        print('\nNo folder chosen.\n')

elif answer == '2':

    l1 = LifClass()
    l1.convert(write_xml_metadata=WriteMetadata)

elif answer == '3':

    l1 = LifClass()
    n = l1.prompt_select_image()
    l1.convert(n, write_xml_metadata=WriteMetadata)

else:
    print('No valid option selected. Will not do anything')



