import os.path
import numpy as np
import tables as hdf

from uncoverml import geoio
from uncoverml import patch


def output_features(feature_vector, mask_vector, outfile):
    """
    Writes a vector of features out to a standard HDF5 format. The function
    assumes that it is only 1 chunk of a larger vector, so outputs a numerical
    suffix to the file as an index.

    Parameters
    ----------
        feature_vector: array
            A 2D numpy array of shape (nPoints, nDims) of type float.
        mask_vector: array
            A 2D numpy mask array of shape (nPoints, nDims) of type bool
        outfile: path
            The name of the output file
    """
    h5file = hdf.open_file(outfile, mode='w')
    array_shape = feature_vector.shape

    filters = hdf.Filters(complevel=5, complib='zlib')
    h5file.create_carray("/", "features", filters=filters,
                         atom=hdf.Float64Atom(), shape=array_shape)
    h5file.root.features[:] = feature_vector
    h5file.create_carray("/","mask",filters=filters,
                         atom=hdf.BoolAtom(), shape=array_shape)
    h5file.root.mask[:] = mask_vector
    h5file.close()

def input_features(infile):
    """
    Reads a vector of features out from a standard HDF5 format. The function
    assumes the file it is reading was written by output_features

    Parameters
    ----------
        infile: path
            The name of the input file
    Returns
    -------
        data: array
            A 2D numpy array of shape (nPoints, nDims) of type float
    """
    with hdf.open_file(infile, mode='r') as f:
        data = f.root.features[:]
    return data

def transform(x, x_mask):
    return x.flatten(), x_mask.flatten()

def transform(img, img_mask, mean, var, onehot):
    
    x_m = x - mean if mean is not None else x
    x_v = x_m/var if var is not None else x_m
    return x_v


def patches_from_image(image, patchsize, targets=None):
    """
    Pulls out masked patches from a geotiff, either everywhere or 
    at locations specificed by a targets shapefile
    """
    # Get the target points if they exist:
    data_and_mask = image.data()
    data = data_and_mask.data
    data_dtype = data.dtype
    mask = data_and_mask.mask
    pixels = None
    if targets is not None:
        lonlats = geoio.points_from_hdf(targets)
        inx = np.logical_and(lonlats[:, 0] >= image.xmin,
                             lonlats[:, 0] < image.xmax)
        iny = np.logical_and(lonlats[:, 1] >= image.ymin,
                             lonlats[:, 1] < image.ymax)
        valid = np.logical_and(inx, iny)
        valid_lonlats = lonlats[valid]
        pixels = image.lonlat2pix(valid_lonlats, centres=True)
        patches = patch.point_patches(data, patchsize, pixels)
        patch_mask = patch.point_patches(mask, patchsize, pixels)
    else:
        patches = patch.grid_patches(data, patchsize)
        patch_mask = patch.grid_patches(mask, patchsize)

    patch_data = np.array(list(patches), dtype=data_dtype)
    mask_data = np.array(list(patch_mask), dtype=bool)

    return patch_data, mask_data


    # transformed_data = [transform(x,m) for x,m in zip(patches, patch_mask)]
    # t_patches, t_mask = zip(*transformed_data)
    # features = np.array(t_patches, dtype=float)
    # feature_mask = np.array(t_mask, dtype=bool)
    # filename = os.path.join(output_dir,
    #                         name + "_{}.hdf5".format(image.chunk_idx))
    # output_features(features, feature_mask, filename)

