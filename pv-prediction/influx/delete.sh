#!/bin/bash

# Load environment variables
if [ -f ../config/secrets.env ]; then
  export $(grep -v '^#' ../config/secrets.env | xargs)
else
  echo ".env file not found!"
  exit 1
fi

# Check required vars
: "${INFLUX_TOKEN:?Missing INFLUX_TOKEN in .env}"
: "${INFLUX_ORG:?Missing INFLUX_ORG in .env}"
: "${INFLUX_BUCKET:?Missing INFLUX_BUCKET in .env}"
: "${INFLUX_URL:?Missing INFLUX_URL in .env}"

# Time range
START="1970-01-01T00:00:00Z"
STOP="2100-01-01T00:00:00Z"

# Default: no predicate yet
FILTER=""

echo "Using org: $INFLUX_ORG"

# Parse CLI arguments
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --all)
      echo "⚠️ Deleting ALL data in bucket '$INFLUX_BUCKET'..."
      FILTER='_measurement!=""'  # safest supported all-data filter
      ;;
    --measurement)
      shift
      MEASUREMENT="$1"
      FILTER="_measurement=\"$MEASUREMENT\""
      ;;
    --device)
      shift
      DEVICE="$1"
      FILTER="${FILTER} AND device=\"$DEVICE\""
      ;;
    *)
      echo "❌ Unknown argument: $1"
      echo "Usage:"
      echo "  $0 --all"
      echo "  $0 --measurement accumulated_energy"
      echo "  $0 --measurement accumulated_energy --device hoymiles_shelly"
      exit 1
      ;;
  esac
  shift
done

# Make sure something was set
if [ -z "$FILTER" ]; then
  echo "❌ No valid deletion criteria given."
  exit 1
fi

echo "🔍 Predicate: $FILTER"
read -p "❗ Really delete matching data? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
  echo "❌ Aborted."
  exit 0
fi

# Run delete command
influx delete \
  --org "$INFLUX_ORG" \
  --bucket "$INFLUX_BUCKET" \
  --token "$INFLUX_TOKEN" \
  --host "$INFLUX_URL" \
  --start "$START" \
  --stop "$STOP" \
  --predicate "$FILTER"

echo "✅ Deletion completed."
