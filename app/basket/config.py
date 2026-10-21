"""Strict, bounded basket configuration. Values are examples, not trading advice."""
import hashlib
import json
from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from pathlib import Path

D = Decimal


@dataclass(frozen=True)
class BasketConfig:
    magic: int = 5202601
    lot: Decimal = D('0.01')
    max_positions: int = 6
    max_total_lots: Decimal = D('0.06')
    stop_points: Decimal = D('2000')
    dca_before_points: tuple[Decimal, ...] = (D('300'),)
    dca_after_points: tuple[Decimal, ...] = (D('900'), D('1500'))
    hedge_points: tuple[Decimal, ...] = (D('600'), D('1200'))
    hedge_ratios: tuple[Decimal, ...] = (D('0.5'), D('1'))
    pyramid_step_points: Decimal = D('300')
    max_pyramid_layers: int = 2
    trim_enabled: bool = True
    trim_buffer_usd: Decimal = D('0.10')
    costs_per_lot_usd: Decimal = D('10')
    basket_take_profit_usd: Decimal = D('0')
    max_spread_points: Decimal = D('50')
    min_margin_level_pct: Decimal = D('200')
    cooldown_seconds: int = 60
    deviation_points: int = 20

    def __post_init__(self):
        ints = {'magic': (1, 2147483647), 'max_positions': (1, 20),
                'max_pyramid_layers': (0, 10), 'cooldown_seconds': (5, 86400),
                'deviation_points': (0, 1000)}
        for name, (low, high) in ints.items():
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'Invalid {name}')
        if type(self.trim_enabled) is not bool:
            raise ValueError('Invalid trim_enabled')
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in ints or f.name == 'trim_enabled':
                continue
            values = value if isinstance(value, tuple) else (value,)
            if any(not isinstance(v, Decimal) or not v.is_finite() or v < 0 for v in values):
                raise ValueError(f'Invalid {f.name}')
            if isinstance(value, tuple):
                if len(value) > 10 or any(v <= 0 for v in value):
                    raise ValueError(f'Invalid {f.name}')
                if any(a >= b for a, b in zip(value, value[1:], strict=False)):
                    raise ValueError(f'{f.name} must increase')
        if any(getattr(self, name) <= 0 for name in (
            'lot', 'max_total_lots', 'stop_points', 'pyramid_step_points',
            'max_spread_points', 'costs_per_lot_usd',
        )):
            raise ValueError('Lot, distances and cost allowance must be positive')
        if self.max_total_lots < self.lot or self.min_margin_level_pct < 100:
            raise ValueError('Invalid exposure/margin limits')
        if len(self.hedge_points) != len(self.hedge_ratios) or any(
            x > 1 for x in self.hedge_ratios
        ):
            raise ValueError('Hedge coverage must be at most 100%')

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self), default=str,
                                         sort_keys=True).encode()).hexdigest()

    @classmethod
    def load(cls, path):
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        defaults = cls()
        if not isinstance(raw, dict) or set(raw) - {f.name for f in fields(cls)}:
            raise ValueError('Unknown configuration fields')
        for key, value in raw.items():
            default = getattr(defaults, key)
            if isinstance(default, Decimal):
                raw[key] = D(str(value))
            elif isinstance(default, tuple):
                if not isinstance(value, list):
                    raise ValueError(f'Expected array: {key}')
                raw[key] = tuple(D(str(v)) for v in value)
        return cls(**raw)
