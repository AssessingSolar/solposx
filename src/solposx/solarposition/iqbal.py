import pandas as pd
import numpy as np
from pvlib.tools import acosd, sind, cosd
from solposx.tools import _pandas_to_utc, _fractional_hour


def iqbal(times, latitude, longitude):
    """
    Calculate solar position using the Iqbal algorithm.

    The Iqbal algorithm [1]_ is based on equations in [2]_.

    Parameters
    ----------
    times : pandas.DatetimeIndex
        Time stamps for which to calculate solar position. Must be timezone
        aware.
    latitude : float
        Latitude in decimal degrees. Positive north of equator, negative
        to south. [degrees]
    longitude : float
        Longitude in decimal degrees. Positive east of prime meridian,
        negative to west. [degrees]

    Returns
    -------
    pandas.DataFrame
        DataFrame with the following columns (all values in degrees):

        - elevation : actual sun elevation (not accounting for refraction).
        - zenith : actual sun zenith (not accounting for refraction).
        - azimuth : sun azimuth, east of north.

    References
    ----------
    .. [1] M. Iqbal, “An Introduction to Solar Radiation,” 1983,
       :doi:`10.1016/b978-0-12-373750-2.x5001-0`.
    .. [2] J. W. Spencer, "Fourier series representation of the position of the
       Sun," Search, vol. 2, no. 5, pp. 172, 1971.
    """
    times_utc = _pandas_to_utc(times)

    dayofyear = times_utc.dayofyear
    day_angle = 2 * np.pi * (dayofyear - 1) / 365  # [radians]

    declination = (
        +0.006918
        - 0.399912 * np.cos(day_angle)
        + 0.070257 * np.sin(day_angle)
        - 0.006758 * np.cos(2 * day_angle)
        + 0.000907 * np.sin(2 * day_angle)
        - 0.002697 * np.cos(3 * day_angle)
        + 0.00148 * np.sin(3 * day_angle)
    ) * (
        180 / np.pi
    )  # [degrees]

    # equation of time [minutes]
    eot = (
        (
            0.0000075
            + 0.001868 * np.cos(day_angle)
            - 0.032077 * np.sin(day_angle)
            - 0.014615 * np.cos(2 * day_angle)
            - 0.040849 * np.sin(2 * day_angle)
        )
        * 1440
        / 2
        / np.pi
    )

    # hour angle [degrees]
    hour_angle = (_fractional_hour(times_utc) - 12) * 15 + longitude + eot / 4

    zenith = acosd(
        sind(declination) * sind(latitude)
        + cosd(declination) * cosd(latitude) * cosd(hour_angle)
    )

    # The azimuth function provided in [1] does not always select the right
    # quadrant. Therefore, this implementation uses the arctan2 method.
    azimuth = (
        np.rad2deg(
            np.arctan2(
                sind(hour_angle) * cosd(declination),
                cosd(hour_angle) * sind(latitude) * cosd(declination)
                - cosd(latitude) * sind(declination),
            )
        )
        + 180
    )

    result = pd.DataFrame(
        {
            "elevation": 90 - zenith,
            "zenith": zenith,
            "azimuth": azimuth,
        },
        index=times,
    )
    return result
