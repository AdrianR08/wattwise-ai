import argparse
import json
from pathlib import Path

from src.consumption import analyze_csv


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze an hourly customer consumption CSV')
    parser.add_argument('csv')
    parser.add_argument('--unit', choices=['kWh', 'kW'], required=True)
    parser.add_argument('--timezone', default='UTC')
    parser.add_argument('--timestamp-column')
    parser.add_argument('--value-column')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze_csv(args.csv, unit=args.unit, timezone=args.timezone,
                         timestamp_column=args.timestamp_column, value_column=args.value_column)
    text = json.dumps(result, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text)
