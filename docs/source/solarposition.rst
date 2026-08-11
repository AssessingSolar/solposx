.. currentmodule:: solposx


Solar position algorithms
=========================

Functions to compute sun positions for the specified times and
location.  All functions return solar zenith, elevation, and azimuth angles.
Algorithms that include an atmospheric refraction model also return
"apparent" (refraction-corrected) values.

.. autosummary::
   :toctree: generated/

   solarposition.iqbal
   solarposition.michalsky
   solarposition.nasa_horizons
   solarposition.noaa
   solarposition.psa
   solarposition.sg2
   solarposition.sg2_c
   solarposition.skyfield
   solarposition.spa
   solarposition.usno
   solarposition.walraven

Utility
-------

.. autosummary::
   :toctree: generated/

   solarposition.sunup_solarposition
