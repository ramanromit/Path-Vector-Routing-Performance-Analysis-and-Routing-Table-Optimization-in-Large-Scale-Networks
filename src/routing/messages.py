"""Path Vector BGP-style Routing Protocol Messages.

Implements UPDATE and WITHDRAWAL messages carrying AS-path vectors.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class MessageType(Enum):
    """BGP Message Types."""
    UPDATE = "UPDATE"
    WITHDRAWAL = "WITHDRAWAL"


@dataclass(frozen=True)
class RouteMessage:
    """Represents a Path Vector routing message exchanged between adjacent ASes."""
    msg_type: MessageType
    sender_as: int
    receiver_as: int
    prefix: str
    as_path: Tuple[int, ...] = field(default_factory=tuple)
    next_hop: int = 0
    metric: int = 0

    @property
    def is_withdrawal(self) -> bool:
        return self.msg_type == MessageType.WITHDRAWAL

    @property
    def path_length(self) -> int:
        return len(self.as_path)

    def contains_as(self, as_id: int) -> bool:
        """Loop detection check."""
        return as_id in self.as_path

    def __repr__(self) -> str:
        if self.is_withdrawal:
            return f"WITHDRAW(from=AS{self.sender_as}->AS{self.receiver_as}, prefix={self.prefix})"
        path_str = " -> ".join(f"AS{a}" for a in self.as_path)
        return f"UPDATE(from=AS{self.sender_as}->AS{self.receiver_as}, prefix={self.prefix}, path=[{path_str}], next_hop=AS{self.next_hop})"
