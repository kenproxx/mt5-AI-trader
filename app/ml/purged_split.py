"""Time-based split with strict label availability before later folds."""


def purged_chronological_split(rows, *, train_fraction=0.6, validation_fraction=0.2):
    if not (0 < train_fraction < 1 and 0 < validation_fraction < 1):
        raise ValueError("Invalid split fractions")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Invalid split fractions")
    data = list(rows)
    if any(
        row["asof_time"] >= row["time"] or row["label_available_at"] <= row["time"]
        for row in data
    ):
        raise ValueError("Invalid feature or label timestamps")
    if any(data[i]["time"] >= data[i + 1]["time"] for i in range(len(data) - 1)):
        raise ValueError("Rows must be ordered and unique")
    a = int(len(data) * train_fraction)
    b = int(len(data) * (train_fraction + validation_fraction))
    if not (0 < a < b < len(data)):
        raise ValueError("Not enough observations")
    train = [row for row in data[:a] if row["label_available_at"] < data[a]["time"]]
    validation = [
        row for row in data[a:b] if row["label_available_at"] < data[b]["time"]
    ]
    test = data[b:]
    if not train or not validation or not test:
        raise ValueError("Not enough rows after purging")
    return train, validation, test
