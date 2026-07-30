Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.


1.0.2 - upcoming
----------------

Changed
^^^^^^^
* matplotlib is now an optional ``doc`` dependency instead of a required
  dependency. (:pull:`146`)
* Add support for correctly handling sub-second timestamp resolution in
  :py:func:`solposx.solarposition.usno`. (:issue:`156`, :pull:`157`)

Added
^^^^^
* Add testing for Python 3.14. (:pull:`144`)

Testing
^^^^^^^
* The test values for the skyfield solar position function were updated to
  match skyfield version 1.54. (:issue:`148`, :pull:`150`)

1.0.1 - 2025-11-09
-------------------

Changed
^^^^^^^
* Moved the package GitHub repository from the GitHub organization AssessingSolar
  to the pvlib organization. (:pull:`134`)
* Improved error messages raised when optional packages are not available.
  (:issue:`86`, :pull:`122`)

Added
^^^^^
* Added optional ``refraction_correction`` parameter to
  :py:func:`solposx.solarposition.nasa_horizons`. (:issue:`83`, :pull:`133`)

1.0.0 - 2025-09-22
-------------------
First stable release.
