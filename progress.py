import json
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_date(date_string):
    return datetime.strptime(date_string, "%m-%d-%Y").date()


def build_date_range(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def linear_extrapolation(start_date, start_value, end_date, end_value):
    days_total = (end_date - start_date).days
    if days_total <= 0:
        return [(start_date, start_value)]

    output = []
    for offset, current_date in enumerate(build_date_range(start_date, end_date)):
        fraction = offset / days_total
        value = start_value + (end_value - start_value) * fraction
        output.append((current_date, value))
    return output


def load_actual_data(data_path):
    payload = load_json(data_path)
    samples = payload.get("data", [])
    actual = []
    for entry in samples:
        date = parse_date(entry["date"])
        value = float(entry["value"])
        actual.append((date, value))
    actual.sort(key=lambda item: item[0])
    return actual


def plot_progress(endpoints_path, data_path, output_path):
    endpoints = load_json(endpoints_path)
    start = endpoints["start"]
    end = endpoints["end"]

    start_date = parse_date(start["date"])
    end_date = parse_date(end["date"])
    start_value = float(start["value"])
    end_value = float(end["value"])

    forecast = linear_extrapolation(start_date, start_value, end_date, end_value)
    actual = load_actual_data(data_path)

    forecast_dates = [d for d, _ in forecast]
    forecast_values = [v for _, v in forecast]

    actual_dates = [d for d, _ in actual]
    actual_values = [v for _, v in actual]

    plt.figure(figsize=(10, 6))
    line_forecast = plt.plot(forecast_dates, forecast_values, label="Forecast (linear extrapolation)", marker="o")
    line_actual = plt.plot(actual_dates, actual_values, label="Actual data", marker="s")

    forecast_color = line_forecast[0].get_color()
    actual_color = line_actual[0].get_color()

    # Add label for today if it's on the plot
    today = parse_date("06-15-2026")
    for date, value in forecast:
        if date == today:
            idx = forecast_dates.index(date)
            plt.annotate(f"{value:.1f}", xy=(date, value), xytext=(5, 5),
                        textcoords="offset points", fontsize=12, ha="left", color=forecast_color)
            break

    # Add label for most recent data point
    if actual:
        most_recent_date, most_recent_value = actual[-1]
        idx = actual_dates.index(most_recent_date)
        plt.annotate(f"{most_recent_value:.1f}", xy=(most_recent_date, most_recent_value),
                    xytext=(5, -15), textcoords="offset points", fontsize=12, ha="left", color=actual_color)

    plt.title("Goal Progress")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


if __name__ == "__main__":
    root = Path(__file__).parent
    plot_progress(root / "endPoints.json", root / "data.json", root / "progress.png")
