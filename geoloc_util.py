#!/usr/bin/env python3
import argparse
import logging
import os
import requests

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

API_KEY = os.environ.get('OPENWEATHER_API_KEY')
if not API_KEY:
    logger.error("OPENWEATHER_API_KEY environment variable is not set")
    raise ValueError("OPENWEATHER_API_KEY environment variable is required")

BASE_URL = 'http://api.openweathermap.org/geo/1.0'

def fetch_api_data(endpoint, params):
    """Make an API call to the Open Weather Geocoding API and return the result or an error."""
    url = f'{BASE_URL}/{endpoint}'
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # raise an exception for 4xx/5xx status codes

        data = response.json()
        if not data:
            logger.warning(f'No data returned from {url} with params {params}')
            return {'error': 'No data returned from API'}

        # Return first item for 'direct', full response for 'zip'
        return data[0] if endpoint == 'direct' else data

    except requests.exceptions.Timeout:
        logger.error(f'Request to {url} timed out after 10 seconds')
        return {'error': 'API request timed out'}
    except requests.exceptions.ConnectionError:
        logger.error(f'Connection error while Accessing {url}')
        return {'error': 'API connection failed'}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            logger.error('Invalid API key provided')
            return {'error': 'Invalid API key'}
        elif status_code == 429:
            logger.error('API rate limit exceeded')
            return {'error': 'API rate limit exceeded'}
        else:
            logger.error(f'HTTP error {status_code} while accessing {url}')
            return {'error': f'API error: {status_code}'}
    except requests.exceptions.RequestException as e:
        logger.error(f'Unexpected error while accessing {url}: {str(e)}')
        return {'error': 'Unexpected API error'}

def fetch_location_by_city_state(query):
    """Fetch location data by city and state."""
    params = {'q': f'{query},US', 'limit': 1, 'appid': API_KEY}
    return fetch_api_data('direct', params)

def fetch_location_by_zip(zip_code):
    """Fetch location data by zip code."""
    params = {'zip': f'{zip_code},US', 'appid': API_KEY}
    return fetch_api_data('zip', params)

def get_location_info(location):
    """Determine input type and fetch location data."""
    location = location.strip()
    if location.isdigit() and len(location) == 5:  # 5-digit US zip code format
        data = fetch_location_by_zip(location)
    else:
        data = fetch_location_by_city_state(location)

    if 'error' in data:
        return data  # Propagate the error from fetch_api_data
    return {
        'name': data.get('name', ''),
        'lat': data.get('lat', ''),
        'lon': data.get('lon', ''),
        'state': data.get('state', ''),
        'country': data.get('country', 'US')
    }

def process_locations(locations):
    """Process multiple location inputs."""
    return [get_location_info(location) for location in locations]

def format_location(result):
    """Format a location result into a string."""
    if 'error' in result:
        return result['error']
    state = f', {result["state"]}' if result.get("state") else ''
    return f'Location: {result["name"]}{state} - Lat: {result["lat"]}, Lon: {result["lon"]}'

def main():
    """Main function to handle CLI arguments and output results."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--locations',
        nargs='+',
        required=True,
        help='List of locations (e.g., "Madison, WI" or "12345")',
    )
    args = parser.parse_args()

    results = process_locations(args.locations)
    for result in results:
        print(format_location(result))

if __name__ == '__main__':
    main()