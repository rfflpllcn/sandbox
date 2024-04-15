import pytest
from unittest.mock import AsyncMock

from sandbox.cov_caching import BulkCovarianceCache

@pytest.mark.asyncio
@pytest.mark.skip("dfdefvv")
async def test_bulk_covariance_cache(mocker):
    # Mock the wrapper object with AsyncMock directly
    mock_wrapper = mocker.Mock()
    mock_wrapper.get_lower_triangular_square_covariance = AsyncMock(return_value={
        'key1:key1': 1.0,
        'key1:key2': 0.5,
        'key1:key3': 0.3,
        'key2:key2': 1.0,
        'key2:key3': 0.4,
        'key3:key3': 1.0
    })

    # Create an instance of the cache
    cache = BulkCovarianceCache(ttl=1000)

    # Prepare the mock data
    svc = {
        'calcCovarianceParameter': {'param': 'value'},
        'listSearchKeys': [{'tsKey': 'key1'}, {'tsKey': 'key2'}, {'tsKey': 'key3'}]
    }

    # Call the method under test
    results = await cache.get_covariances(mock_wrapper, svc)

    # Check if the results are as expected
    expected_covariance = {
        'key1:key1': 1.0,
        'key1:key2': 0.5,
        'key1:key3': 0.3,
        'key2:key2': 1.0,
        'key2:key3': 0.4,
        'key3:key3': 1.0
    }
    for key, expected_value in expected_covariance.items():
        assert results[key] == expected_value, f"Failed for {key}"


@pytest.mark.asyncio
async def test_cache_miss_and_fill(mocker):
    # Create a mock wrapper with an AsyncMock for the data retrieval method
    mock_wrapper = mocker.Mock()
    expected_data = {
        'key1:key1': 1.0,
        'key1:key2': 0.5,
        'key1:key3': 0.3,
        'key2:key2': 1.0,
        'key2:key3': 0.4,
        'key3:key3': 1.0
    }
    mock_wrapper.get_lower_triangular_square_covariance = AsyncMock(return_value=expected_data)

    # Create the cache instance
    cache = BulkCovarianceCache(ttl=3600)  # TTL is just an example

    # Prepare the service configuration (svc)
    svc = {
        'calcCovarianceParameter': {'param': 'value'},
        'listSearchKeys': [{'tsKey': 'key1'}, {'tsKey': 'key2'}, {'tsKey': 'key3'}]
    }

    # Initial cache miss check
    # Simulate accessing the cache for 'key1:key2' which should be a miss and trigger data fetching
    initial_result = await cache.get_covariances(mock_wrapper, svc)
    assert initial_result['key1:key2'] == 0.5, "Cache miss did not fetch the expected data."

    # Verify the mock was called
    mock_wrapper.get_lower_triangular_square_covariance.assert_called_once()

    # Now test cache hit, access the same data again
    second_result = await cache.get_covariances(mock_wrapper, svc)
    assert second_result['key1:key2'] == 0.5, "Cache did not return expected data on second access."

    # Ensure the data source is not queried again
    mock_wrapper.get_lower_triangular_square_covariance.assert_called_once()  # Still only one call

