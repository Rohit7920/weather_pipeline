import time

import pandas as pd
import requests
from google.cloud import bigquery
from google.oauth2 import service_account

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

weather_df = pd.DataFrame(weather_records)

merged_df = pd.merge(df, weather_df, on="City", how="inner")

print(merged_df.shape)
print(merged_df.head())

print(merged_df.isna().sum())

clean_df = merged_df.dropna(subset=["Temperature", "Windspeed", "Population"]).copy()

clean_df["Population"] = clean_df["Population"].astype("int64")
clean_df["Temperature"] = clean_df["Temperature"].astype("float64")

clean_df["Temperature_F"] = clean_df["Temperature"] * 9 / 5 + 32

clean_df["Temp_Category"] = pd.cut(
    clean_df["Temperature"],
    bins=[-float("inf"), 15, 28, float("inf")],
    labels=["Cold", "Mild", "Hot"],
).astype(str)

print(clean_df.dtypes)
print(clean_df.head(10))
print(clean_df["Temp_Category"].value_counts())

project_id = "flowing-silo-512321-b6"
table_id = f"{project_id}.global_weather_data.current_weather_stats"

credentials = service_account.Credentials.from_service_account_file("scripts/gcp-key.json")
client = bigquery.Client(credentials=credentials, project=project_id)

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

load_job = client.load_table_from_dataframe(clean_df, table_id, job_config=job_config)
load_job.result()

table = client.get_table(table_id)
print(f"Loaded {table.num_rows} rows into {table_id}")