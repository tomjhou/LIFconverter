
1. CREATING EXE FILE FROM PYTHON:

Install auto-py-to-exe using the following:

pip install auto-py-to-exe

You then have to find the .exe file which will be in the Scripts folder of the python installation. For example, it might be in:

C:/Users/TomJhou/anaconda3/Scripts/auto-py-to-exe.exe

Add that folder to the Windows path if you want to run from command line. Or add a shortcut to taskbar and run from there.

Strangely, there is also an "autopytoexe.exe" file. It is the same size as auto-py-to-exe.exe, and seems to act the same.

When you run it, it will take a while and produce ~50 lines of messages. That is normal.

Don't try to resize the window to see more text. Strange things will happen to it.

Output will be sent to whatever folder you ran it from, in a subfolder called "output".


2. NOTES ON READLIF

readlif has been modified from original 0.6.5 version on pypi.org. Here are some changes:

1. No longer crashes when reading newer lif files where the end of the file is zero instead of having one final magic number
2. No longer crashes if number of offsets is less than number of detected images (usually indicates truncated or corrupted file)
3. Fixed bug where magic number value error would close file and cause the wrong kind of error to be reported (truncation)

The python lif viewer is based on this java version:
https://github.com/ome/bioformats/blob/master/components/formats-gpl/src/loci/formats/in/LIFReader.java