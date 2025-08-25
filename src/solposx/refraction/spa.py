"""SPA refraction model."""
import numpy as np


def spa(elevation, pressure=101325., temperature=12., refraction_limit=-0.5667):
    r"""
    Atmospheric refraction correction from the SPA algorithm.

    This function calculates the atmospheric refraction correction of the solar
    elevation angle using the method described in Reda and Andreas's [1]_
    Solar Position Algorithm (SPA).

    Parameters
    ----------
    elevation : array-like
        True solar elevation angle (not accounting for refraction). [degrees]
    pressure : numeric, default 101325
        Annual average local pressure. [Pa]
    temperature : numeric, default 12
        Annual average local air temperature. [C]
    refraction_limit : float, default -0.5667
        Solar elevation angle below which refraction is not applied, as the sun
        is assumed to be below horizon. Note that the sun diameter is added to
        this. [degrees]

    Returns
    -------
    np.array or pd.Series
        Atmospheric refraction angle. [degrees]

    Notes
    -----
    The equation to calculate the refraction correction is given by:

    .. math::

       ref = \frac{P}{101000} \cdot \frac{283}{273 + T} \cdot \frac{1.02}{60 \cdot \text{tan} (el + 10.3/(el + 5.11))}

    where :math:`el` is the true solar elevation angle, :math:`P` is the annual average local
    air pressure, and :math:`T` is the annual average local air temperature.

    References
    ----------
    .. [1] I. Reda and A. Andreas, "Solar Position Algorithm for Solar
       Radiation Applications (Revised)," NREL Report No. TP-560-34302, pp. 55,
       2008, :doi:`10.2172/15003974`.
    """  # noqa: E501
    pressure = pressure / 100  # convert from Pa to hPa/mbar
    # switch sets elevation when the sun is below the horizon
    above_horizon = elevation >= (-0.26667 + refraction_limit)

    refraction_correction = (
        (pressure / 1010.0) * (283.0 / (273 + temperature))
        * 1.02 / (60 * np.tan(np.radians(elevation + 10.3 /
                                         (elevation + 5.11))))) * above_horizon

    return refraction_correction
