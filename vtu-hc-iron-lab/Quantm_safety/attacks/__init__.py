"""Quantum attack modules for security testing.

Each attack implements a common interface:

    launch(alice_bits, alice_basis, bob_basis) -> AttackResult

where AttackResult contains bob_results, qber, and eve_info.
"""

from .base import AttackResult, BaseAttack
from .intercept_resend import InterceptResendAttack
from .pns_attack import PNSAttack
from .detector_blinding import DetectorBlindingAttack
