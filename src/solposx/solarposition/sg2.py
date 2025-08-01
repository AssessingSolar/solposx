import pandas as pd
import numpy as np
from solposx.tools import _pandas_to_utc, _fractional_hour
from solposx import refraction


def sg2(times, latitude, longitude, elevation=0, air_pressure=101325, temperature=12):
    """
    Calculate solar position using the SG2 algorithm.

    The SG2 algorithm [1]_ has a stated accuracy of 0.003 degrees
    from years 1980 to 2030.

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
    elevation : float, default : 0
        Altitude of the location of interest. [m]
    air_pressure : float, default : 101325
        Annual average air pressure. [Pa]
    temperature : float, default : 12
        Annual average air temperature. [°C]

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
    The SG2 equations as described in [1]_ had a number of typos and errors.
    These errors have been corrected in the present implementation.

    See Also
    --------
    solposx.solarposition.sg2_c

    References
    ----------
    .. [1] Ph. Blanc and L. Wald, "The SG2 algorithm for a fast and accurate
       computation of the position of the sun for multidecadal time period,"
       Solar Energy, vol. 86, no. 10, pp. 3072-3083, 2012,
       :doi:`10.1016/j.solener.2012.07.018`
    """
    # convert coordinates to [rad]
    latitude = np.deg2rad(latitude)
    longitude = np.deg2rad(longitude)

    # convert time to UTC
    times_utc = _pandas_to_utc(times)

    year = times_utc.year
    month = times_utc.month
    day = times_utc.day  # this is day of month and not day of year
    hour = _fractional_hour(times_utc)

    # year in decimal form
    year_dec = year + (month - 0.5) / 12

    # parameters for calculating delta_t
    params_t = pd.DataFrame(
        np.array(
            [
                [1975, 45.45, 1.067, -1 / 260, -1 / 718, 0, 0],  # [1980, 1986]
                [
                    2000,
                    63.86,
                    0.3345,
                    -0.060374,
                    0.0017275,
                    6.518 * 10**-4,
                    2.374 * 10**-5,
                ],  # [1986, 2005]
                [2000, 63.48, 0.2040, 0.005576, 0, 0, 0],  # [2005, 2030]
            ]
        ),
        columns=["y", "a_0", "a_1", "a_2", "a_3", "a_4", "a_5"],
    )

    if (year_dec < 1980) | (year_dec > 2030):
        raise ValueError("The algorithm is valid only between 1980 and 2030")

    row = np.where(
        (year_dec >= 1980) & (year_dec <= 1986),
        0,
        np.where(
            (year_dec >= 1986) & (year_dec <= 2005),
            1,
            np.where((year_dec >= 2005) & (year_dec <= 2030), 2, np.nan),
        ),
    ).astype(int)[0]

    delta_t = 0.0
    for k in range(0, 6):
        delta_t += params_t[f"a_{k}"][row] * (year - params_t["y"][row]) ** k

    year_mod = np.where((month == 1) | (month == 2), year - 1, year)
    month_mod = np.where((month == 1) | (month == 2), month + 12, month)

    # SG2 C-code implementation (differs from journal paper!)
    jd_ut = (
        1721028.0
        + day
        + np.floor((153.0 * month_mod - 2.0) / 5.0)
        + 365.0 * year_mod
        + np.floor(year_mod / 4.0)
        + hour / 24
        - 0.5
        - np.floor(year_mod / 100.0)
        + np.floor(year_mod / 400.0)
    )

    jd_tt = jd_ut + delta_t / 86400

    jd_ut_mod = jd_ut - 2444239.5
    jd_tt_mod = jd_tt - 2444239.5

    # Earth heliocentric longitude
    params = pd.DataFrame(
        np.array(
            [
                [1 / 365.261278, 3.401508 * 10**-2, 1.600780],
                [1 / 182.632412, 3.486440 * 10**-4, 1.662976],
                [1 / 29.530634, 3.136227 * 10**-5, -1.195905],
                [1 / 399.529850, 3.578979 * 10**-5, -1.042052],
                [1 / 291.956812, 2.676185 * 10**-5, 2.012613],
                [1 / 583.598201, 2.333925 * 10**-5, -2.867714],
                [1 / 4652.629372, 1.221214 * 10**-5, 1.225038],
                [1 / 1450.236684, 1.217941 * 10**-5, -0.828601],
                [1 / 199.459709, 1.343914 * 10**-5, -3.108253],
                [1 / 365.355291, 8.499475 * 10**-4, -2.353709],
            ]
        ),
        columns=["f_L", "rho_L", "phi_L"],
    )

    # I reshape the jd and dataframe in order to do the sum operation
    jd_tt_mod_reshaped = jd_tt_mod.to_numpy().reshape(len(jd_tt_mod), 1)
    f_L = params["f_L"].to_numpy().reshape(1, 10)
    rho_L = params["rho_L"].to_numpy().reshape(1, 10)
    phi_L = params["phi_L"].to_numpy().reshape(1, 10)

    # Compute the sum term
    sums = rho_L * np.cos(2 * np.pi * f_L * jd_tt_mod_reshaped - phi_L)

    # Sum along axis 1 (the parameter axis) [rad]
    a_L = 1 / 58.130101
    b_L = 1.742145

    L = (sums.sum(axis=1) + a_L * jd_tt_mod + b_L) % (2 * np.pi)

    # Geocentric parameters
    D_t = -9.933735 * 10**-5  # [rad]
    xi = 4.263521 * 10**-5  # [rad]

    f_psi = 1 / 6791.164405
    rho_psi = 8.329092 * 10**-5
    phi_psi = -2.052757

    # Sun geocentric longitude [rad]
    D_psi = rho_psi * np.cos(2 * np.pi * f_psi * jd_tt_mod - phi_psi)

    a_e = -6.216374 * 10**-9
    b_e = 4.091383 * 10**-1
    f_e = 1 / 6791.164405
    rho_e = 4.456183 * 10**-5
    phi_e = 2.660352

    # true Earth obliquityn[rad]
    epsilon = (
        rho_e * np.cos(2 * np.pi * f_e * jd_tt_mod - phi_e) + a_e * jd_tt_mod + b_e
    )

    # Apparent Sun geocentric longitude [rad]
    Theta = (L + np.pi + D_psi + D_t) % (2 * np.pi)

    # Sun Geocentric declination [rad]
    decl_g = np.arcsin(np.sin(Theta) * np.sin(epsilon))

    # Sun Geocentric right ascension [rad]
    ra = np.arctan2(np.sin(Theta) * np.cos(epsilon), np.cos(Theta))

    # mean sidereal time [rad]
    mst = (6.300388099 * jd_ut_mod + 1.742079) % (2 * np.pi)

    a = 6378140.0  # m
    # b = 6357014.436696  # m
    f = 1 / 298.257282697

    u = np.arctan((1 - f) * np.tan(latitude))
    x = np.cos(u) + elevation / a * np.cos(latitude)
    y = (1 - f) * np.sin(u) + elevation / a * np.sin(latitude)

    # omega_g is the geocentric hour angle
    # no formula is given in the paper to calcualte this
    # using the formulas from Reda and Andreas publication

    # apparent sidereal time at Greenwich [rad]
    v = mst + D_psi * np.cos(epsilon)

    # geocentric hour angle [rad]
    omega_g = v + longitude - ra

    # Parallax effects in the Sun right ascension [rad]
    D_r_a = -x * np.sin(omega_g) / np.cos(decl_g) * xi

    # Sun topocentric declination [rad]
    declination = (
        decl_g + (x * np.cos(omega_g) * np.sin(decl_g) - y * np.cos(decl_g)) * xi
    )

    # Sun topocentric hour angle [rad]
    omega = mst + D_psi * np.cos(epsilon) - ra + longitude - D_r_a

    # Sun topocentric azimuth [rad]
    azimuth = (
        np.arctan2(
            np.sin(omega),
            np.cos(omega) * np.sin(latitude) - np.tan(declination) * np.cos(latitude),
        )
        + np.pi
    )

    # Sun topocentric elevation angle without refraction correction [rad]
    elevation = np.arcsin(
        np.sin(latitude) * np.sin(declination)
        + np.cos(latitude) * np.cos(declination) * np.cos(omega)
    )

    elevation_deg = np.rad2deg(elevation)

    # Atmospheric refraction correction term
    r = refraction.sg2(np.array(elevation_deg), air_pressure, temperature)

    result = pd.DataFrame(
        {
            "elevation": elevation_deg,
            "apparent_elevation": elevation_deg + r,
            "zenith": 90 - elevation_deg,
            "apparent_zenith": 90 - elevation_deg - r,
            "azimuth": np.rad2deg(azimuth),
        },
        index=times,
    )
    return result


