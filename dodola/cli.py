"""Commandline interface to the application.
"""

import logging
import click
import dodola.services as services


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Main entry point
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--debug/--no-debug", default=False, envvar="DODOLA_DEBUG")
def dodola_cli(debug):
    """GCM bias-correction and downscaling

    Authenticate with storage by setting the appropriate environment variables
    for your fsspec-compatible URL library.
    """
    noisy_loggers = [
        "azure.core.pipeline.policies.http_logging_policy",
        "asyncio",
        "adlfs.spec",
        "gcsfs",
        "chardet.universaldetector",
        "fsspec",
    ]
    for logger_name in noisy_loggers:
        nl = logging.getLogger(logger_name)
        nl.setLevel(logging.WARNING)

    if debug:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)


@dodola_cli.command(help="Prime a Zarr Store for regionally-written QDM output")
@click.option(
    "--simulation", "-s", required=True, help="URL to simulation store to adjust"
)
@click.option(
    "--years",
    required=True,
    help="firstyear,lastyear inclusive range of years in simulation to adjust and output",
)
@click.option("--variable", "-v", required=True, help="Variable name in data stores")
@click.option(
    "--out",
    "-o",
    required=True,
    help="URL to write Zarr Store with adjusted simulation year to",
)
@click.option(
    "--zarr-region-dims",
    required=True,
    help="'variable1,variable2' comma-delimited list of variables used to define region when writing",
)
@click.option(
    "--root-attrs-json-file",
    help="fsspec-compatible URL pointing to a JSON file to use as root ``attrs`` for output data.",
)
@click.option(
    "--new-attrs",
    multiple=True,
    help="'key1=value1' entry to merge into the output Dataset root metadata (attrs)",
)
def prime_qdm_output_zarrstore(
    simulation,
    variable,
    years,
    out,
    zarr_region_dims=None,
    root_attrs_json_file=None,
    new_attrs=None,
):
    """Initialize a Zarr Store for writing QDM output regionally in independent processes"""
    first_year, last_year = (int(x) for x in years.split(","))

    unpacked_attrs = None
    if new_attrs:
        unpacked_attrs = {k: v for x in new_attrs for k, v in (x.split("="),)}

    region_dims = zarr_region_dims.split(",")
    services.prime_qdm_output_zarrstore(
        simulation=simulation,
        years=(first_year, last_year),
        variable=variable,
        out=out,
        zarr_region_dims=region_dims,
        root_attrs_json_file=root_attrs_json_file,
        new_attrs=unpacked_attrs,
    )


@dodola_cli.command(help="Prime a Zarr Store for regionally-written QPLAD output")
@click.option(
    "--simulation", "-s", required=True, help="URL to simulation store to adjust"
)
@click.option("--variable", "-v", required=True, help="Variable name in data stores")
@click.option(
    "--out",
    "-o",
    required=True,
    help="URL to write Zarr Store with adjusted simulation year to",
)
@click.option(
    "--zarr-region-dims",
    required=True,
    help="'variable1,variable2' comma-delimited list of variables used to define region when writing",
)
@click.option(
    "--root-attrs-json-file",
    help="fsspec-compatible URL pointing to a JSON file to use as root ``attrs`` for output data.",
)
@click.option(
    "--new-attrs",
    multiple=True,
    help="'key1=value1' entry to merge into the output Dataset root metadata (attrs)",
)
def prime_qplad_output_zarrstore(
    simulation,
    variable,
    out,
    zarr_region_dims=None,
    root_attrs_json_file=None,
    new_attrs=None,
):
    """Initialize a Zarr Store for writing QPLAD output regionally in independent processes"""
    unpacked_attrs = None
    if new_attrs:
        unpacked_attrs = {k: v for x in new_attrs for k, v in (x.split("="),)}

    region_dims = zarr_region_dims.split(",")
    services.prime_qplad_output_zarrstore(
        simulation=simulation,
        variable=variable,
        out=out,
        zarr_region_dims=region_dims,
        root_attrs_json_file=root_attrs_json_file,
        new_attrs=unpacked_attrs,
    )


