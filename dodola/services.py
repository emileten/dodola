"""Used by the CLI or any UI to deliver services to our lovely users
"""
from functools import wraps
import logging
import os
from tempfile import TemporaryDirectory
from rechunker import rechunk as rechunker_rechunk
from dodola.core import (
    apply_bias_correction,
    build_xesmf_weights_file,
    xesmf_regrid,
    standardize_gcm,
    xclim_remove_leapdays,
)

logger = logging.getLogger(__name__)


def log_service(func):
    """Decorator for dodola.services to log service start and stop"""

    @wraps(func)
    def service_logger(*args, **kwargs):
        servicename = func.__name__
        logger.info(f"Starting {servicename} dodola service")
        func(*args, **kwargs)
        logger.info(f"dodola service {servicename} done")

    return service_logger


@log_service
def bias_correct(
    x, x_train, train_variable, y_train, out, out_variable, method, storage
):
    """Bias correct input model data with IO to storage

    Parameters
    ----------
    x : str
        Storage URL to input data to bias correct.
    x_train : str
        Storage URL to input biased data to use for training bias-correction
        model.
    train_variable : str
        Variable name used in training and obs data.
    y_train : str
        Storage URL to input 'true' data or observations to use for training
        bias-correction model.
    out : str
        Storage URL to write bias-corrected output to.
    out_variable : str
        Variable name used as output variable name.
    method : str
        Bias correction method to be used.
    storage : dodola.repository._ZarrRepo
        Storage abstraction for data IO.
    """
    gcm_training_ds = storage.read(x_train)
    obs_training_ds = storage.read(y_train)
    gcm_predict_ds = storage.read(x)

    # This is all made up demo. Just get the output dataset the user expects.
    bias_corrected_ds = apply_bias_correction(
        gcm_training_ds,
        obs_training_ds,
        gcm_predict_ds,
        train_variable,
        out_variable,
        method,
    )

    storage.write(out, bias_corrected_ds)


@log_service
def build_weights(x, method, storage, target_resolution=1.0, outpath=None):
    """Generate local NetCDF weights file for regridding climate data

    Parameters
    ----------
    x : str
        Storage URL to input xr.Dataset that will be regridded.
    method : str
        Method of regridding. Passed to ``xesmf.Regridder``.
    target_resolution : float, optional
        Decimal-degree resolution of global grid to regrid to.
    storage : dodola.repository._ZarrRepo
        Storage abstraction for data IO.
    outpath : optional
        Local file path name to write regridding weights file to.
    """
    ds = storage.read(x)
    build_xesmf_weights_file(
        ds, method=method, target_resolution=target_resolution, filename=outpath
    )


@log_service
def rechunk(x, target_chunks, out, max_mem, storage):
    """Rechunk data to specification

    Parameters
    ----------
    x : str
        Storage URL to input data.
    target_chunks : dict
        A dict of dicts. Top-level dict key maps variables name in `ds` to an
        inner dict {coordinate_name: chunk_size} mapping showing how data is
        to be rechunked.
    out : str
        Storage URL to write rechunked output to.
    max_mem : int or str
        Maximum memory to use for rechunking (bytes).
    storage : dodola.repository._ZarrRepo
        Storage abstraction for data IO.
    """
    ds = storage.read(x)

    # Using tempdir for isolation/cleanup as rechunker dumps zarr files to disk.
    with TemporaryDirectory() as tmpdir:
        tmpzarr_path = os.path.join(tmpdir, "rechunk_tmp.zarr")
        plan = rechunker_rechunk(
            ds,
            target_chunks=target_chunks,
            target_store=storage.get_mapper(out),  # Stream directly into storage.
            temp_store=tmpzarr_path,
            max_mem=max_mem,
        )
        plan.execute()
        logger.info(f"Written {out}")


@log_service
def regrid(x, out, method, storage, domain_file, weights_path=None):
    """Regrid climate data

    Parameters
    ----------
    x : str
        Storage URL to input xr.Dataset that will be regridded.
    out : str
        Storage URL to write regridded output to.
    method : str
        Method of regridding. Passed to ``xesmf.Regridder``.
    storage : dodola.repository._ZarrRepo
        Storage abstraction for data IO.
    domain_file : str
        Storage URL to input xr.Dataset domain file to regrid to.
    weights_path : optional
        Local file path name to write regridding weights file to.
    """
    ds = storage.read(x)

    ds_domain = storage.read(domain_file)

    regridded_ds = xesmf_regrid(
        ds,
        ds_domain,
        method=method,
        weights_path=weights_path,
    )

    storage.write(out, regridded_ds)


@log_service
def clean_cmip6(x, out, leapday_removal, storage):
    """Cleans and standardizes CMIP6 GCM

    Parameters
    ----------
    x : str
        Storage URL to input xr.Dataset that will be cleaned.
    out : str
        Storage URL to write cleaned GCM output to.
    leapday_removal : bool
        Whether or not to remove leap days.
    storage : dodola.repository._ZarrRepo
        Storage abstraction for data IO.
    """
    ds = storage.read(x)
    cleaned_ds = standardize_gcm(ds, leapday_removal)
    storage.write(out, cleaned_ds)


@log_service
def remove_leapdays(x, out, storage):
    """Removes leap days and updates calendar attribute

    Parameters
    ----------
    x : str
        Storage URL to input xr.Dataset that will be regridded.
    out : str
        Storage URL to write regridded output to.
    storage : dodola.repository._ZarrRepo
        Storage abstraction for data IO.
    """
    ds = storage.read(x)
    noleap_ds = xclim_remove_leapdays(ds)
    storage.write(out, noleap_ds)


@log_service
def disaggregate(x, weights, out, repo):
    """This is just an example. Please replace or delete."""
    raise NotImplementedError