def sg2_c(times, latitude, longitude, elevation=0, air_pressure=101325, temperature=12):
    """
    Calculate solar position using the SG2 Python package.

    This function uses the SG2 Python package [1]_, which wraps the
    official C-code.

    The SG2 algorithm [2]_ has a stated accuracy of 0.003 degrees
    from years 1980 to 2030.


    Parameters
    ----------
    times : pandas.DatetimeIndex
        Must be localized.
    latitude : float
        Latitude in decimal degrees. Positive north of equator, negative
        to south. [degrees]
    longitude : float
        Longitude in decimal degrees. Positive east of prime meridian,
        negative to west. [degrees]
    elevation : float, default : 0
        Altitude of the location of interest. [m]
    air_pressure : float, default : 101325
        Annual average air pressure. [Pa]
    temperature : float, default : 12
        Annual average air temperature. [°C]

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

    See Also
    --------
    solposx.solarposition.sg2

    References
    ----------
    .. [1] https://pypi.org/project/sg2/
    .. [2] Ph. Blanc and L. Wald, "The SG2 algorithm for a fast and accurate
       computation of the position of the sun for multidecadal time period,"
       Solar Energy, vol. 86, no. 10, pp. 3072-3083, 2012,
       :doi:`10.1016/j.solener.2012.07.018`
    """
    try:
        # Try loading optional package
        import sg2 as sg2_package
    except ImportError:  # pragma: no cover
        # Raise an error if package is not available
        raise ImportError(
            "The sg2_c function requires the sg2 Python package."
        )  # pragma: no cover

    # list of geopoints as 2D array of (N,3) where each row is repectively
    # longitude in degrees, latitude in degrees and altitude in meters.
    geopoints = np.vstack([longitude, latitude, elevation]).T

    fields = ["topoc.alpha_S", "topoc.gamma_S0", "geoc.epsilon"]

    ret = sg2_package.sun_position(
        geopoints,
        times.values,
        fields,
    )
    elevation_rad = ret.topoc.gamma_S0[0]
    elevation_deg = np.rad2deg(elevation_rad)

    apparent_elevation_rad = sg2_package.topocentric_correction_refraction_SAE(
        elevation_rad,
        air_pressure / 100,
        temperature,
    )

    out = pd.DataFrame(
        {
            "elevation": elevation_deg,
            "apparent_elevation": np.rad2deg(apparent_elevation_rad),
            "zenith": 90 - elevation_deg,
            "apparent_zenith": 90 - np.rad2deg(apparent_elevation_rad),
            "azimuth": np.degrees(ret.topoc.alpha_S[0]),
        },
        index=times,
    )

    return out
