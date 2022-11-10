from LifClass import LifClass
import tkinter as tk
from tkinter import filedialog
import os

print('\nSelect what to analyze:')
print('1. All .LIF files in one folder')
print('2. Single .LIF file')
print('3. Single image within .LIF file')
answer = input('Make selection (default = 1): ')

if answer == '':
    answer = '1'

if answer == '1':
    root = tk.Tk()  # pointing root to Tk() to use it as Tk() in program.
    root.withdraw()  # Hides small tkinter window.
    root.attributes('-topmost', True)  # Opened windows will be active. above all windows despite of selection.
    folder_path = filedialog.askdirectory()

    files = os.scandir(folder_path)

    for f in files:
        if f.is_dir():
            continue

        path_ext = os.path.splitext(f)
        if path_ext[1] != '.lif':
            continue

        print(f'\nProcessing file {f.name}')
        l1 = LifClass(f.path)
        l1.convert()

elif answer == '2':

    l1 = LifClass()
    l1.convert()

elif answer == '3':

    l1 = LifClass()
    n = l1.prompt_select_image()
    l1.convert(n)

else:
    print('No valid option selected. Will not do anything')



