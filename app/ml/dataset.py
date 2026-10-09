"""Leakage-aware feature/label alignment."""


def align_training_rows(features, labels):
    by_time = {x["time"]: x for x in labels}
    if len(by_time) != len(labels):
        raise ValueError("Duplicate labels")
    result = []
    for feature in features:
        label = by_time.get(feature["time"])
        if label is None:
            continue
        if feature["asof_time"] >= feature["time"]:
            raise ValueError("Feature uses nonhistorical data")
        if label["label_available_at"] <= feature["time"]:
            raise ValueError("Invalid future label horizon")
        result.append({**feature, **label})
    return result
