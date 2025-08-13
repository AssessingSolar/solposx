"""Archer refraction correction method."""
from pvlib.tools import cosd, acosd


def archer(elevation):
    r"""
    Atmospheric refraction correction based on the Archer algorithm.

    This function calculates the atmospheric refraction correction of the solar
    elevation angle using the method described in Archer [1]_. The method was
    originally developed to be used with the Walraven solar position algorithm
    [2]_.

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

        \begin{align}
        & C = \text{cos}(Z) + 0.0083 \cdot \left(\frac{1}{0.955 + (20.267 \cdot \text{cos}(Z))} - 0.047121 \right)\\
        & Z_a = \text{arccos}(C)\\
        & refraction = Z - Z_a\\
        \end{align}

    where :math:`Z` is the true solar zenith angle and :math:`Z_a` is the
    aparent zenith angle.

    References
    ----------
    .. [1] C. B. Archer, "Comments on 'Calculating the position of the sun',"
       Solar Energy, vol. 25, Issue 1, pp. 91, 1980,
       :doi:`10.1016/0038-092X(80)90410-7`.
    .. [2] R. Walraven, "Calculating the position of the sun," Solar Energy,
       vol. 20, no. 5, pp. 393-397, 1978, :doi:`10.1016/0038-092X(78)90155-X`.
    """  # noqa: E501

    zenith = 90 - elevation
    C1 = cosd(zenith)
    D = 1 / (0.955 + (20.267 * C1)) - 0.047121
    C = C1 + 0.0083 * D
    apparent_zenith = acosd(C)
    refraction_correction = zenith - apparent_zenith

    return refraction_correction
