---
title: 'solposx: A Python package for determining solar position and atmospheric refraction'
tags:
  - Python
  - solar energy
  - photovoltaics
  - solar position
authors:
  - name: Adam R. Jensen
    corresponding: true
    orcid: 0000-0002-5554-9856
    equal-contrib: true
    affiliation: 1
  - name: Ioannis Sifnaios
    orcid: 0000-0003-0933-2952
    equal-contrib: true
    affiliation: 1
  - name: Kevin S. Anderson
    orcid: 0000-0002-1166-7957
    equal-contrib: true
    affiliation: 2
affiliations:
  - name: Technical University of Denmark (DTU), Denmark
    index: 1
    ror: 04qtj9h94
  - name: Sandia National Laboratories, USA
    index: 2
    ror: 01apwpt12
date: 13 August 2025
bibliography: paper.bib
---

# Summary
`solposx` is a Python package of reference algorithms for calculating the sun’s position and atmospheric refraction. The package includes 11 solar position algorithms and 6 refraction models from the past 50 years. All functions follow a standardized design pattern, making it easy to compare different algorithms. The provided algorithm implementations have been thoroughly vetted, making the package a valuable research tool and a reliable reference for implementing solar position algorithms in other programming languages or applications.


# Statement of need

Calculating the sun's position is a fundamental task in solar energy research, for example, when modeling solar irradiance, estimating the yield of photovoltaic (PV) systems, or determining rotation angles for solar trackers. For this reason, the literature contains numerous solar position algorithms (SPAs), some of which are: [@spencer1971; @walraven1978; @michalsky1988; @reda2004; @blanco2020].

Existing SPAs vary in accuracy, computational speed, and period of validity. These characteristics are usually tradeoffs, and thus the choice of algorithm depends on the specific application. Some algorithms have been developed to be computationally lightweight for use in solar tracker microcontrollers, and as a tradeoff, are inaccurate for past and future years. In contrast, high-accuracy algorithms may consist of several hundred mathematical operations to retain validity for hundreds or even thousands of years. One example of such an algorithm is the SPA from NREL, whose high accuracy and extensive period of validity come at the cost of being computationally expensive and impractical for non-experts to implement.

Solar position algorithms are already available in several open source software packages, such as the PV modeling software packages pvlib-python [@anderson2023] and pysolar [@stafford2025], the astronomy packages pyephem [@rhodes2011] and skyfield [@rhodes2019], and the sun physics package sunpy [@sunpy2020]. These packages are tailored to very specific purposes and only contain one or a few solar position algorithms. Consequently, there are many solar position algorithms for which open source reference implementation is not available. This makes it difficult to evaluate the tradeoffs of the various solar position algorithms, which is necessary in order to make informed decisions on which algorithm to choose for a specific application.

**Sol**ar**Pos**ition**X** (`solposx`) is a Python package for calculating solar position angles and atmospheric refraction corrections. The package provides reference implementations of a large number of solar position and refraction correction algorithms spanning 50 years of the scientific literature. The SPAs range from simple algorithms based on fitted equations to research-grade astronomy algorithms based on complex ephemerides. As of solposx version v1.0.0, the package includes 11 different solar position algorithms and 6 algorithms for estimating atmospheric refraction. The "X" in solposx refers to the modular design of the package, allowing users to seamlessly switch between a variety of algorithms depending on their desired needs. An overview of the modules and functions is provided in \autoref{fig:package}.

The solar position functions follow a standard pattern, taking three main input parameters (times, latitude, and longitude) and returning a pandas DataFrame with solar elevation, zenith, and azimuth angles. This makes it extremely easy to compare and switch between SPAs, regardless of whether the functions execute code from within the solposx package, rely on external Python packages (which is the case for the skyfield and sg2 functions), or retrieve data remotely (which is the case for NASA's Horizons service [@nasa2025]). The refraction correction models also follow a standardized pattern where the main input is an array or series of solar elevation angles and the output is the atmospheric refraction correction angle.

![Overview of modules and functions in the solposx package.\label{fig:package}](solposx_package_structure.png)

The package relies heavily on the pandas Python package [@mckinney2010], due to its convenient DatetimeIndex class. The reason for this choice is that it offers a very convenient way to handle timestamps, including timezone information and conversion between timezones. The refraction correction algorithms are not reliant on pandas and can be used with most Python array libraries.

Besides direct applications of calculating solar position, one of the main use cases of the package is providing verified reference implementations to users who are implementing algorithms in other languages or applications. Access to verified reference implementations is an essential tool as solar position algorithms tend to be sensitive to small implementation details. For example, a small detail such as using an incorrect rounding convention, e.g., rounding towards zero vs. rounding down, can result in solar position angles being off by more than 0.1 degrees, an error much larger than the claimed accuracy of most SPAs. Such subtle but serious implementation errors are, in the authors’ experience, almost inevitable when implementing SPAs, creating a need for correct and accessible reference implementations. With access to vetted and tested reference implementations of these SPAs, users can generate reliable test values for validating and debugging their own implementations. Notably, the solposx package has already been used for research purposes, most recently in a study comparing the performance of solar position algorithms for PV applications [@jensen2025].

`solposx` is developed openly on GitHub and released under a BSD 3-clause license, allowing permissive use with attribution. The package is extensively tested, ensuring that the algorithms work for a large range of inputs and remain consistent. In general, solposx has been developed following modern best practices for packaging, documentation, and testing. Additional algorithms are expected to be added as new algorithms are developed or if additional historical algorithms of interest are identified.


# References
