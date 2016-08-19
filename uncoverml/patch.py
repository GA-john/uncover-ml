""" Image patch extraction and windowing utilities. """

from __future__ import division

import numpy as np
import skimage


def grid_patches(image, pwidth):
    """
    Generate (overlapping) patches from an image. This function extracts square
    patches from an image in an overlapping, dense grid.

    Parameters
    ----------
        image: ndarray
            an array of shape (x, y) or (x, y, channels).
        pwidth: int
            the half-width of the square patches to extract, in pixels. E.g.
            pwidth = 0 gives a 1x1 patch, pwidth = 1 gives a 3x3 patch, pwidth
            = 2 gives a 5x5 patch etc. The formula for calculating the full
            patch width is pwidth * 2 + 1.
    Returns
    -------
        patch: ndarray
            An image of shape (x, y, channels*psize*psize), where
            psize = pwidth * 2 + 1
    """
    # Check and get image dimensions
    assert image.ndim == 3
    window = (2 * pwidth + 1, 2 * pwidth + 1, 1)
    x = skimage.util.view_as_windows(image, window_shape=window, step=1)
    # window_z, img_x, img_y, window_x, window_y, channel
    x = x.transpose((5, 0, 1, 3, 4, 2))[0]
    x = x.reshape(-1, x.shape[2], x.shape[3], x.shape[4])
    return x


def point_patches(image, pwidth, points):
    """
    Extract patches from an image at specified points.

    Parameters
    ----------
        image: ndarray
            an array of shape (x, y, channels).
        pwidth: int
            the half-width of the square patches to extract, in pixels. E.g.
            pwidth = 0 gives a 1x1 patch, pwidth = 1 gives a 3x3 patch, pwidth
            = 2 gives a 5x5 patch etc. The formula for calculating the full
            patch width is pwidth * 2 + 1.
        points: ndarray
           of shape (N, 2) where there are N points, each with an x and y
           coordinate of the patch centre within the image.

    Returns
    -------
        patches: ndarray
            An image patch array of shape (N, psize, psize, channels), where
            psize = pwidth * 2 + 1
    """
    points_x = points[:, 0]
    points_y = points[:, 1]
    npixels = points.shape[0]
    side = 2 * pwidth + 1
    offsets = np.mgrid[0:side, 0:side].transpose((1, 2, 0)).reshape((-1, 2))
    # centre the patches on the middle pixel
    dtype = image.dtype

    nchannels = image.shape[2]
    output = np.empty((npixels, side, side, nchannels), dtype=dtype)

    for x, y in offsets:
        output[:, x, y] = image[points_x + x - pwidth,
                                points_y + y - pwidth]
    return output


def _spacing(dimension, psize, pstride):
    """
    Calculate the patch spacings along a dimension of an image.
    Returns the lowest-index corner of the patches for a given
    dimension,  size and stride. Always returns at least 1 patch index
    """
    assert dimension >= psize  # otherwise a single patch won't fit
    assert psize > 0
    assert pstride > 0  # otherwise we'll never move along the image

    offset = int(np.floor(float((dimension - psize) % pstride) / 2))
    return range(offset, dimension - psize + 1, pstride)


def _checkim(image):
    if image.ndim == 3:
        (Ih, Iw, Ic) = image.shape
    elif image.ndim == 2:
        (Ih, Iw) = image.shape
        Ic = 1
    else:
        raise ValueError('image must be a 2D or 3D array')

    if (Ih < 1) or (Iw < 1):
        raise ValueError('image must be a 2D or 3D array')

    return Ih, Iw, Ic


def _image_to_data(image):
    """
    breaks up an image object into arrays suitable for sending to the
    patching functions
    """
    data_and_mask = image.data()
    data = data_and_mask.data
    data_dtype = data.dtype
    mask = data_and_mask.mask
    return data, mask, data_dtype


def _all_patches(image, patchsize):
    data, mask, data_dtype = _image_to_data(image)
    patches = grid_patches(data, patchsize)
    patch_mask = grid_patches(mask, patchsize)
    result = np.ma.masked_array(data=patches, mask=patch_mask)
    return result


def load(image, patchsize, targets=None):
    if targets is None:
        result = _all_patches(image, patchsize)
    else:
        result = _patches_at_target(image, patchsize, targets)
    return result


def _patches_at_target(image, patchsize, targets):
    data, mask, data_dtype = _image_to_data(image)

    lonlats = targets.positions
    valid = image.in_bounds(lonlats)
    valid_indices = np.where(valid)[0]

    if len(valid_indices) > 0:
        valid_lonlats = lonlats[valid]
        pixels = image.lonlat2pix(valid_lonlats)
        patches = point_patches(data, patchsize, pixels)
        patch_mask = point_patches(mask, patchsize, pixels)
        patch_array = np.ma.masked_array(data=patches, mask=patch_mask)

    else:
        patch_array = None

    return patch_array
