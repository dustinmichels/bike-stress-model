"""Validated score tables shared by the stress models.

Scores run from 0 (lowest stress) to 4 (highest stress).
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

# `int | float` keeps integer scores as ints, so score columns keep their dtype.
Score = Annotated[int | float, Field(ge=0, le=4)]


class Tier(BaseModel):
    model_config = ConfigDict(frozen=True)

    max_value: float
    """Inclusive upper bound of the tier."""
    score: Score


class Tiers(RootModel[tuple[Tier, ...]]):
    """Threshold tiers ordered by ascending `max_value`."""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def _ascending(self) -> "Tiers":
        bounds = [tier.max_value for tier in self.root]
        if not bounds:
            raise ValueError("at least one tier is required")
        if bounds != sorted(bounds):
            raise ValueError(f"tier bounds must ascend, got {bounds}")
        return self

    def score(self, value: float) -> int | float:
        """Score of the first tier whose bound is >= `value`; the last tier above all bounds."""
        for tier in self.root:
            if value <= tier.max_value:
                return tier.score
        return self.root[-1].score
