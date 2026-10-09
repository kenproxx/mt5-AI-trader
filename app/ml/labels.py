"""Research labels; explicitly record future availability time."""


def forward_direction_labels(candles, horizon=3):
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    data = list(candles)
    times = [x["time"] for x in data]
    if any(a >= b for a, b in zip(times, times[1:], strict=False)):
        raise ValueError("Candles must be chronological")
    labels = []
    for i in range(len(data) - horizon):
        current = float(data[i]["close"])
        future = float(data[i + horizon]["close"])
        if current <= 0 or future <= 0:
            raise ValueError("Prices must be positive")
        labels.append({
            "time": data[i]["time"],
            "label_available_at": data[i + horizon]["time"],
            "target_up": int(future > current),
        })
    return labels