@dodola_cli.command(help="Adjust simulation year with quantile delta mapping (QDM)")
@click.option(
    "--simulation", "-s", required=True, help="URL to simulation store to adjust"
)
@click.option("--qdm", "-q", required=True, help="URL to trained QDM model store")
@click.option(
    "--years",
    required=True,
    help="firstyear,lastyear inclusive range of years in simulation to adjust and output",
)
@click.option("--variable", "-v", required=True, help="Variable name in data stores")
@click.option(
    "--out",
    "-o",
    required=True,
    help="URL to write Zarr Store with adjusted simulation year to",
)
@click.option(
    "--selslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'isel' slice input simulation before applying",
)
@click.option(
    "--iselslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'sel' slice input simulation before applying",
)
@click.option(
    "--out-zarr-region",
    multiple=True,
    required=False,
    help="variable=start,stop index to write output to region of existing Zarr Store",
)
@click.option(
    "--root-attrs-json-file",
    help="fsspec-compatible URL pointing to a JSON file to use as root ``attrs`` for output data.",
)
@click.option(
    "--new-attrs",
    multiple=True,
    help="'key1=value1' entry to merge into the output Dataset root metadata (attrs)",
)
def apply_qdm(
    simulation,
    qdm,
    years,
    variable,
    out,
    selslice=None,
    iselslice=None,
    out_zarr_region=None,
    root_attrs_json_file=None,
    new_attrs=None,
):
    """Adjust simulation years with QDM bias correction method, outputting Zarr Store"""
    first_year, last_year = (int(x) for x in years.split(","))

    unpacked_attrs = None
    if new_attrs:
        unpacked_attrs = {k: v for x in new_attrs for k, v in (x.split("="),)}

    sel_slices_d = None
    if selslice:
        sel_slices_d = {}
        for s in selslice:
            k, v = s.split("=")
            sel_slices_d[k] = slice(*map(str, v.split(",")))

    isel_slices_d = None
    if iselslice:
        isel_slices_d = {}
        for s in iselslice:
            k, v = s.split("=")
            isel_slices_d[k] = slice(*map(int, v.split(",")))

    out_zarr_region_d = None
    if out_zarr_region:
        out_zarr_region_d = {}
        for s in out_zarr_region:
            k, v = s.split("=")
            out_zarr_region_d[k] = slice(*map(int, v.split(",")))

    services.apply_qdm(
        simulation=simulation,
        qdm=qdm,
        years=range(
            first_year, last_year + 1
        ),  # +1 because years is an inclusive range.
        variable=variable,
        out=out,
        sel_slice=sel_slices_d,
        isel_slice=isel_slices_d,
        out_zarr_region=out_zarr_region_d,
        root_attrs_json_file=root_attrs_json_file,
        new_attrs=unpacked_attrs,
    )


@dodola_cli.command(help="Train quantile delta mapping (QDM)")
@click.option(
    "--historical", "-h", required=True, help="URL to historical simulation store"
)
@click.option("--reference", "-r", required=True, help="URL to reference data store")
@click.option("--variable", "-v", required=True, help="Variable name in data stores")
@click.option(
    "--kind",
    "-k",
    required=True,
    type=click.Choice(["additive", "multiplicative"], case_sensitive=False),
    help="Variable kind for mapping",
)
@click.option("--out", "-o", required=True, help="URL to write QDM model to")
@click.option(
    "--selslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'isel' slice inputs before training",
)
@click.option(
    "--iselslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'sel' slice inputs before training",
)
def train_qdm(
    historical, reference, out, variable, kind, selslice=None, iselslice=None
):
    """Train Quantile Delta Mapping (QDM) model and output to storage"""
    sel_slices_d = None
    isel_slices_d = None

    if selslice:
        sel_slices_d = {}
        for s in selslice:
            k, v = s.split("=")
            sel_slices_d[k] = slice(*map(str, v.split(",")))

    if iselslice:
        isel_slices_d = {}
        for s in iselslice:
            k, v = s.split("=")
            isel_slices_d[k] = slice(*map(int, v.split(",")))

    services.train_qdm(
        historical=historical,
        reference=reference,
        out=out,
        variable=variable,
        kind=kind,
        sel_slice=sel_slices_d,
        isel_slice=isel_slices_d,
    )


