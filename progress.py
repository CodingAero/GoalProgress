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


def plot_folder(ax, endpoints_path, data_path, title):
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

    line_forecast = ax.plot(forecast_dates, forecast_values, label="Forecast (linear extrapolation)", marker="o")
    line_actual = ax.plot(actual_dates, actual_values, label="Actual data", marker="s")

    forecast_color = line_forecast[0].get_color()
    actual_color = line_actual[0].get_color()

    # Add label for today if it's on the plot
    today = datetime.now().date()
    for date, value in forecast:
        if date == today:
            ax.annotate(f"{value:.1f}", xy=(date, value), xytext=(5, 5),
                        textcoords="offset points", fontsize=10, ha="left", color=forecast_color)
            break

    # Add label for most recent data point
    if actual:
        most_recent_date, most_recent_value = actual[-1]
        ax.annotate(f"{most_recent_value:.1f}", xy=(most_recent_date, most_recent_value),
                    xytext=(5, -15), textcoords="offset points", fontsize=10, ha="left", color=actual_color)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    ax.tick_params(axis="x", rotation=45)


if __name__ == "__main__":
    root = Path(__file__).parent
    # Find subdirectories that contain both data.json and endPoints.json
    candidate_dirs = [p for p in root.iterdir() if p.is_dir()]
    folders = []
    for p in candidate_dirs:
        data_file = p / "data.json"
        endpoints_file = p / "endPoints.json"
        if data_file.exists() and endpoints_file.exists():
            folders.append((p.name, endpoints_file, data_file))

    if not folders:
        # Fallback to the original weight folder if present
        weight_dir = root / "weight"
        data_file = weight_dir / "data.json"
        endpoints_file = weight_dir / "endPoints.json"
        if data_file.exists() and endpoints_file.exists():
            folders.append((weight_dir.name, endpoints_file, data_file))

    if not folders:
        raise SystemExit("No folders with data.json and endPoints.json found.")

    import math

    n = len(folders)
    cols = min(n, 2)
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows), squeeze=False)
    axes_flat = [ax for row in axes for ax in row]

    for idx, (name, endpoints_path, data_path) in enumerate(folders):
        ax = axes_flat[idx]
        plot_folder(ax, endpoints_path, data_path, title=name)

    # Hide any unused axes
    for ax in axes_flat[n:]:
        ax.set_visible(False)

    fig.tight_layout()
    fig.savefig(root / "progress.png", dpi=150)
    plt.close(fig)
