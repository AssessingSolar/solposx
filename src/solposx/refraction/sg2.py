"""SG2 refraction model."""
import numpy as np


def sg2(elevation, pressure=101325., temperature=12.):
    r"""
    Atmospheric refraction correction based on the algorithm in SG2.

    This function calculates the atmospheric refraction correction of the solar
    elevation angle using the method developed by Ph. Blanc and L. Wald [1]_.

    Parameters
    ----------
    elevation : array-like
        True solar elevation angle (not accounting for refraction). [degrees]
    pressure : numeric, default 101325
        Annual average atmospheric pressure. [Pascal]
    temperature : numeric, default 12
        Annual average air temperature. [C]

    Returns
    -------
    np.array or pd.Series
        Atmospheric refraction angle. [degrees]

    Notes
    -----
    The equation to calculate the refraction correction is given by:

    .. math::

       \begin{align}
       & \frac{P}{1010} \cdot \frac{283}{273+T} \cdot \frac{2.96706 \cdot 10^{-4}}{\text{tan}(el+0.0031376 \cdot (el+0.089186)^{-1})} & \text{ for } el > -0.01 \text{ [rad]}\\
       & -\frac{P}{1010} \cdot \frac{283}{273+T} \cdot \frac{1.005516 \cdot 10^{-4}}{\text{tan}(el)} & \text{ for } el < -0.01 \text{ [rad]}
       \end{align}

    where :math:`el` is the true solar elevation angle, :math:`P` is the local
    air pressure, :math:`T` is the local air temperature.

    References
    ----------
    .. [1] Ph. Blanc and L. Wald, "The SG2 algorithm for a fast and accurate
       computation of the position of the sun for multidecadal time period,"
       Solar Energy, vol. 86, no. 10, pp. 3072-3083, 2012,
       :doi:`10.1016/j.solener.2012.07.018`
    """  # noqa: E501

    pressure = pressure / 100  # convert Pa to hPa
    elevation_rad = np.deg2rad(elevation)

    refraction = (
        2.96706 * 10**-4 /
        (np.tan(elevation_rad + 0.0031376 / (elevation_rad + 0.089186))))

    # Apply correction term of Cornwall et al. (2011)
    low_elevation_mask = elevation_rad <= -0.01
    refraction[low_elevation_mask] = (
        -1.005516*10**-4 / (np.tan(elevation_rad)))[low_elevation_mask]

    refraction = refraction * pressure / 1010 * 283 / (273 + temperature)

    return np.rad2deg(refraction)
