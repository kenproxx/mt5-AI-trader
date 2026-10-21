"""Strategy inputs and persistent layer counters."""
from dataclasses import dataclass, field
from decimal import Decimal

from app.broker.models import Validation


@dataclass(frozen=True)
class Position:
    ticket: int
    side: str
    lots: Decimal
    entry: Decimal
    stop: Decimal
    pnl: Decimal  # MT5 floating profit + accrued swap, before reserved exit costs.
    role: str = 'primary'


@dataclass(frozen=True)
class Snapshot:
    status: Validation
    positions: tuple[Position, ...]
    identity: str
    now: int


@dataclass
class BasketState:
    side: str | None = None
    anchor: Decimal = Decimal('0')
    hedged: bool = False
    dca_before: int = 0
    dca_after: int = 0
    hedge_count: int = 0
    pyramid_count: int = 0
    last_action: int = 0
    exiting: bool = False
    tickets: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    kind: str
    reason: str
    side: str = ''
    lots: Decimal = Decimal('0')
    stop: Decimal = Decimal('0')
    tickets: tuple[int, ...] = ()

    @property
    def opens_position(self):
        return self.kind in ('SEED', 'HEDGE', 'DCA_BEFORE', 'DCA_AFTER', 'PYRAMID')
