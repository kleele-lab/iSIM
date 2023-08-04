#!‪C:\Internal\.envs\decon_310\Scripts\python.exe

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

os.system("C:/Internal/.envs/decon_310/Scripts/activate")
os.system("cd C:/Internal/deconvolution")


from pathlib import Path
import cuda_decon

# Import
# folder = "Z:/iSIMstorage/Users/Willi/decon_test_Tatjana/"
# file = r"\\lebnas1\microsc125\iSIMstorage\Users\Willi\decon_test_Tatjana\Cell_1\original.tif"
# cuda_decon.decon_one_frame(file, {'background': 'median'})
folder = r"\\lebnas1\microsc125\iSIMstorage\Users\Juan_iSIM\232707_MEF_Opa1_last"

files = Path(folder).rglob('*0.ome.tif')

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