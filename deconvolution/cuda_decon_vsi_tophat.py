# deconvolution of .vsi file with top hat filter

from typing import Tuple, Callable
from flowdec import data as fd_data
from flowdec import restoration as fd_restoration
from skimage import io, morphology
from scipy import ndimage
import numpy as np
import matplotlib.pyplot as plt
from prepare import prepare_decon, get_filter_zone
from dataclasses import dataclass
# import tensorflow_probability as tfp
import tensorflow as tf
import h5py as h
import javabridge as jb
import bioformats as bf 

import tifffile
import xmltodict
from dicttoxml import dicttoxml
from tqdm import tqdm
from typing import Union
import json
from PIL import Image

import uuid
import time  
import os  
import pdb


os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
# os.environ["XLA_PYTHON_CLIENT_ALLOCATOR"] = 'platform'

SIZE_LIMIT = 100_000_000
OVERLAP = 6

def main():
    from Analysis.tools import get_files
    folder = '/nfs/nas22/fs2202/biol_bc_kleele_2/Joshua/240119_RPE1_Torin_Mdivi_MFI8_iSIM/18h'
    files, _ = get_files(folder)

    algo = fd_restoration.RichardsonLucyDeconvolver(2).initialize()
    kernel = make_kernel(io.imread(files['network'][0]), sigma=3.9/2.355)
    for struct_file in files['network']:
        struct_img = io.imread(struct_file)
        _, axs = plt.subplots(1, 2)
        # axs[0].imshow(struct_img)
        t0 = time.perf_counter()
        struct_img = prepare_decon(struct_img)
        img = richardson_lucy(struct_img, algo=algo, kernel=kernel).astype(np.uint16)
        print(time.perf_counter()-t0)
        axs[0].imshow(struct_img.astype(np.uint16))
        axs[1].imshow(img)
        # plt.show()

# added: function to apply top hat filter 

def top_hat(x,sigma):
    max = x.max()
    min = x.min()
    footprint = morphology.disk(sigma)
    res = morphology.white_tophat(x, footprint)
    res = (res - res.min()) / (res.max() - res.min()) # between [0,1]
    return np.array((res * (max - min) + min))


# added: import of vsi formats

def import_vsi(image_path):
    jb.start_vm(class_path=bf.JARS)

    # path = path to .vsi image file
    img = []
    # get metadata
    metadata = xmltodict.parse(bf.get_omexml_metadata(image_path))

    # extract Z and T, X and Y
    Z = int(metadata['OME']['Image'][0]['Pixels']['@SizeZ'])
    T = int(metadata['OME']['Image'][0]['Pixels']['@SizeT'])
    X = int(metadata['OME']['Image'][0]['Pixels']['@SizeX'])
    Y = int(metadata['OME']['Image'][0]['Pixels']['@SizeY'])
    C = int(metadata['OME']['Image'][0]['Pixels']['@SizeC'])
    #z_step = float(metadata['OME']['Image']["Pixels"]['@PhysicalSizeZ'])

    # loop over z and t
    for t in range(T):
        for z in range(Z):
            # rescale = False otherwise it will scale from 0-1 
            # apply top-hat here. with sigma = 20
            load_img = bf.load_image(image_path,z=z,t=t, rescale=False)
            # apply top hat over each color: set sigma to 
            img_processed = []
            for channel in range(0,C):
                img_processed.append(top_hat(load_img[:,:,channel],sigma=20))

            img.append(img_processed)
    
    # make numpy array and move channels axis --> shape = TZCYX 

    return np.array(img), (T,Z,C,Y,X), metadata

@dataclass
class CudaParams():
    """ Class for storing CUDA parameters to be passed to the flowdec function"""

    shape: Tuple[int] = (100, 100)
    ndim: int = 2
    sigma: float = 3.9/2.335
    z_step: float = 0.2
    prepared: bool = False
    background: Union[int, str] = 'median'
    after_gaussian: float = 2
    destripe: Callable = get_filter_zone

    def __post_init__(self):
        self.kernel = make_kernel(np.zeros(self.shape), sigma=self.sigma)
        self.algo = fd_restoration.RichardsonLucyDeconvolver(self.ndim, start_mode="INPUT").initialize()

    def to_dict(self):
        class_dict = {'sigma': self.sigma,
                      'z_step': self.z_step,
                      'background': self.background,
                      'after_gaussian': self.after_gaussian}
        return class_dict


