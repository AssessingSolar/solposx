"""Calculate solar position using Skyfield."""

import pandas as pd


def skyfield(times, latitude, longitude, de='de440.bsp'):
    """
    Calculate solar position using the Skyfield Python package.

    Skyfield is a Python package [1]_, [2]_ that can calculate high precision
    position of stars, planets, and satellites in orbit around the Earth based
    on ephemerides. Calculated positions should agree with the Astronomical
    Almanac to within 0.0005 arcseconds.

    Parameters
    ----------
    times : pandas.DatetimeIndex
        Timestamps - must be localized. Prior to 1970 and far in
        the future UTC and UT1 may deviate significantly. For such use
        cases,  UT1 times should be provided.
    latitude : float
        Latitude in decimal degrees. Positive north of equator, negative
        to south. [degrees]
    longitude : float
        Longitude in decimal degrees. Positive east of prime meridian,
        negative to west. [degrees]
    de : str or Skyfield SpiceKernel, optional, default : 'de440.bsp'
        Ephemeris of choice.

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
        from skyfield.api import load, wgs84
    except ImportError:  # pragma: no cover
        # Raise an error if package is not available
        raise ImportError(
            'The skyfield function requires the skyfield Python package.'
            )  # pragma: no cover

    if isinstance(de, str):
        de = load(de)

    TS = load.timescale()

    earth = de['Earth']
    sun = de['Sun']

    dts = TS.from_datetimes(times.to_pydatetime())
    location = earth + wgs84.latlon(latitude, longitude)
    alt, az, _ = location.at(dts).observe(sun).apparent().altaz()

    result = pd.DataFrame({
        'elevation': alt.degrees,
        'zenith': 90 - alt.degrees,
        'azimuth': az.degrees,
    }, index=times)

    return result
