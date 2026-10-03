from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Expense:
    description: str
    amount: Decimal
    category: str
    date: date
    id: UUID = field(default_factory=uuid4, init=False)

    @classmethod
    def restore(
        cls, *, id: UUID, description: str, amount: Decimal, category: str, date: date
    ) -> "Expense":
        """Reconstruct an existing expense using typed, validated values."""
        if not isinstance(id, UUID):
            raise TypeError("id must be a UUID")
        expense = cls(description=description, amount=amount, category=category, date=date)
        object.__setattr__(expense, "id", id)
        return expense

    def __post_init__(self) -> None:
        for name in ("description", "category"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            value = value.strip()
            if not value:
                raise ValueError(f"{name} must not be blank")
            object.__setattr__(self, name, value)

        if not isinstance(self.amount, Decimal):
            raise TypeError("amount must be a Decimal")
        if not self.amount.is_finite() or self.amount <= 0:
            raise ValueError("amount must be finite and greater than zero")

        if not isinstance(self.date, date) or isinstance(self.date, datetime):
            raise TypeError("date must be a date, not a datetime")
