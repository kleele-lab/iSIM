#!‪C:\Internal\.envs\decon\Scripts\python.exe

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

os.system("cd C:/Internal/deconvolution")


from pathlib import Path
import cuda_decon


# Import
#folder = "Z:/iSIMstorage/Users/Willi/decon_test_Tatjana/"
# file = r"\\lebnas1\microsc125\iSIMstorage\Users\Willi\decon_test_Tatjana\Cell_1\original.tif"
# cuda_decon.decon_one_frame(file, {'background': 'median'})
# folder = r"\\lebnas1.epfl.ch\microsc125\iSIMstorage\Users\Tatjana\2022\220302_MEFwt_MitotrG_S5"
#folder = r"\\lebnas1\microsc125\iSIMstorage\Users\Willi\decon_test_Sheda\test"
#folder = r"D:/Users/cbennejm/Desktop/My_iSIM_deconv/FOV16_2"
#folder = "D:/Users/cbennejm/Desktop/FOV16"
#folder = "D:/Users/cbennejm/Desktop/Poster_images/FOV5_crop2/frames"
folder = "D:/Users/cbennejm/Desktop/My_iSIM_deconv/221019_YAB201_SCD/FOV7_2"


files = Path(folder).rglob('*.ome.tif')

parameters = {
    #'background': 'median'
    'background' : 0.9
}
# background      0-3: otsu with this scaling factor
# background      > 3: fixed value
# background 'median': median of each z-stack as bg

for file in files:

    if not 'decon' in file.name:
        print(file.name)
        print(file.as_posix())
        cuda_decon.decon_ome_stack(file.as_posix(), params=parameters)
