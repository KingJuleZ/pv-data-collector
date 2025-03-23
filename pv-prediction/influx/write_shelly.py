# influx/write_shelly.py

import os
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv("../config/secrets.env")

# Shelly device config
SHELLY_IP = "192.168.0.92"
DEVICE_NAME = "hoymiles_shelly"

# Influx config
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = "pv_data"

print(f"InfluxDB URL: {INFLUX_URL}")
print(f"InfluxDB Token: {INFLUX_TOKEN}")
print(f"InfluxDB Org: {INFLUX_ORG}")

def fetch_shelly_status(ip):
    try:
        response = requests.get(f"http://{ip}/rpc/Shelly.GetStatus", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"?? Error fetching from {ip}: {e}")
        return None

def write_to_influx(status):
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        switch_status = status.get("switch:0", {})
        power = switch_status.get("apower", 0.0)  # Active power in watts
        voltage = switch_status.get("voltage", None)  # Voltage in volts
        current = switch_status.get("current", None)  # Current in amperes
        aenergy = switch_status.get("aenergy", {}).get("total", None)  # Total accumulated energy in watt-minutes
        external_temp = switch_status.get("temperature", {}).get("tC", None)  # Device temperature in Celsius

        point = (
            Point("pv_power")
            .tag("device", DEVICE_NAME)
            .field("power_w", power)
            .time(datetime.now(timezone.utc), WritePrecision.S)
        )

        write_api.write(bucket=INFLUX_BUCKET, record=point)

        if voltage is not None:
            voltage_point = (
                Point("voltage")
                .tag("device", DEVICE_NAME)
                .field("voltage_v", voltage)
                .time(datetime.now(timezone.utc), WritePrecision.S)
            )
            write_api.write(bucket=INFLUX_BUCKET, record=voltage_point)

        if current is not None:
            current_point = (
                Point("current")
                .tag("device", DEVICE_NAME)
                .field("current_a", current)
                .time(datetime.now(timezone.utc), WritePrecision.S)
            )
            write_api.write(bucket=INFLUX_BUCKET, record=current_point)

        if aenergy is not None:
            aenergy_point = (
                Point("accumulated_energy")
                .tag("device", DEVICE_NAME)
                .field("energy_wh", aenergy * 0.0166667)  # Convert watt-minutes to watt-hours
                .time(datetime.now(timezone.utc), WritePrecision.S)
            )
            write_api.write(bucket=INFLUX_BUCKET, record=aenergy_point)

        external_temp = status.get("temperature:100", {}).get("tC", None)
        if external_temp is not None:
            ext_temp_point = (
                Point("external_temperature")
                .tag("device", DEVICE_NAME)
                .field("temp_c", external_temp)
                .time(datetime.now(timezone.utc), WritePrecision.S)
            )
            write_api.write(bucket=INFLUX_BUCKET, record=ext_temp_point)
            print(f"? External sensor temperature: {external_temp}°C")

        print(f"? Wrote data: power={power}W, voltage={voltage}V, current={current}A, energy={aenergy}Wh, temp={external_temp}°C")


if __name__ == "__main__":
    status = fetch_shelly_status(SHELLY_IP)
    if status:
        write_to_influx(status)
# influx/write_shelly.py
