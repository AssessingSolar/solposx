"""Calculate solar position using Skyfield."""

import pandas as pd

try:
    # Try loading optional package
    from skyfield.api import load

    DE440 = load("de440.bsp")
    TS = load.timescale()
except ImportError:  # pragma: no cover
    pass  # pragma: no cover


def skyfield(times, latitude, longitude, de=None):
    """
    Calculate solar position using the Skyfield Python package.

    Skyfield is a Python package that can calculate high precision
    position of stars, planets, and satellites in orbit around the Earth based
    on epherides. Calculated positions should agree with the Astronomical
    Almanac to within 0.0005 arcseconds.

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
    de : Skyfield SpiceKernel, optional, default DE440
        Empheris of choice.

    Returns
    -------
    pandas.DataFrame
        DataFrame with the following columns (all values in degrees):

        - elevation : actual sun elevation (not accounting for refraction).
        - zenith : actual sun zenith (not accounting for refraction).
        - azimuth : sun azimuth, east of north.

    References
    ----------
    .. [1] Skyfield website
       https://rhodesmill.org/skyfield/
    .. [2] Skyfield GitHub repository
       https://github.com/skyfielders/python-skyfield
    """
    try:
        # Try loading optional package
        from skyfield.api import wgs84
    except ImportError:  # pragma: no cover
        # Raise an error if package is not available
        raise ImportError(
            "The skyfield function requires the skyfield Python package."
        )  # pragma: no cover

    if de is None:
        de = DE440

    earth = de["Earth"]
    sun = de["Sun"]

    dts = TS.from_datetimes(times.to_pydatetime())
    location = earth + wgs84.latlon(latitude, longitude)
    alt, az, _ = location.at(dts).observe(sun).apparent().altaz()

    result = pd.DataFrame(
        {
            "elevation": alt.degrees,
            "zenith": 90 - alt.degrees,
            "azimuth": az.degrees,
        },
        index=times,
    )

    return result
