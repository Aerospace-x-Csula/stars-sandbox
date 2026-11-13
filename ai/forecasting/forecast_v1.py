"""Initial trend forecast for gradually increasing resource usage (Python 3.10+)."""

import json
from statistics import linear_regression


def forecast_capacity(samples, capacity, horizon_minutes=15):
    """Forecast one resource using complete, oldest-first, one-minute readings.

    Readings and capacity must use the same units and refer to the same resource.
    The time estimates assume the recent growth trend continues.
    """
    if len(samples) < 10 or capacity <= 0:
        raise ValueError("Need at least 10 samples and a positive capacity")
    if horizon_minutes <= 0:
        raise ValueError("Forecast horizon must be positive")

    growth_per_minute, _ = linear_regression(range(len(samples)), samples)
    current = samples[-1]
    predicted = max(0, current + growth_per_minute * horizon_minutes)

    def minutes_until(target):
        if current >= target:
            return 0.0
        if growth_per_minute <= 0:
            return None
        return round((target - current) / growth_per_minute, 1)

    return {
        "current_pct": round(current / capacity * 100, 1),
        "forecast_pct": round(predicted / capacity * 100, 1),
        "minutes_to_90_pct": minutes_until(capacity * 0.9),
        "minutes_to_limit": minutes_until(capacity),
        "warning": max(current, predicted) >= capacity * 0.9,
    }


if __name__ == "__main__":
    # example container memory usage in MiB, one reading per minute
    memory_mib = [500, 520, 540, 560, 580, 600, 620, 640, 660, 680]
    result = forecast_capacity(memory_mib, capacity=1024)
    print(json.dumps(result, indent=2))
