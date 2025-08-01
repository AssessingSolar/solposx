import pandas as pd
from pvlib.tools import sind, cosd, asind, acosd, tand
import numpy as np
from pvlib import spa
from solposx import refraction
from solposx.tools import _pandas_to_utc, _fractional_hour


def noaa(times, latitude, longitude, delta_t=67.0):
    """
    Calculate solar position using the NOAA algorithm.

    NOAA's algorithm [1]_ has a stated accuracy of 0.0167 degrees
    from years -2000 to +3000 for latitudes within +/- 72 degrees. For
    latitudes outside this the accuracy is 0.167 degrees.

    The NOAA algorithm uses by default the Hughes refraction model,
    see ~:py:func:`solposx.refraction.hughes`.  Note, that the implementation
    deviates slightly from Hughes in that refraction is set to 0 for solar
    elevation angles above 85 degrees.

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
    delta_t : numeric, default 67.0
        Difference between terrestrial time and UT1.
        If delta_t is None, uses spa.calculate_deltat
        using time.year and time.month from pandas.DatetimeIndex.
        For most simulations the default delta_t is sufficient.
        The USNO has historical and forecasted delta_t [3]_. [seconds]

    Returns
    -------
    pandas.DataFrame
        DataFrame with the following columns (all values in degrees):

        - elevation : actual sun elevation (not accounting for refraction).
        - apparent_elevation : sun elevation, accounting for
          atmospheric refraction.
        - zenith : actual sun zenith (not accounting for refraction).
        - apparent_zenith : sun zenith, accounting for atmospheric
          refraction.
        - azimuth : sun azimuth, east of north.

    Notes
    -----
    The algorithm is from Astronomical Algorithms by Jean Meeus [2]_.

    References
    ----------
    .. [1] Solar Calculation Details. Global Monitoring
       Laboratory Earth System Research Laboratories.
       https://gml.noaa.gov/grad/solcalc/calcdetails.html
    .. [2] J. Meeus, "Astronomical Algorithms," 1991.
       https://archive.org/details/astronomicalalgorithmsjeanmeeus1991
    .. [3] USNO delta T:
       https://maia.usno.navy.mil/products/deltaT
    """
    times_utc = _pandas_to_utc(times)
    julian_date = times_utc.to_julian_date()
    jc = (julian_date - 2451545) / 36525

    # Allow for latitude of -90 and 90 on Ubunty and MacOS
    if latitude == 90:
        latitude += -1e-6
    elif latitude == -90:
        latitude += 1e-6

    if delta_t is None:
        delta_t = spa.calculate_deltat(times_utc.year, times_utc.month)

    # [degrees]
    mean_long = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360

    mean_anom = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)

    eccent_earth_orbit = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)

    sun_eq_ctr = (
        sind(mean_anom) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + sind(2 * mean_anom) * (0.019993 - 0.000101 * jc)
        + sind(3 * mean_anom) * 0.000289
    )

    sun_true_long = mean_long + sun_eq_ctr

    sun_app_long = sun_true_long - 0.00569 - 0.00478 * sind(125.04 - 1934.136 * jc)

    mean_obliq_ecliptic = (
        23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    )

    obliq_corr = mean_obliq_ecliptic + 0.00256 * cosd(125.04 - 1934.136 * jc)

    sun_declin = asind(sind(obliq_corr) * sind(sun_app_long))

    var_y = tand(obliq_corr / 2) ** 2

    eot = 4 * np.degrees(
        +var_y * sind(2 * mean_long)
        - 2 * eccent_earth_orbit * sind(mean_anom)
        + 4 * eccent_earth_orbit * var_y * sind(mean_anom) * cosd(2 * mean_long)
        - 0.5 * (var_y**2) * sind(4 * mean_long)
        - 1.25 * (eccent_earth_orbit**2) * sind(2 * mean_anom)
    )

    minutes = _fractional_hour(times_utc) * 60

    true_solar_time = (minutes + eot + 4 * longitude) % 1440

    hour_angle = np.where(
        true_solar_time / 4 < 0,
        true_solar_time / 4 + 180,
        true_solar_time / 4 - 180,
    )

    zenith = acosd(
        sind(latitude) * sind(sun_declin)
        + cosd(latitude) * cosd(sun_declin) * cosd(hour_angle)
    )

    azimuth = np.where(
        hour_angle > 0,
        (
            acosd(
                ((sind(latitude) * cosd(zenith)) - sind(sun_declin))
                / (cosd(latitude) * sind(zenith))
            )
            + 180 % 360
        ),
        (
            540
            - acosd(
                ((sind(latitude) * cosd(zenith)) - sind(sun_declin))
                / (cosd(latitude) * sind(zenith))
            )
        )
        % 360,
    )

    elevation = 90 - zenith
    refraction_correction = refraction.hughes(
        elevation=np.array(elevation), pressure=101325, temperature=10
    )
    # Minor deviation of the refraction correction used by NOAA
    refraction_correction[elevation > 85] = 0

    result = pd.DataFrame(
        {
            "elevation": elevation,
            "apparent_elevation": elevation + refraction_correction,
            "zenith": zenith,
            "apparent_zenith": zenith - refraction_correction,
            "azimuth": azimuth,
        },
        index=times,
    )
    return result
