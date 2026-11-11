"""Fallback obligations draw helper for D2 mapping (ASM-D4).

Spec: docs/08-datasets.md section 3, config/generator.toml [obligations_fallback].
Seed derivation: docs/experiment-protocol.md section 1.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import numpy as np


def draw_fallback_obligations(
    sk_id_curr: int,
    monthly_net_income: int | None,
    fallback_base_seed: int,
    zero_fraction: Any,
    beta_alpha: Any,
    beta_beta: Any,
) -> int:
    """Draw from the fallback obligations distribution for one applicant.

    Seed = (fallback_base_seed + sk_id_curr) % (2**32).
    Draws share from Beta(beta_alpha, beta_beta) with probability (1 - zero_fraction).
    Returns whole rupees (int), rounded half-up.
    """
    seed = (fallback_base_seed + sk_id_curr) % (2**32)
    rng = np.random.default_rng(seed)
    zf = float(str(zero_fraction))
    if rng.random() < zf:
        return 0
    ba = float(str(beta_alpha))
    bb = float(str(beta_beta))
    share = rng.beta(ba, bb)
    if monthly_net_income is None or monthly_net_income == 0:
        return 0
    amount = Decimal(str(share)) * Decimal(str(monthly_net_income))
    return int(amount.to_integral_value(rounding=ROUND_HALF_UP))
