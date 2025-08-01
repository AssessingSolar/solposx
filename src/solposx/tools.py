"""Collection of utility functions."""

import pvlib
import numpy as np


def _pandas_to_utc(pd_object):
    """
    Convert a pandas datetime-like object to UTC, if localized.

    Parameters
    ----------
    pd_object : Localized DatetimeIndex or Timestamp

    Returns
    -------
    pandas object localized to UTC.

    Raises
    ------
    TypeError : Error raised if `pd_object` is time-zone naive.

    """
    try:
        pd_object_utc = pd_object.tz_convert("UTC")
    except TypeError:
        raise TypeError(
            "The provided time stamps are timezone naive."
            "Please make the time stamps timezone aware."
            "See ``pandas.Timestamp.tz_localize``."
        )
    return pd_object_utc


def _fractional_hour(times):
    """
    Calculate the fraction of the hour with microsecond resolution.

    Parameters
    ----------
    times : pd.DatetimeIndex

    Returns
    -------
    fraction_of_hour : pd.Index
    """
    hour = (
        times.hour
        + (times.minute + (times.second + times.microsecond * 1e-6) / 60) / 60
    )
    return hour


def calc_error(zenith_1, azimuth_1, zenith_2, azimuth_2):
    """
    Calculate angular difference metrics between two sets of solar positions.

    Parameters
    ----------
    zenith_1, zenith_2 : array-like
        Zenith angles for the two sets of solar positions. [degrees]
    azimuth_1, azimuth_2 : array-like
        Azimuth angles for the two sets of solar positions. [degrees]

    Returns
    -------
    out : dict
        Dict with keys:

        * zenith_bias, azimuth_bias: average (signed) difference in zenith/azimuth
        * zenith_mad, azimuth_mad: mean absolute difference in zenith/azimuth
        * zenith_rmsd, azimuth_rmsd: root-mean-squared difference in zenith/azimuth
        * combined_rmse: total angular root-mean-squared difference in position
    """
    zenith_diff = zenith_1 - zenith_2
    zenith_bias = zenith_diff.mean()
    zenith_mad = np.abs(zenith_diff).mean()
    zenith_rmsd = (zenith_diff**2).mean() ** 0.5

    azimuth_diff = (azimuth_1 - azimuth_2 + 180) % 360 - 180  # handle 0/360 correctly
    azimuth_bias = azimuth_diff.mean()
    azimuth_mad = np.abs(azimuth_diff).mean()
    azimuth_rmsd = (azimuth_diff**2).mean() ** 0.5

    aoi = pvlib.irradiance.aoi(zenith_1, azimuth_1, zenith_2, azimuth_2)
    combined_rmsd = (aoi**2).mean() ** 0.5

    out = {
        "zenith_bias": zenith_bias,
        "zenith_mad": zenith_mad,
        "zenith_rmsd": zenith_rmsd,
        "azimuth_bias": azimuth_bias,
        "azimuth_mad": azimuth_mad,
        "azimuth_rmsd": azimuth_rmsd,
        "combined_rmsd": combined_rmsd,
    }
    return out
