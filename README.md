# Geoloc Utility [![Build and Test](https://github.com/crank-chips/geoloc/actions/workflows/build_test.yml/badge.svg?branch=main&event=push)](https://github.com/crank-chips/geoloc/actions/workflows/build_test.yml)

CLI utility to fetch geolocation data (city, state, latitude, longitude) for US cities or zip codes using the Open Weather Geocoding API.

## Requirements
- To run or build from source code: macOS or Linux, Python 3.12+, `requests`, and `pyinstaller`.
- To run binary from `dist` folder no additional installation needed

## Usage of Pre-Built Executable
1. Clone this repository:
   ```bash
   git clone git@github.com:crank-chips/geoloc.git
   cd geoloc
2. Export the OpenWeather API key to your environment profile config file `~/.zshrc` or `~/.bashrc`:
   ```bash
   echo "export OPENWEATHER_API_KEY='your_api_key'" >> "env_profile_config_file"
3. Build binary executable: [Building from Source](#building-from-source-code)
4. Run utility:

   Use `--location` argument to pass locations list in format `"Location1" "Location2" "LocationN"`, locations must be separated by space
   Example:
   ```bash
   ./dist/geoloc_util --location "Madison, WI" "Chicago, IL" "10001"
   
  ### Example Output
   ```
   Location: Madison, WI - Lat: 43.0731, Lon: -89.4012
   Location: Chicago, IL - Lat: 41.8781, Lon: -87.6298
   Location: New York - Lat: 40.7128, Lon: -74.0060
   ```

### Notes
- Scope is limited to US locations.
- For multiple API results, the first result is used.
- For ZIP code lookup only city name is provided without the state code.

## Building from Source code

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
2. Build the executable:
   ```bash
   pyinstaller --onefile geoloc_util.py
   ```
   OR for Apple Silicon arch we need to force 86_64 (pyinstaller is having issues building binary on Apple Silicon by default)
   ```
   arch -x86_64 pyinstaller --onefile geoloc_util.py
   ```

## Testing
   To run all test:
   ```bash
      python -m pytest -v
   ```