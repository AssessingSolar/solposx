from pvlib.tools import sind, cosd, asind
import numpy as np
import pandas as pd
from solposx import refraction
from solposx.tools import _pandas_to_utc, _fractional_hour


def michalsky(
    times, latitude, longitude, spencer_correction=True, julian_date="original"
):
    """
    Calculate solar position using the Michalsky algorithm.

    Michalsky's algorithm [1]_ has a stated accuracy of 0.01 degrees
    from 1950 to 2050.

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
    spencer_correction : bool, default True
        Applies the correction suggested by Spencer [2]_ so the algorithm
        works for all latitudes.
    julian_date : string, default 'original'
        Julian date calculation. Can be one of the following:
            * ``'original'``: calculation based on Michalsky's paper [1]_.
            * ``'pandas'``: calculation using a pandas build-in function

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

    Raises
    ------
    ValueError
        An error is raised if the julian_date calculation is not `original`
        or `pandas`.

    Notes
    -----
    The Michalsky algorithm is based equations in the Astronomical Almanac.

    As pointed out by Spencer (1989) [2]_, the original Michalsky
    algorithm [1]_ did not work for the southern hemisphere. This
    implementation includes by default the correction provided by Spencer such
    that it works for all latitudes.

    Minor clarifications were made to the original paper have been published
    as errata in [3]_ and [4]_.

    The Julian date calculation in the original Michalsky paper [1]_ ensures
    the stated accuracy (0.01 degrees) only for the period 1950 - 2050. Outside
    this period, the Julian date does not handle leap years correctly. Thus,
    there is the option to use the
    :py:func:`pandas.DatetimeIndex.to_julian_date` method.

    References
    ----------
    .. [1] J. J. Michalsky, "The Astronomical Almanac’s algorithm for
       approximate solar position (1950–2050)," Solar Energy, vol. 40, no. 3,
       pp. 227–235, 1988, :doi:`10.1016/0038-092x(88)90045-x`.
    .. [2] J. W. Spencer, “Comments on The Astronomical Almanac’s Algorithm for
       Approximate Solar Position (1950–2050),” Solar Energy, vol. 42, no. 4,
       pp. 353, 1989, :doi:`10.1016/0038-092x(89)90039-x`.
    .. [3] J. J. Michalsky, “Errata,” Solar Energy, vol. 41, no. 1,
       pp. 113, 1988, :doi:`10.1016/0038-092x(88)90122-3`.
    .. [4] J. J. Michalsky, “Errata,” Solar Energy, vol. 43, no. 5,
       pp. 323, 1989, :doi:`10.1016/0038-092x(89)90122-9`.
    """
    times_utc = _pandas_to_utc(times)

    hour = _fractional_hour(times_utc)

    if julian_date == "original":
        year = times_utc.year
        day = times_utc.dayofyear
        delta = year - 1949
        leap = np.floor(delta / 4)
        jd = 2432916.5 + delta * 365 + leap + day + hour / 24
    elif julian_date == "pandas":
        jd = times_utc.to_julian_date()
    else:
        raise ValueError("`julian_date` has to be either `original` or `pandas`.")

    n = jd - 2451545.0

    # L - mean longitude [degrees]
    L = 280.460 + 0.9856474 * n
    # L has to be between 0 and 360 deg
    L = L % 360

    # g - mean anomaly [degrees]
    g = 357.528 + 0.9856003 * n
    # g has to be between 0 and 360 deg
    g = g % 360

    # l - ecliptic longitude [degrees]
    l = L + 1.915 * sind(g) + 0.02 * sind(2 * g)
    # l has to be between 0 and 360 deg
    l = l % 360

    # ep - obliquity of the ecliptic [degrees]
    ep = 23.439 - 0.0000004 * n

    # ra - right ascension [degrees]
    ra = np.rad2deg(np.arctan2(cosd(ep) * sind(l), cosd(l)))
    # ra has to be between 0 and 360 deg
    ra = ra % 360

    # dec - declination angle [degrees]
    dec = asind(sind(ep) * sind(l))

    # gmst - Greenwich mean sidereal time [hr]
    gmst = 6.697375 + 0.0657098242 * n + hour
    # gmst has to be between 0 and 24 h
    gmst = gmst % 24

    # lmst - local mean sideral time [hr]
    lmst = gmst + longitude / 15  # to convert deg to h, divide with 15
    # lmst has to be between 0 and 24 h
    lmst = lmst % 24

    # ha - hour angle [hr]
    ha = lmst - ra / 15
    # ha has to be between -12 and 12 h
    ha = (ha + 12) % 24 - 12

    # el - solar elevation angle [degrees]
    el = asind(
        sind(dec) * sind(latitude) + cosd(dec) * cosd(latitude) * cosd(15 * ha)
    )  # to convert h to deg, multiply with 15

    # az - azimuth [degrees]
    az = asind(-cosd(dec) * sind(15 * ha) / cosd(el))

    if spencer_correction:
        # Spencer correction for the azimuth quadrant assignment
        cos_az = sind(dec) - sind(el) * sind(latitude)
        az = np.where((cos_az >= 0) & (sind(az) < 0), 360 + az, az)
        az = np.where(cos_az < 0, 180 - az, az)
    else:
        # Original Michalsky implementation does not work for all latitudes
        # calcualte critical elevation
        elc = asind(sind(dec) / sind(latitude))
        # correct azimuth using critical elevation
        az = np.where(el >= elc, 180 - az, az)
        az = np.where((el <= elc) & (ha > 0), az + 360, az)
        az = az % 360

    # refraction correction
    el = np.array(el)  # convert from Index to array
    r = refraction.michalsky(el)

    result = pd.DataFrame(
        {
            "elevation": el,
            "apparent_elevation": el + r,
            "zenith": 90 - el,
            "apparent_zenith": 90 - (el + r),
            "azimuth": az,
        },
        index=times,
    )
    return result