@dodola_cli.command(
    help="Adjust (downscale) simulation year with Quantile-Preserving, Localized Analogs Downscaling (QPLAD)"
)
@click.option(
    "--simulation", "-s", required=True, help="URL to simulation store to adjust"
)
@click.option(
    "--qplad",
    "-d",
    required=True,
    help="URL to trained QPLAD store of adjustment factors",
)
@click.option("--variable", "-v", required=True, help="Variable name in data stores")
@click.option(
    "--out",
    "-o",
    required=True,
    help="URL to write Zarr with downscaled output to",
)
@click.option(
    "--selslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'isel' slice input simulation before applying",
)
@click.option(
    "--iselslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'sel' slice input simulation before applying",
)
@click.option(
    "--out-zarr-region",
    multiple=True,
    required=False,
    help="variable=start,stop index to write output to region of existing Zarr Store",
)
@click.option(
    "--root-attrs-json-file",
    help="fsspec-compatible URL pointing to a JSON file to use as root ``attrs`` for output data.",
)
@click.option(
    "--new-attrs",
    multiple=True,
    help="'key1=value1' entry to merge into the output Dataset root metadata (attrs)",
)
@click.option(
    "--wetday-post-correction",
    type=bool,
    default=False,
    help="Whether to apply wet day frequency correction on downscaled data",
)
def apply_qplad(
    simulation,
    qplad,
    variable,
    out,
    selslice=None,
    iselslice=None,
    out_zarr_region=None,
    root_attrs_json_file=None,
    new_attrs=None,
    wetday_post_correction=False,
):
    """Adjust simulation with QPLAD downscaling method, outputting Zarr Store"""
    unpacked_attrs = None
    if new_attrs:
        unpacked_attrs = {k: v for x in new_attrs for k, v in (x.split("="),)}

    sel_slices_d = None
    if selslice:
        sel_slices_d = {}
        for s in selslice:
            k, v = s.split("=")
            sel_slices_d[k] = slice(*map(str, v.split(",")))

    isel_slices_d = None
    if iselslice:
        isel_slices_d = {}
        for s in iselslice:
            k, v = s.split("=")
            isel_slices_d[k] = slice(*map(int, v.split(",")))

    out_zarr_region_d = None
    if out_zarr_region:
        out_zarr_region_d = {}
        for s in out_zarr_region:
            k, v = s.split("=")
            out_zarr_region_d[k] = slice(*map(int, v.split(",")))

    services.apply_qplad(
        simulation=simulation,
        qplad=qplad,
        variable=variable,
        out=out,
        sel_slice=sel_slices_d,
        isel_slice=isel_slices_d,
        out_zarr_region=out_zarr_region_d,
        root_attrs_json_file=root_attrs_json_file,
        new_attrs=unpacked_attrs,
        wet_day_post_correction=wetday_post_correction,
    )


@dodola_cli.command(
    help="Train Quantile-Preserving, Localized Analogs Downscaling (QPLAD)"
)
@click.option(
    "--coarse-reference", "-cr", required=True, help="URL to coarse reference store"
)
@click.option(
    "--fine-reference", "-fr", required=True, help="URL to fine reference store"
)
@click.option("--variable", "-v", required=True, help="Variable name in data stores")
@click.option(
    "--kind",
    "-k",
    required=True,
    type=click.Choice(["additive", "multiplicative"], case_sensitive=False),
    help="Variable kind for mapping",
)
@click.option("--out", "-o", required=True, help="URL to write QDM model to")
@click.option(
    "--selslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'isel' slice inputs before training",
)
@click.option(
    "--iselslice",
    multiple=True,
    required=False,
    help="variable=start,stop to 'sel' slice inputs before training",
)
def train_qplad(
    coarse_reference, fine_reference, out, variable, kind, selslice=None, iselslice=None
):
    """Train Quantile-Preserving, Localized Analogs Downscaling (QPLAD) model and output to storage"""
    sel_slices_d = None
    isel_slices_d = None

    if selslice:
        sel_slices_d = {}
        for s in selslice:
            k, v = s.split("=")
            sel_slices_d[k] = slice(*map(str, v.split(",")))

    if iselslice:
        isel_slices_d = {}
        for s in iselslice:
            k, v = s.split("=")
            isel_slices_d[k] = slice(*map(int, v.split(",")))

    services.train_qplad(
        coarse_reference=coarse_reference,
        fine_reference=fine_reference,
        out=out,
        variable=variable,
        kind=kind,
        sel_slice=sel_slices_d,
        isel_slice=isel_slices_d,
    )


@dodola_cli.command(help="Clean up and standardize GCM")
@click.argument("x", required=True)
@click.argument("out", required=True)
@click.option(
    "--drop-leapdays/--no-drop-leapdays",
    default=True,
    help="Whether to remove leap days",
)
def cleancmip6(x, out, drop_leapdays):
    """Clean and standardize CMIP6 GCM to 'out'. If drop-leapdays option is set, remove leap days"""
    services.clean_cmip6(x, out, drop_leapdays)


@dodola_cli.command(help="Remove leap days and update calendar")
@click.argument("x", required=True)
@click.argument("out", required=True)
def removeleapdays(x, out):
    """Remove leap days and update calendar attribute"""
    services.remove_leapdays(x, out)


@dodola_cli.command(help="Get attrs from data")
@click.argument("x", required=True)
@click.option("--variable", "-v", help="Variable name in data stores")
def get_attrs(x, variable=None):
    """Get JSON str of data attrs metadata."""
    click.echo(services.get_attrs(x, variable))


