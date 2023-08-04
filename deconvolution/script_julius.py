#!‪C:\Internal\.envs\decon\Scripts\python.exe

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

os.system("cd C:/Internal/deconvolution")


from pathlib import Path
import cuda_decon


# Import
folder = r"D:\Users\winter\Desktop\Deconvolution"

files = Path(folder).rglob('*.ome.tif')

parameters = {
    'background': 'median'
    #'background' : 1.0
}
# background      0-3: otsu with this scaling factor
# background      > 3: fixed value
# background 'median': median of each z-stack as bg

for file in files:

    if not 'decon' in file.name:
        print(file.name)
        print(file.as_posix())
        cuda_decon.decon_ome_stack(file.as_posix(), params=parameters)
