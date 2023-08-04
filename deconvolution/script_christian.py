#!‪C:\Internal\.envs\decon_310\Scripts\python.exe

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "0"

os.system("C:/Internal/.envs/decon_310/Scripts/activate")
os.system("cd C:/Internal/deconvolution")


from pathlib import Path
from prepare import get_filter_zone_ver_stripes, prepare_one_slice
import cuda_decon

# Import
folder = r"Z:/_Lab members/Christian_Z/MMJ/20230301_MMJ_Experiment1"


files = Path(folder).rglob('*.ome.tif')

parameters = {
    'background': 'median',
}
# background      0-3: otsu with this scaling factor
# background      > 3: fixed value
# background 'median': median of each z-stack as bg


for file in files:
    if not 'decon' in file.name:
        print(file.name)
        print(file.as_posix())
        cuda_decon.decon_ome_stack(file.as_posix(), params=parameters)
