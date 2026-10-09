"""No look-ahead: strictly ordered time splits."""


def chronological_split(records, train_fraction=0.6, validation_fraction=0.2, embargo=0):
    if not (0 < train_fraction < 1 and 0 < validation_fraction < 1):
        raise ValueError("Invalid fractions")
    if train_fraction + validation_fraction >= 1 or embargo < 0:
        raise ValueError("Invalid split")
    ordered = list(records)
    if any(ordered[i]["time"] >= ordered[i + 1]["time"]
           for i in range(len(ordered) - 1)):
        raise ValueError("Records must be chronological and unique")
    n = len(ordered)
    a = int(n * train_fraction)
    b = int(n * (train_fraction + validation_fraction))
    train = ordered[:a]
    validation = ordered[a + embargo:b]
    test = ordered[b + embargo:]
    if not train or not validation or not test:
        raise ValueError("Insufficient observations after embargo")
    return train, validation, test