def richardson_lucy(image, params=None, algo=None, kernel=None, prepared=True, background=None):
    original_data_type = image.dtype
    if params is not None:
        algo, kernel, prepared = params.algo, params.kernel, params.prepared
        background = params.background
        try:
            destripe_zones = params.destripe
        except (KeyError, AttributeError) as e:
            print("No function for destriping, will use default")
        # print(params)
    else:
        if algo is None:
            algo = fd_restoration.RichardsonLucyDeconvolver().initialize()
        if kernel is None:
            kernel = make_kernel(image, sigma=3.9/2.355)
        if background is None:
            print('no background specified, using 0.85')
            background = 0.85
        destripe_zones = get_filter_zone
    if not prepared:
        image = prepare_decon(image, background, destripe_zones)
    res = algo.run(fd_data.Acquisition(data=image, kernel=kernel['kernel']), niter=10).data
    return res.astype(original_data_type)


def make_kernel(image: np.ndarray, sigma=1.67, z_step=0.2):
    """Make a gaussian kernel that fits the psf of the microscope"""
    if image.ndim == 3:
        z_sigma = 0.48/z_step
        sigma = [z_sigma, sigma, sigma]
        print("3D images, sigma: ", sigma)

    size = image.shape
    size = [min([17, x]) for x in size]

    # If even size dimensions crop to have a center pixel
    kernel = {'kernel': np.zeros(size, dtype=float),
              'sigma': sigma}
    kernel['kernel'][tuple(np.array(kernel['kernel'].shape)//2)] = 1
    kernel['kernel'] = ndimage.gaussian_filter(kernel['kernel'], sigma=sigma)


    kernel['kernel'][kernel['kernel']<1e-6*np.max(kernel['kernel'])] = 0
    kernel['kernel'] = np.divide(kernel['kernel'], np.sum(kernel['kernel'])).astype(np.float32)
    return kernel


def init_algo(image):
    return fd_restoration.RichardsonLucyDeconvolver(image.ndim).initialize()


def decon_ome_stack(file_dir, save_dir, params=None):
    data = None

    data, meta, image_metadata = import_vsi(file_dir) 
    size_c = meta[2]
    size_t = meta[0]
    size_z = meta[1]

    # dont get why there is no z-step in the metadata
    z_step = 0.2

    dim_order = 'TZCYX'
    
    print(data.shape)
    print('size T', size_t)
    print('size Z', size_z)
    print('size C', size_c)
    print(dim_order)

    ndim = 2 if size_z == 1 else 3
    # Make standardized array with all dimensions
    # time [0], z[1], c[2] if not there, just missing depending on order
    # If it was recorded differently, swap dimensions

    if size_t == 1:
        data = np.expand_dims(data, 0)

    if size_z > 1 and size_c > 1 and dim_order == 'XYZCT':
        data = np.moveaxis(data, 1, 2)

    if size_z == 1:
        data = np.expand_dims(data, 1)
    if size_c == 1:
        data = np.expand_dims(data, 2)

    if size_t != data.shape[0]:
        size_t = data.shape[0]

    print("SHAPE", data.shape)

    # Make data odd shaped
    original_size_data = data.shape
    pad = tuple(np.zeros((5,2), int))
    crop = tuple(np.zeros((5,2), int))
    if data.shape[1]%2 == 0:
        pad_here = tuple(np.zeros((5,2), int))
        pad_here[1][1] = 1
        data = np.pad(data, pad)
    for dim in [3, 4]:
        if data.shape[dim]%2 == 0:
            pad[dim][1] = 1
            crop[dim][1] = data.shape[dim] - 1
        else:
            crop[dim][1] = data.shape[dim]
    data = data[:, :, :, :crop[3][1], :crop[4][1]]

    # Check if data might be too big for GPU and slice - removed this. 
    my_slices = None
    #if ndim == 3:
    #    n_pixels = np.prod(data[0, : ,0, :, :].shape)
    #    
    #    print(n_pixels)
    #    if n_pixels > SIZE_LIMIT:
    #        n_stacks = np.ceil(n_pixels/SIZE_LIMIT)
    #        print("n_stacks ", n_stacks)
    #        n_slices = round(size_z/n_stacks)
    #        n_slices = n_slices - 1 if n_slices%2 == 0 else n_slices
    #        print("n_slices ", n_slices)
    #        print("z ", size_z)
    #        my_slices = get_overlapping_slices(size_z, n_slices, OVERLAP)
    #        print(my_slices)

    kernel_shape = data.shape[-2:] if ndim==2 else [np.min([17, size_z]), *data.shape[-2:]]
    # Decon
    if params is None:
        background = 100
    else:
        background = params['background']
        try:
            destripe_zones = params['destripe_zones']
        except (AttributeError, KeyError) as e:
            print("No destripe specified.")
            destripe_zones = get_filter_zone
     
    params = CudaParams(background=background, shape=kernel_shape, ndim=ndim, z_step=z_step, destripe=destripe_zones)

    decon = np.empty_like(data)
    for timepoint in tqdm(range(size_t)):
        data_t = data[timepoint, :, :, :, :]
        for channel in range(size_c):
            data_c = data_t[:, channel, :, :]
            if size_z == 1:
                data_c = data_c[0, :, :]
            if my_slices is None:
                if ndim == 3:
                    padding = (data_c.shape[0] - params.kernel['kernel'].shape[0])//2
                    params.kernel['kernel'] = np.pad(params.kernel['kernel'],((padding, padding),(0,0),(0,0)))
                decon[timepoint, :, channel, :, :] = richardson_lucy(data_c, params=params)
            else:
                old_kernel_shape = params.kernel['kernel'].shape
                kernel_shape = None
                for idx, slices in enumerate(tqdm(my_slices)):
                    data_here = data_c[slices[0]:slices[1], :, :]
                    kernel_shape = [slices[1] - slices[0], *data_here.shape[-2:]]
                    if idx == 0:
                        # print("0 to ", slices[1]-OVERLAP//2)
                        decon[timepoint, 0:slices[1]-OVERLAP//2, channel, :, :] = richardson_lucy(data_here, params=params)[0:slices[1]-OVERLAP//2, :, :]
                    elif slices[1] == size_z:
                        # print(slices[0]+OVERLAP//2, " to ", size_z)
                        if params.kernel['kernel'].shape[0] != kernel_shape[0]:
                            padding = (params.kernel['kernel'].shape[0] - kernel_shape[0] + 1)//2
                            if padding > 0:
                                params.kernel['kernel'] = params.kernel['kernel'][padding+1:-padding]
                            print(params.kernel['kernel'].shape[0], " and ", kernel_shape[0])
                            print(padding)
                        # params = CudaParams(background=background, shape=kernel_shape, ndim=ndim, z_step=z_step)
                        decon[timepoint, slices[0]+OVERLAP//2:slices[1], channel, :, :] = richardson_lucy(data_here, params=params)[OVERLAP//2:, :, :]
                    else:
                        # print(slices[0]+OVERLAP//2, " to ", slices[1]-OVERLAP//2)
                        decon[timepoint, slices[0]+OVERLAP//2:slices[1]-OVERLAP//2, channel, :, :] = richardson_lucy(data_here, params=params)[OVERLAP//2:-OVERLAP//2, :, :]
                    old_kernel_shape = kernel_shape

    #Crop the data back if we padded it
    if original_size_data != decon.shape:
        decon = decon[:, :original_size_data[1], :, :, :]
    if original_size_data != decon.shape:
        decon = np.pad(decon, pad)
    
    print("DECON SHAPE ", decon.shape)

    out_file = os.path.basename(file_dir).replace('.vsi', '_decon.ome.tif')
    print(out_file)

    # Naive attempt to save as tiff
    #io.imsave(os.path.join(save_dir, out_file), decon)

    # reshape data TZCYX and remove axes that have only 1 length
    decon = np.squeeze(decon)

    tifffile.imwrite(os.path.join(save_dir,out_file), data=decon, bigtiff=True, metadata=image_metadata)



def decon_one_frame(file_dir, params=None):
    image = tifffile.imread(file_dir)

    if params is None:
        params = {'background': 'median'}

    # image = cv2.GaussianBlur(image, (0, 0), 1)
    print("Image shape for decon", image.shape)
    kernel_shape = image.shape
    ndim = 2
    params = CudaParams(background=params['background'], shape=kernel_shape, ndim=ndim)
    decon = richardson_lucy(image, params=params)

    out_file = os.path.basename(file_dir).rsplit('.', 2)
    out_file = out_file[0] + ".".join(["_decon", *out_file[1:]])

    tifffile.imwrite(os.path.join(os.path.dirname(file_dir), out_file), decon)


def get_overlapping_slices(total_slices, slice_step, overlap):
    slice_now = 0
    my_bins = []
    while slice_now + overlap <= total_slices:
        if slice_now + slice_step + overlap < total_slices:
            my_bins.append((slice_now, slice_now + slice_step + overlap))
        else:
            my_bins.append((slice_now, total_slices))
        slice_now = slice_now + slice_step
    return my_bins

jb.kill_vm()

if __name__ == '__main__':
    main()