@dodola_cli.command(help="Rechunk Zarr store")
@click.argument("x", required=True)
@click.option(
    "--chunk", "-c", multiple=True, required=True, help="coord=chunksize to rechunk to"
)
@click.option("--out", "-o", required=True)
def rechunk(x, chunk, out):
    """Rechunk Zarr store"""
    # Convert ["k1=1", "k2=2"] into {k1: 1, k2: 2}
    coord_chunks = {c.split("=")[0]: int(c.split("=")[1]) for c in chunk}

    services.rechunk(
        str(x),
        target_chunks=coord_chunks,
        out=out,
    )


@dodola_cli.command(help="Build NetCDF weights file for regridding")
@click.argument("x", required=True)
@click.option("--out", "-o", required=True)
@click.option(
    "--method",
    "-m",
    required=True,
    help="Regridding method - 'bilinear' or 'conservative'",
)
@click.option("--domain-file", "-d", help="Domain file to regrid to")
@click.option(
    "--weightspath",
    "-w",
    default=None,
    help="Local path to existing regrid weights file",
)
@click.option("--astype", "-t", default=None, help="Type to recast output to")
@click.option(
    "--cyclic", default=None, help="Add wrap-around values to dim before regridding"
)
def regrid(x, out, method, domain_file, weightspath, astype, cyclic):
    """Regrid a target climate dataset

    Note, the weightspath only accepts paths to NetCDF files on the local disk. See
    https://xesmf.readthedocs.io/ for details on requirements for `x` with
    different methods.
    """
    # Configure storage while we have access to users configurations.
    services.regrid(
        str(x),
        out=str(out),
        method=str(method),
        domain_file=domain_file,
        weights_path=weightspath,
        astype=astype,
        add_cyclic=cyclic,
    )


@dodola_cli.command(help="Correct wet day frequency in a dataset")
@click.argument("x", required=True)
@click.option("--out", "-o", required=True)
@click.option(
    "--process",
    "-p",
    required=True,
    type=click.Choice(["pre", "post"], case_sensitive=False),
    help="Whether to pre or post process wet day frequency",
)
def correct_wetday_frequency(x, out, process):
    """Correct wet day frequency in a dataset"""
    services.correct_wet_day_frequency(str(x), out=str(out), process=str(process))


@dodola_cli.command(help="Adjust maximum precipitation in a dataset")
@click.argument("x", required=True)
@click.option("--out", "-o", required=True)
@click.option(
    "--threshold", "-t", help="Threshold for correcting maximum precipitation"
)
def adjust_maximum_precipitation(x, out, threshold=3000.0):
    """Apply maximum precipitation threshold to a dataset"""
    services.adjust_maximum_precipitation(
        str(x), out=str(out), threshold=float(threshold)
    )


@dodola_cli.command(
    help="Apply a floor to diurnal temperature range (DTR) in a dataset"
)
@click.argument("x", required=True)
@click.option("--out", "-o", required=True)
@click.option("--floor", "-f", help="floor to apply to DTR values")
def apply_dtr_floor(x, out, floor=1.0):
    """Apply a floor to diurnal temperature range (DTR) in a dataset"""
    services.apply_dtr_floor(str(x), out=str(out), floor=float(floor))


@dodola_cli.command(
    help="Apply a ceiling to diurnal temperature range (DTR) in a dataset"
)
@click.argument("x", required=True)
@click.option("--out", "-o", required=True)
@click.option("--ceiling", "-c", help="ceiling to apply to DTR values")
def apply_non_polar_dtr_ceiling(x, out, ceiling=70.0):
    """Apply a ceiling to diurnal temperature range (DTR) in a dataset"""
    services.apply_non_polar_dtr_ceiling(str(x), out=str(out), ceiling=float(ceiling))


@dodola_cli.command(help="Validate a CMIP6, bias corrected or downscaled dataset")
@click.argument("x", required=True)
@click.option("--variable", "-v", required=True)
@click.option(
    "--data-type",
    "-d",
    required=True,
    type=click.Choice(["cmip6", "bias_corrected", "downscaled"], case_sensitive=False),
    help="Which data type to validate",
)
@click.option(
    "--time-period",
    "-t",
    required=True,
    type=click.Choice(["historical", "future"], case_sensitive=False),
    help="Which time period to validate",
)
def validate_dataset(x, variable, data_type, time_period):
    """Validate a dataset"""
    services.validate(
        str(x),
        var=str(variable),
        data_type=str(data_type),
        time_period=str(time_period),
    )
