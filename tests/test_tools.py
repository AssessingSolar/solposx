import pandas as pd
import numpy as np
import pytest
from solposx.tools import _pandas_to_utc, _fractional_hour, calc_error


@pytest.fixture
def times_index():
    return pd.date_range('2020-01-01', freq='1h', periods=10, tz=-60*60)


@pytest.fixture
def times_index_utc():
    return pd.date_range('2020-01-01 01', freq='1h', periods=10, tz='UTC')


def test_pandas_to_utc(times_index, times_index_utc):
    result = _pandas_to_utc(times_index)
    pd.testing.assert_index_equal(result, times_index_utc)


def test_pandas_to_utc_missing_tz():
    with pytest.raises(TypeError, match='stamps are timezone naive.'):
        _pandas_to_utc(pd.date_range('2020-01-01', '2020-01-02'))


@pytest.fixture
def expected_fractional_hour():
    return pd.Index([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])


def test_fractional_hour(times_index, expected_fractional_hour):
    result = _fractional_hour(times_index)
    pd.testing.assert_index_equal(result, expected_fractional_hour)


@pytest.fixture
def expected_calc_error_zeros():
    N = 10
    out = {
        'zenith_bias': np.zeros(N),
        'zenith_mad': np.zeros(N),
        'zenith_rmsd': np.zeros(N),
        'azimuth_bias': np.zeros(N),
        'azimuth_mad': np.zeros(N),
        'azimuth_rmsd': np.zeros(N),
        'combined_rmsd': np.zeros(N),
    }
    return out


def test_calc_error_zeros(expected_calc_error_zeros):
    zeros = np.zeros(10)
    result = calc_error(zeros, zeros, zeros, zeros)
    for k in expected_calc_error_zeros.keys():
        np.testing.assert_equal(result[k], expected_calc_error_zeros[k])
    assert len(result.keys()) == len(expected_calc_error_zeros.keys())


@pytest.mark.parametrize('zenith', [0, 45, 90, 135, 180])
@pytest.mark.parametrize('azimuth', [0, 45, 90, 135, 180, 225, 270, 315, 360])
@pytest.mark.parametrize('zenith_delta', [-100, -50, 0, 50, 100])
def test_calc_error_zenith_shift(zenith, azimuth, zenith_delta):
    zenith = np.array([zenith])
    azimuth = np.array([azimuth])
    errs = calc_error(zenith+zenith_delta, azimuth, zenith, azimuth)

    np.testing.assert_almost_equal(errs['zenith_bias'], zenith_delta)
    np.testing.assert_almost_equal(errs['zenith_mad'], abs(zenith_delta))
    np.testing.assert_almost_equal(errs['zenith_rmsd'], abs(zenith_delta))

    for key in ['azimuth_bias', 'azimuth_mad', 'azimuth_rmsd']:
        np.testing.assert_almost_equal(errs[key], 0)

    np.testing.assert_almost_equal(errs['combined_rmsd'], abs(zenith_delta))


@pytest.mark.parametrize('zenith', [0, 45, 90, 135, 180])
@pytest.mark.parametrize('azimuth', [0, 45, 90, 135, 180, 225, 270, 315, 360])
@pytest.mark.parametrize('azimuth_delta', [
    -300, -200, -100, -10, 0, 10, 100, 200, 300
])
def test_calc_error_azimuth_shift(zenith, azimuth, azimuth_delta):
    errs = calc_error(zenith, azimuth+azimuth_delta, zenith, azimuth)

    for key in ['zenith_bias', 'zenith_mad', 'zenith_rmsd']:
        np.testing.assert_almost_equal(errs[key], 0)

    expected_azimuth_diff = azimuth_delta % 360
    expected_azimuth_diff = np.minimum(expected_azimuth_diff,
                                       360 - expected_azimuth_diff)
    np.testing.assert_almost_equal(abs(errs['azimuth_bias']),
                                   expected_azimuth_diff)
    np.testing.assert_almost_equal(abs(errs['azimuth_mad']),
                                   expected_azimuth_diff)
    np.testing.assert_almost_equal(abs(errs['azimuth_rmsd']),
                                   expected_azimuth_diff)

    # equal when zenith=90, otherwise less than.  1e-3 accommodates round-off
    assert errs['combined_rmsd'] <= expected_azimuth_diff + 1e-8


def test_calc_error_special_cases():
    result = calc_error(90, 0, 0, 90)
    assert result == pytest.approx({
        'zenith_bias': 90, 'zenith_mad': 90, 'zenith_rmsd': 90,
        'azimuth_bias': -90, 'azimuth_mad': 90, 'azimuth_rmsd': 90,
        'combined_rmsd': 90,
    })
    result = calc_error(0, 270, 0, 90)
    assert result == pytest.approx({
        'zenith_bias': 0, 'zenith_mad': 0, 'zenith_rmsd': 0,
        'azimuth_bias': -180, 'azimuth_mad': 180, 'azimuth_rmsd': 180,
        'combined_rmsd': 0,
    })
    result = calc_error(45, 270, 45, 90)
    assert result == pytest.approx({
        'zenith_bias': 0, 'zenith_mad': 0, 'zenith_rmsd': 0,
        'azimuth_bias': -180, 'azimuth_mad': 180, 'azimuth_rmsd': 180,
        'combined_rmsd': 90,
    })
