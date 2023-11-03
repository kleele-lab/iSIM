import os
os.environ['TF_GPU_ALLOCATOR'] = 'cuda_malloc_async'

import tensorflow

gpus = tensorflow.config.list_physical_devices('GPU')
for gpu in gpus:
    tensorflow.config.experimental.set_memory_growth(gpu, True)


from pathlib import Path
from prepare import get_filter_zone_ver_stripes, prepare_one_slice
import cuda_decon

# Import
# folder = r"/nfs/nas22/fs2202/biol_bc_kleele_2/Joshua/iSIM/231010_RPE1_cycling_1"
folder = r"/nfs/nas22/fs2202/biol_bc_kleele_2/Joshua/20231012_coculture48h/20231012_coculture08_2hybrids"

files = Path(folder).rglob('*.ome.tif')


parameters = {
    'background': "median",
}
# background      0-3: otsu with this scaling factor
# background      > 3: fixed value
# background 'median': median of each z-stack as bg

for file in files:

    if not 'decon' in file.name:

        print(file.name)
        print(file.as_posix())
        cuda_decon.decon_ome_stack(file.as_posix(), params=parameters)
