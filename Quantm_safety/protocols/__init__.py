"""Quantum Protocols: BB84, E91, and Q-SHIELD Hybrid.

The Q-SHIELD hybrid protocol is the core innovation of this platform,
combining QKD (BB84) with Post-Quantum Cryptography (Kyber768) under a
trust-aware controller that automatically falls back to PQC-only when
quantum channel conditions degrade.
"""

from .bb84 import BB84Protocol
from .e91 import E91Protocol
from .qshield_hybrid import QShieldHybrid, HybridResult, ProtocolMode
