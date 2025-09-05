import requests
import pandas as pd
import io

URL = 'https://ssd.jpl.nasa.gov/api/horizons.api'


def nasa_horizons(latitude, longitude, start, end, elevation=0.,
                  time_step='1h', url=URL):
    """
    Retrieve solar positions from NASA's Horizons web service.

    The NASA Horizons [1]_ is an online solar system data and ephemeris
    computation service, which among other things can provide highly
    accurate calculations of sun positions.

    The NASA Horizons API is described in [2]_.

    Parameters
    ----------
    latitude : float
        Latitude in decimal degrees. Positive north of equator, negative
        to south. [degrees]
    longitude : float
        Longitude in decimal degrees. Positive east of prime meridian,
        negative to west. [degrees]
    start : datetime-like
        Start of the requested time period.
    end : datetime-like
        End of the requested time period.
    elevation : float, optional
        Elevation of the point of interest [m]. The default is 0 m.
    time_step : str, optional
        Time step size of the requested time series. '1m' for minutes,
        '1h' for hours, '1d' for days, '1mo' for months, and '1y' for years.
        The default is '1h'.
    url : str, optional
        API endpoint. The default is
        ``'https://ssd.jpl.nasa.gov/api/horizons.api'``.

    Returns
    -------
    pandas.DataFrame
        DataFrame with the following columns (all values in degrees):

        - uncertainty_right_ascension
        - uncertainty_declination
        - right_ascension
        - declination
        - apparent_right_ascesion
        - apparent_declination
        - apparent_azimuth
        - apparent_elevation

    References
    ----------
    .. [1] `NASA Horizons Systems
       <https://ssd.jpl.nasa.gov/horizons/>`_
    .. [2] `NASA Horizons API
       <https://ssd-api.jpl.nasa.gov/doc/horizons.html>`_
    """
    params = {
        "MAKE_EPHEM": "YES",  # generate ephemeris
        "COMMAND": "10",  # the sun
        "EPHEM_TYPE": "OBSERVER",  # telescope observations
        "CENTER": "coord@399",  # input coordinates for Earth (399)
        "COORD_TYPE": "GEODETIC",  # latitude, longitude, elevation in degrees
        "SITE_COORD": f"{longitude},{latitude},{elevation/1000}",
        "START_TIME": pd.Timestamp(start).strftime('%Y-%m-%d %H:%M'),
        "STOP_TIME": pd.Timestamp(end).strftime('%Y-%m-%d %H:%M'),
        "STEP_SIZE": time_step,
        "QUANTITIES": "2,4",  # corrected angles
        "REF_SYSTEM": "ICRF",
        "CAL_FORMAT": "CAL",  # output date format
        "CAL_TYPE": "MIXED",  # Gregorian or mixed Julian/Gregorian calendar
        "TIME_DIGITS": "FRACSEC",  # output time precision
        "ANG_FORMAT": "DEG",  # output angles in degrees
        "APPARENT": "AIRLESS",  # no refraction
        # "RANGE_UNITS": "AU",
        # "SUPPRESS_RANGE_RATE": "NO",
        "SKIP_DAYLT": "NO",  # include daylight periods
        "SOLAR_ELONG": "0,180",
        "EXTRA_PREC": "NO",  # toggle additional digits on some angles (RA/DEC)
        "CSV_FORMAT": "NO",
        "OBJ_DATA": "NO"  # whether to return summary data
    }

    # manual formatting of the url as all parameters except format shall be
    # in enclosed in single quotes
    url_formatted = (
        url
        + '?'
        + "format=text&"
        + '&'.join([f"{k}='{v}'" for k, v in params.items()])
    )

    res = requests.get(url_formatted)

    fbuf = io.StringIO(res.content.decode())

    lines = fbuf.readlines()
    first_line = lines.index('$$SOE\n') + 1
    last_line = lines.index('$$EOE\n', first_line)
    header_line = lines[first_line - 3]
    data_str = [header_line] + lines[first_line: last_line]

    data = pd.read_fwf(io.StringIO('\n'.join(data_str)),
                       index_col=[0], na_values=['n.a.'])
    data.index = pd.to_datetime(data.index, format='%Y-%b-%d %H:%M:%S.%f')
    data.index = data.index.tz_localize('UTC')

    # split columns as several params have a shared header name for two params
    column_name_split_map = {
        'R.A._(a-appar)_DEC.': ['right_ascension', 'declination'],
        'Azi____(a-app)___Elev': ['azimuth', 'elevation'],
    }

    for old_name, new_names in column_name_split_map.items():
        data[new_names] = \
            data[old_name].str.split(r'\s+', expand=True).astype(float)

    data = data.drop(columns=list(column_name_split_map.keys()))

    data.index.name = 'time'
    try:
        del data['Unnamed: 1']
    except KeyError:
        pass

    return data
