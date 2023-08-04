#!‪C:\Internal\.envs\decon_310\Scripts\python.exe

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

os.system("cd C:/Internal/deconvolution")


from pathlib import Path
import cuda_decon

# Import
folder = r"Z:\iSIMstorage\Users\Berna\230131\PB-arc\FOV5\Alltiff"

files = Path(folder).rglob('*.tif*')

parameters = {
    'background': 3
}
# background      0-3: otsu with this scaling factor
# background      > 3: fixed value
# background 'median': median of each z-stack as bg


for file in files:
    print(file.name)
    if not 'decon' in file.name:
        print(file.as_posix())
        cuda_decon.decon_ome_stack(file.as_posix(), params=parameters)
