import numpy as np
import pandas as pd


def sunup_solarposition(
    times,
    latitude,
    longitude,
    solar_position_func=None,
    *,
    sub_intervals="1min",
    side="left",
    agg_func="mean",
    **kwargs,
):
    """
    Calculate solar position for coarse time intervals, aggregating only
    over sub-intervals where the sun is above the horizon.

    For each interval in ``times``, the solar position is calculated at a
    finer temporal resolution (``sub_intervals``), and then aggregated only
    over the sub-intervals where the sun is above the horizon
    (elevation > 0). This avoids the issue where the midpoint of a coarse
    interval (e.g. one hour) falls below the horizon during sunrise or
    sunset, even though part of the interval has daylight.

    Parameters
    ----------
    times : pandas.DatetimeIndex
        Coarse timestamps (e.g., hourly). Must have a uniform, inferrable
        frequency. Most solar position functions require timezone-aware
        timestamps.
    latitude : float
        Latitude in decimal degrees. Positive north of equator. [degrees]
    longitude : float
        Longitude in decimal degrees. Positive east of prime meridian. [degrees]
    solar_position_func : callable, optional, default ``michalsky``
        A solar position function, e.g. ``solposx.solarposition.spa``.
        Must accept ``(times, latitude, longitude, **kwargs)`` and return a
        ``pandas.DataFrame`` with at least an ``'elevation'`` and an
        ``'azimuth'`` column.
    sub_intervals : str or pandas offset alias, optional, default ``'1min'``
        Time resolution for sub-sampling within each coarse interval.
    side : ``'left'`` or ``'right'``, optional, default ``'left'``
        Which boundary of each interval is closed. ``'left'`` means each
        interval is ``[t - freq/2, t + freq/2)``, ``'right'`` means
        ``(t - freq/2, t + freq/2]``.
    agg_func : str or callable, optional, default ``'mean'``
        Aggregation function applied to the sub-interval solar positions.
        Any value accepted by ``pandas.Resample.agg`` is valid, e.g.
        ``'mean'``, ``'median'``, or a custom callable.
    **kwargs
        Additional keyword arguments forwarded to ``solar_position_func``.

    Raises
    ------
    ValueError
        If ``times`` is not uniformly spaced at the inferred frequency.

    Returns
    -------
    pandas.DataFrame
        Solar position with the same index as ``times`` and the same columns
        as returned by ``solar_position_func``. For intervals where the sun
        is entirely below the horizon, all column values are ``NaN``.

    Notes
    -----
    Azimuth is aggregated via a circular approach,
    ``arctan2(agg(sin(azimuth)), agg(cos(azimuth)))``, which avoids
    the discontinuity at 0°/360°.

    Examples
    --------
    >>> import pandas as pd
    >>> import solposx
    >>> times = pd.date_range("2020-01-14 04:30", freq="1h", periods=16, tz="UTC")
    >>> standard = solposx.solarposition.michalsky(
    ...     times, latitude=55.0, longitude=11.0)
    >>> adjusted = solposx.solarposition.sunup_solarposition(
    ...     times, latitude=55.0, longitude=11.0)
    >>> # Plot elevation to illustrate differences
    >>> standard['elevation'].plot(style='-o')
    >>> adjusted['elevation'].plot(style='-o')
    """
    if solar_position_func is None:
        from solposx.solarposition.michalsky import michalsky
        solar_position_func = michalsky

    freq = times.freq
    if freq is None:
        freq = pd.tseries.frequencies.to_offset(pd.infer_freq(times))
    times.freq = freq
    if not times.equals(pd.date_range(start=times[0], end=times[-1], freq=freq, inclusive='both')):
        raise ValueError("Input ``times`` has non-uniformly spaced or "
                         "missing time stamps.")

    sub_offset = pd.tseries.frequencies.to_offset(sub_intervals)

    # Fine-resolution timestamps covering all coarse intervals:
    # [times[0] - freq/2, times[-1] + freq/2), stepped by sub_intervals.
    fine_times = pd.date_range(
        start=times[0] - freq/2,
        end=times[-1] + freq/2,
        freq=sub_offset,
        tz=times.tz,
        inclusive=side,
    )

    fine_solpos = solar_position_func(fine_times, latitude, longitude, **kwargs)

    # Mask sub-intervals where the sun is below the horizon with NaN so
    # that resample().agg() automatically ignores them.
    above_horizon = fine_solpos["elevation"] > 0
    fine_solpos = fine_solpos.where(above_horizon)

    # Circular aggregation for azimuth to handle the 0°/360° wraparound.
    azimuth_rad = np.radians(fine_solpos["azimuth"])
    sin_az = np.sin(azimuth_rad)
    cos_az = np.cos(azimuth_rad)

    resample_params = {"rule": freq, "closed": side, "label": "left", "origin": times[0] - freq / 2}

    non_azimuth_cols = [c for c in fine_solpos.columns if c != "azimuth"]
    result = fine_solpos[non_azimuth_cols].resample(**resample_params).agg(agg_func)

    result["azimuth"] = (
        np.degrees(np.arctan2(
            sin_az.resample(**resample_params).agg(agg_func),
            cos_az.resample(**resample_params).agg(agg_func),
        )) % 360
    )

    result.index = result.index + freq/2

    # Restore original column order.
    result = result[fine_solpos.columns]

    return result
