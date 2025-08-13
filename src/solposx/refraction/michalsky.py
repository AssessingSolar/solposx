"""Michalsky refraction model."""


def michalsky(elevation):
    r"""
    Atmospheric refraction correction based on the Michalsky algorithm.

    This function calculates the atmospheric refraction correction of the solar
    elevation angle using the method described in Michalsky [1]_.

    Parameters
    ----------
    elevation : array-like
        True solar elevation angle (not accounting for refraction). [degrees]

    Returns
    -------
    np.array or pd.Series
        Atmospheric refraction angle. [degrees]

    Notes
    -----
    The equation to calculate the refraction correction is given by:

    .. math::

        ref = \frac{3.51561 \cdot (0.1594 + 0.0196 \cdot el + 0.00002 \cdot el^2)}{1 + 0.505 \cdot el + 0.0845 \cdot el^2}

    where :math:`el` is the true (uncorrected) solar elevation angle.

    References
    ----------
    .. [1] J. J. Michalsky, "The Astronomical Almanac's algorithm for
       approximate solar position (1950–2050)," Solar Energy, vol. 40, no. 3,
       pp. 227–235, 1988, :doi:`10.1016/0038-092x(88)90045-x`.
    """  # noqa: E501
    # note that 3.51561 = 1013.2 mb / 288.2 deg C
    refraction_correction = (
        3.51561 * (0.1594 + 0.0196 * elevation + 0.00002 * elevation**2) /
        (1 + 0.505 * elevation + 0.0845 * elevation**2))

    refraction_correction[elevation < -0.56] = 0.56

    return refraction_correction
