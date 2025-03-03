import subprocess
import pytest
from unittest.mock import patch
import os
import requests

from geoloc_util import fetch_api_data, fetch_location_by_city_state, fetch_location_by_zip

EXECUTABLE = './dist/geoloc_util'

## Integration tests of the executable build
@pytest.fixture(autouse=True)
def check_executable_exists():
    """Ensure the executable exists before running any tests."""
    if not os.path.exists(EXECUTABLE):
        pytest.skip(f'Executable {EXECUTABLE} not found. Please build it with PyInstaller.')

@pytest.fixture
def run_utility():
    """Fixture to run the CLI utility and return its output."""
    def _run(args: list) -> str:
        result = subprocess.run(
            [EXECUTABLE, '--locations'] + args,
            capture_output=True,
            text=True,
            check=True,  # Raise an exception if the command fails
        )
        return result.stdout.strip()
    return _run

@pytest.fixture
def run_utility_with_result():
    """Fixture to run the CLI utility and return the full subprocess result."""
    def _run(args: list) -> subprocess.CompletedProcess:
        return subprocess.run(
            [EXECUTABLE] + args,
            capture_output=True,
            text=True,
        )
    return _run

def test_single_city_state(run_utility):
    """Test a single city/state input."""
    output = run_utility(['Madison, WI'])
    assert 'Madison' in output
    assert 'Lat:' in output
    assert 'Lon:' in output

def test_single_zip(run_utility):
    """Test a single zip code input."""
    output = run_utility(['53703'])  # Madison, WI zip code
    assert 'Madison' in output
    assert 'Lat:' in output
    assert 'Lon:' in output

@pytest.mark.parametrize(
    'locations, expected_lines, expected_names',
    [
        (
            ['Madison, WI', '10001', 'Chicago, IL'],
            3,
            ['Madison', 'New York', 'Chicago']
        ),
    ],
)
def test_multiple_locations(run_utility, locations, expected_lines, expected_names):
    """Test multiple location inputs."""
    output = run_utility(locations)
    lines = output.split('\n')
    assert len(lines) == expected_lines
    for line, name in zip(lines, expected_names):
        assert name in line

def test_invalid_location(run_utility):
    """Test an invalid location input."""
    output = run_utility(['InvalidCity, XX'])
    assert 'No data returned from API' in output

def test_mixed_valid_and_invalid(run_utility):
    """Test a mix of valid and invalid inputs."""
    output = run_utility(['Madison, WI', 'XXXXXX'])
    lines = output.split('\n')
    assert len(lines) == 2
    assert 'Madison' in lines[0]
    assert 'No data returned from API' in lines[1]

def test_empty_locations_list(run_utility_with_result):
    """Test running with an empty locations list."""
    result = run_utility_with_result(['--locations'])
    assert result.returncode != 0  # Non-zero exit code for error
    assert 'error: argument --locations: expected at least one argument' in result.stderr

def test_no_locations_argument(run_utility_with_result):
    """Test running without the --locations argument entirely."""
    result = run_utility_with_result([])
    assert result.returncode != 0  # Non-zero exit code for error
    assert 'error: the following arguments are required: --locations' in result.stderr

## Unit tests for Error handling
# Mock response class to simulate requests.get behavior
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)

# New error handling tests
@pytest.mark.parametrize(
    'status_code, json_data, expected_error',
    [
        (401, {}, 'Invalid API key'),
        (429, {}, 'API rate limit exceeded'),
        (500, {}, 'API error: 500'),
        (200, [], 'No data returned from API'),  # Empty response for 'direct'
        (200, {}, 'No data returned from API'),  # Empty response for 'zip'
    ],
)
def test_fetch_api_data_http_errors(status_code, json_data, expected_error):
    """Test fetch_api_data with various HTTP errors and empty responses."""
    with patch('requests.get', return_value=MockResponse(json_data, status_code)):
        result = fetch_api_data('direct', {'q': 'Madison, WI,US', 'limit': 1, 'appid': 'test'})
        assert 'error' in result
        assert result['error'] == expected_error

def test_fetch_api_data_timeout():
    """Test fetch_api_data with a timeout error."""
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        result = fetch_api_data('zip', {'zip': '12345,US', 'appid': 'test'})
        assert 'error' in result
        assert result['error'] == 'API request timed out'

def test_fetch_api_data_connection_error():
    """Test fetch_api_data with a connection error."""
    with patch('requests.get', side_effect=requests.exceptions.ConnectionError):
        result = fetch_api_data('direct', {'q': 'Madison, WI,US', 'limit': 1, 'appid': 'test'})
        assert 'error' in result
        assert result['error'] == 'API connection failed'

def test_fetch_location_by_city_state_error():
    """Test fetch_location_by_city_state with an API error."""
    with patch('requests.get', return_value=MockResponse({}, 401)):
        result = fetch_location_by_city_state('Madison, WI')
        assert 'error' in result
        assert result['error'] == 'Invalid API key'

def test_fetch_location_by_zip_error():
    """Test fetch_location_by_zip with an API error."""
    with patch('requests.get', side_effect=requests.exceptions.Timeout):
        result = fetch_location_by_zip('12345')
        assert 'error' in result
        assert result['error'] == 'API request timed out'