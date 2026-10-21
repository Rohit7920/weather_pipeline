import time

import pandas as pd
import requests

df = pd.read_csv("data/population.csv", thousands=",").head(50)

weather_records = []

for _, location in df.iterrows():
    api_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={location['Latitude']}"
        f"&longitude={location['Longitude']}"
        f"&current_weather=true"
    )

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        current = response.json()["current_weather"]
        temperature = current["temperature"]
        windspeed = current["windspeed"]
    except (requests.RequestException, KeyError) as error:
        print(f"Failed for {location['City']}: {error}")
        temperature = None
        windspeed = None

    weather_records.append(
        {
            "City": location["City"],
            "Temperature": temperature,
            "Windspeed": windspeed,
        }
    )

    time.sleep(0.2)

print(f"Fetched {len(weather_records)} records")
for record in weather_records[:5]:
    print(record)