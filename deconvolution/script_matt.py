#!‪C:\Internal\.envs\decon_310\Scripts\python.exe

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

os.system("C:/Internal/.envs/decon_310/Scripts/activate")
os.system("cd C:/Internal/deconvolution")


from pathlib import Path
from prepare import get_filter_zone_ver_stripes, prepare_one_slice
import cuda_decon

# Import
# folder = "Z:/iSIMstorage/Users/Willi/decon_test_Tatjana/"
# file = r"\\lebnas1\microsc125\iSIMstorage\Users\Willi\decon_test_Tatjana\Cell_1\original.tif"
# cuda_decon.decon_one_frame(file, {'background': 'median'})
# folder = r"\\lebnas1.epfl.ch\microsc125\iSIMstorage\Users\Tatjana\2022\220302_MEFwt_MitotrG_S5"
# folder = r"Z:\iSIMstorage\Users\Tatjana\2022\2207\220713"
folder = r"Z:\\"

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
