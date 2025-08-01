import pandas as pd
from pvlib.tools import sind, cosd, tand, asind
import numpy as np
from pvlib import spa
from solposx.tools import _pandas_to_utc


def usno(times, latitude, longitude, delta_t=67.0, gmst_option=1):
    """
    Calculate solar position using the USNO algorithm.

    The U.S. Naval Observatory (USNO) algorithm is provided in [1]_.

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
        The USNO has historical and forecasted delta_t [2]_. [seconds]
    gmst_option : int, default 1
        Different ways of calculating the Greenwich mean sidereal time.
        `gmst_option` needs to be either 1, 2, or 3. See [1]_.

    Returns
    -------
    pandas.DataFrame
        DataFrame with the following columns (all values in degrees):

        - elevation : actual sun elevation (not accounting for refraction).
        - zenith : actual sun zenith (not accounting for refraction).
        - azimuth : sun azimuth, east of north.

    References
    ----------
    .. [1] USNO Computing Altitude and Azimuth from Greenwich Apparent Sidereal
       Time: https://aa.usno.navy.mil/faq/alt_az
    .. [2] USNO delta T:
       https://maia.usno.navy.mil/products/deltaT
    """
    times_utc = _pandas_to_utc(times)

    if delta_t is None:
        delta_t = spa.calculate_deltat(times_utc.year, times_utc.month)

    JD = times_utc.to_julian_date()

    D = JD - 2451545.0

    # Mean anomaly of the Sun [deg]
    g = 357.529 + 0.98560028 * D
    # ensure g is between 0 and 360
    g = g % 360

    # Mean longitude of the Sun [deg]
    q = 280.459 + 0.98564736 * D
    # ensure q is between 0 and 360
    q = q % 360

    # Geocentric apparent ecliptic longitude of the Sun
    # (adjusted for aberration) [deg]
    L = q + 1.915 * sind(g) + 0.020 * sind(2 * g)
    # ensure L is between 0 and 360
    L = L % 360

    # Mean obliquity of the ecliptic [deg]
    e = 23.439 - 0.00000036 * D

    # Sun's right ascension angle [hours]
    RA = np.rad2deg(np.arctan2(cosd(e) * sind(L), cosd(L))) / 15
    RA = RA % 24

    # Sun's declination angle [deg]
    d = asind(sind(e) * sind(L))

    # JD_0 is the Julian date of the previous midnight (0h) UT1
    midnight = pd.DatetimeIndex(
        [t.replace(hour=0, minute=0, second=0) for t in times_utc]
    )

    JD_0 = midnight.to_julian_date()

    # Hours of UT1 elapsed since the previous midnight
    H = (JD - JD_0) * 24

    DAY_UT = JD_0 - 2451545.0

    JD_TT = JD + delta_t / 86400.0

    D_TT = JD_TT - 2451545.0

    T = D_TT / 36525  # centuries since the year 2000

    # Greenwich mean sidereal time [hours]
    if gmst_option == 1:
        GMST = (
            6.697375
            + 0.065707485828 * DAY_UT
            + 1.0027379 * H
            + 0.0854103 * T
            + 0.0000258 * T**2
        )
    elif gmst_option == 2:
        GMST = 6.697375 + 0.065709824279 * DAY_UT + 1.0027379 * H + 0.0000258 * T**2
    elif gmst_option == 3:
        GMST = 18.697375 + 24.065709824279 * DAY_UT
    else:
        raise ValueError(f"{gmst_option} is not a valid `gmst_option`")

    GMST = GMST % 24

    # Longitude of the ascending node of the Moon [deg]
    omega = 125.04 - 0.052954 * D_TT

    # Mean Longitude of the Sun [deg]
    LS = 280.47 + 0.98565 * D_TT

    # Nutation in longitude [hours]
    longitude_nutation = -0.000319 * sind(omega) - 0.000024 * sind(2 * LS)

    # obliquity of the ecliptic
    epsilon = 23.4393 - 0.0000004 * D_TT

    # equation of equinoxes [hours]
    eqeq = longitude_nutation * cosd(epsilon)

    # Greenwich apparent sidereal time [hours]
    GAST = GMST + eqeq

    # Local hour angle [deg], logitude is positive if it is east
    LHA = (GAST - RA) * 15 + longitude

    # solar elevation [deg]
    elevation = asind(cosd(LHA) * cosd(d) * cosd(latitude) + sind(d) * sind(latitude))

    # azimuth [deg]
    azimuth = np.rad2deg(
        np.arctan2(-sind(LHA), (tand(d) * cosd(latitude) - sind(latitude) * cosd(LHA)))
    )
    azimuth = azimuth % 360

    result = pd.DataFrame(
        {
            "elevation": elevation,
            "zenith": 90 - elevation,
            "azimuth": azimuth,
        },
        index=times,
    )
    return result
