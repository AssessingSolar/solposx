"""Hughes refraction model."""
import numpy as np


def hughes(elevation, pressure=101325., temperature=12.):
    r"""
    Atmospheric refraction correction based on the Hughes algorithm.

    This function was developed by G. Hughes [1]_ and was used in the SUNAEP
    software [2]_.

    It is also used to calculate the refraction correction in the NOAA
    solar position algorithm using a fixed pressure of 101325 Pa and
    a temperature of 10 degrees Celsius.

    Parameters
    ----------
    elevation : array-like
        True solar elevation angle (not accounting for refraction). [degrees]
    pressure : numeric, default 101325
        Annual average atmospheric pressure. [Pascal]
    temperature : numeric, default 12
        Annual average temperature. The default in this code deviates from
        [1]_, which used 10 C. [C]

    Returns
    -------
    np.array or pd.Series
        Atmospheric refraction angle. [degrees]

    Notes
    -----
    The equation to calculate the refraction correction is given by:

    .. math::

        \begin{align}
        5° < el \le 90° &: \quad \frac{58.1}{\text{tan}(el)} - \frac{0.07}{\text{tan}(el)^3} + \frac{8.6\cdot 10^{-5}}{\tan(el)^5}\\
        -0.575° < el \le 5° &: \quad el \cdot (-518.2 + el \cdot (103.4 + el \cdot (-12.79 + el \cdot 0.711))) + 1735\\
        el \le -0.575° &: \quad \frac{-20.774}{\text{tan}(el)}\\
        \end{align}

    where :math:`el` is the true (unrefracted) solar elevation angle.

    References
    ----------
    .. [1] `G. W. Hughes, "Engineering Astronomy,"
       Sandia Laboratories, 1985,
       <https://pvpmc.sandia.gov/app/uploads/sites/243/2022/10/Engineering-Astronomy.pdf>`_
    .. [2] J. C. Zimmerman, "Sun-pointing programs and their accuracy,"
       SANDIA Technical Report SAND-81-0761, 1981, :doi:`10.2172/6377969`.
    """  # noqa: E501
    TanEl = np.tan(np.radians(elevation))

    Refract = 58.1/TanEl - 0.070/(TanEl**3) + 8.6e-05/(TanEl**5)

    low_elevation_mask = (elevation > -0.575) & (elevation <= 5)
    Refract[low_elevation_mask] = (
        elevation *
        (-518.2 + elevation*(103.4 + elevation*(-12.79 + elevation*0.711))) +
        1735)[low_elevation_mask]

    negative_elevation_mask = elevation <= -0.575
    Refract[negative_elevation_mask] = (-20.774 / TanEl)[negative_elevation_mask]

    # Correct for temperature and pressure and convert to degrees
    Refract *= (283/(273. + temperature)) * (pressure/101325.) / 3600.

    return Refract
