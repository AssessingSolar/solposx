import pandas as pd
import numpy as np
from solposx.tools import _pandas_to_utc, _fractional_hour


def walraven(times, latitude, longitude):
    """
    Calculate solar position using the Walraven algorithm.

    Walraven's algorithm [1]_ has a stated accuracy of 0.01 degrees. The
    implementation accounts for the 1979 Erratum [2]_ and the correct
    azimuth quadrant selection [3]_.

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
    .. [1] R. Walraven, “Calculating the position of the sun,” Solar Energy,
       vol. 20, no. 5, pp. 393–397, 1978, :doi:`10.1016/0038-092x(78)90155-x`.
    .. [2] R. Walraven, "Erratum," Solar Energy,
       vol. 22, pp. 195, 1979, :doi:`10.1016/0038-092X(79)90106-3`
    .. [3] J. W. Spencer, “Comments on The Astronomical Almanac’s Algorithm for
       Approximate Solar Position (1950–2050),” Solar Energy, vol. 42, no. 4,
       pp. 353, 1989, :doi:`10.1016/0038-092x(89)90039-x`.
    """
    times_utc = _pandas_to_utc(times)

    longitude = -longitude  # outdated convention used by Walraven

    year = times_utc.year
    day = times_utc.dayofyear
    T = _fractional_hour(times_utc)

    delta = year - 1980

    leap = np.int64(delta / 4.0)  # round towards zero

    time = delta * 365 + leap + day - 1 + T / 24

    time = np.where(delta == (leap * 4), time - 1, time)

    time = np.where((delta < 0) & (delta != (leap * 4)), time - 1, time)

    # [rad]
    theta = 2 * np.pi * time / 365.25

    # [rad]
    g = -0.031271 - 4.53963 * 10**-7 * time + theta

    # longitude of the sun [rad]
    L = (
        4.900968
        + (3.67474 * 10**-7) * time
        + (0.033434 - 2.3 * 10**-9 * time) * np.sin(g)
        + 0.000349 * np.sin(2 * g)
        + theta
    )

    # angle between the plane of the ecliptic and the plane of the
    # celestial equator [rad]
    epsilon = np.deg2rad(23.4420) - np.deg2rad(3.56 * 10**-7) * time

    SEL = np.sin(L)

    A1 = SEL * np.cos(epsilon)

    A2 = np.cos(L)

    # right angle [rad]
    RA = np.arctan2(A1, A2)
    RA = np.where(RA < 0, RA + 2 * np.pi, RA)

    # declination [rad]
    DECL = np.arcsin(SEL * np.sin(epsilon))

    # sidereal time [rad]
    ST = 1.759335 + 2 * np.pi * (time / 365.25 - delta) + 3.694 * 10**-7 * time
    ST = np.where(ST >= (2 * np.pi), ST - 2 * np.pi, ST)

    # local sidereal time [rad]
    S = ST - np.deg2rad(longitude) + np.deg2rad(T * 15)
    S = np.where(S >= (2 * np.pi), S - 2 * np.pi, S)

    # hour angle [rad]
    H = RA - S

    # latitude in [rad]
    PHI = np.deg2rad(latitude)

    # elevation [rad]
    E = np.arcsin(np.sin(PHI) * np.sin(DECL) + np.cos(PHI) * np.cos(DECL) * np.cos(H))

    # azimuth [deg]
    A = np.rad2deg(np.arcsin(np.cos(DECL) * np.sin(H) / np.cos(E)))

    # azimuth quadrant assignment - Spencer (1989) correct for all longitudes
    cos_az = np.sin(DECL) - np.sin(E) * np.sin(PHI)
    A = np.where((cos_az >= 0) & (np.sin(np.deg2rad(A)) < 0), 360 + A, A)
    A = np.where(cos_az < 0, 180 - A, A)

    result = pd.DataFrame(
        {
            "elevation": np.rad2deg(E),
            "zenith": 90 - np.rad2deg(E),
            "azimuth": A,
        },
        index=times,
    )
    return result
