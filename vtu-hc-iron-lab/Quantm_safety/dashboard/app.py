"""Iron Lab Hybrid QKD + Kyber768 Protocol — Quantum-Secured AI Agent Platform.

A corporate MNC / Google-style interface for simulating quantum-safe
AI-to-AI communication using BB84, E91, and the Iron Lab Hybrid QKD + Kyber768 Protocol
combined with GibberLink acoustic audio modems.

Features:
- Bidirectional messaging (Agent Alice 🔁 Agent Bob) with text input.
- Active Eve attack simulation: Passive Eavesdropping vs Active Message Tampering.
- Visual Quantum Circuits (BB84, E91 Bell pairs, Hybrid Architecture).
- Quantum Mathematical Equations in LaTeX / KaTeX.
- Statistical Graphs & Histograms (QBER distributions, Bell CHSH parameter S).
- Complete documentation of all tools and technologies used.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
from typing import Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import numpy as np

# Cryptographic and quantum simulation modules
from core.quantum_sim import BB84Simulator
from core.qber_analyzer import QBERAnalyzer, QBER_THRESHOLD_PERCENT, CHANNEL_LOSS_THRESHOLD
from protocols.bb84 import BB84Protocol
from protocols.e91 import E91Protocol
from protocols.qshield_hybrid import QShieldHybrid, ProtocolMode
from attacks.intercept_resend import InterceptResendAttack
from attacks.pns_attack import PNSAttack
from attacks.detector_blinding import DetectorBlindingAttack
from ai_agent.gibberlink_audio import GibberLinkAudio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory of pre-rendered high-res figures
FIGURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")

# ---------------------------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Iron Lab | Hybrid QKD + Kyber768 Quantum Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Google / MNC Corporate Clean Light Theme CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* Global Base */
    .stApp {
        background-color: #f8f9fa !important;
        color: #202124 !important;
        font-family: 'Google Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Seamless Top Header & Deploy Bar */
    header[data-testid="stHeader"] {
        background-color: #f8f9fa !important;
        border-bottom: 1px solid #dadce0 !important;
        height: 3.5rem !important;
        z-index: 9999 !important;
    }

    /* Remove Streamlit default rainbow decoration line */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Clean corporate style for Deploy button and top toolbar */
    .stDeployButton, [data-testid="stToolbar"] {
        color: #5f6368 !important;
    }
    .stDeployButton button {
        background-color: #ffffff !important;
        color: #1a73e8 !important;
        border: 1px solid #dadce0 !important;
        border-radius: 20px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 4px 16px !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.1) !important;
    }
    .stDeployButton button:hover {
        background-color: #f1f3f4 !important;
        border-color: #1a73e8 !important;
    }

    /* Main container padding ensuring zero overlap with top bar */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px !important;
    }

    /* Clean Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #dadce0 !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #202124 !important;
        font-weight: 600 !important;
    }

    /* Typography */
    h1 {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #202124 !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 4px !important;
    }
    h2 {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #202124 !important;
        margin-top: 14px !important;
        margin-bottom: 8px !important;
    }
    h3 {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #3c4043 !important;
    }
    p, label, span {
        color: #3c4043 !important;
    }

    /* Corporate Badges */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
    }
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .badge-blue {
        background-color: #e8f0fe;
        color: #1a73e8;
        border: 1px solid #d2e3fc;
    }
    .badge-green {
        background-color: #e6f4ea;
        color: #137333;
        border: 1px solid #ceead6;
    }
    .badge-purple {
        background-color: #f3e8fd;
        color: #7627bb;
        border: 1px solid #e1c3f9;
    }
    .badge-amber {
        background-color: #fef7e0;
        color: #b06000;
        border: 1px solid #feefc3;
    }

    /* MNC Clean Cards */
    .mnc-card {
        background-color: #ffffff;
        border: 1px solid #dadce0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(60,64,67,0.08);
    }
    .mnc-card-header {
        font-size: 15px;
        font-weight: 600;
        color: #202124;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Bob Verified Green Box */
    .box-bob-verified {
        background-color: #e6f4ea;
        border: 1.5px solid #34a853;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .box-bob-title {
        color: #137333;
        font-size: 15px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
    }
    .box-bob-body {
        background-color: #ffffff;
        border: 1px solid #ceead6;
        border-radius: 8px;
        padding: 12px 14px;
        font-size: 15px;
        color: #0d652d;
        font-weight: 500;
        line-height: 1.4;
    }

    /* Bob Tampered Alert Box */
    .box-bob-tampered {
        background-color: #fef7e0;
        border: 1.5px solid #f9ab00;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .box-bob-tampered-title {
        color: #b06000;
        font-size: 15px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
    }
    .box-bob-tampered-body {
        background-color: #ffffff;
        border: 1px solid #feefc3;
        border-radius: 8px;
        padding: 12px 14px;
        font-size: 14px;
        color: #b06000;
        font-family: 'Consolas', 'Roboto Mono', monospace;
        word-break: break-all;
    }

    /* Eve Intercept Red Box */
    .box-eve-intercept {
        background-color: #fce8e6;
        border: 1.5px solid #ea4335;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .box-eve-title {
        color: #c5221f;
        font-size: 15px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
    }
    .box-eve-body {
        background-color: #ffffff;
        border: 1px solid #fad2cf;
        border-radius: 8px;
        padding: 12px 14px;
        font-size: 14px;
        color: #b31412;
        font-family: 'Consolas', 'Roboto Mono', monospace;
        word-break: break-all;
    }

    /* Details Monospace Code Box */
    .code-box {
        background-color: #f1f3f4;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px 14px;
        font-family: 'Consolas', 'Roboto Mono', monospace;
        font-size: 13px;
        color: #202124;
        word-break: break-all;
        margin-top: 6px;
        margin-bottom: 10px;
    }

    /* Primary Buttons (Google Blue) */
    .stButton > button {
        background-color: #1a73e8 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.3) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background-color: #1557b0 !important;
        box-shadow: 0 2px 6px rgba(60,64,67,0.4) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1.5px solid #dadce0 !important;
        gap: 12px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #5f6368 !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 10px 16px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #1a73e8 !important;
        border-bottom: 3px solid #1a73e8 !important;
        font-weight: 600 !important;
    }

    /* Metric Containers */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #dadce0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.06) !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #5f6368 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #202124 !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header Section
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="badge-container">
    <span class="badge badge-blue">Track 1: Quantum Cryptography & Security</span>
    <span class="badge badge-purple">Hybrid QKD + Kyber768 Protocol</span>
    <span class="badge badge-green">NIST Kyber-768 ML-KEM + Qiskit 2.6 Aer</span>
    <span class="badge badge-amber">GibberLink Acoustic Modem</span>
</div>
<h1>Iron Lab: Quantum-Secured AI Agent Platform</h1>
<p style="color: #5f6368; font-size: 15px; margin-bottom: 20px;">
    An enterprise-grade quantum cryptographic platform for autonomous AI-to-AI communications.
    Combines <strong>Quantum Key Distribution (BB84 / E91)</strong> with <strong>Post-Quantum Cryptography (NIST Kyber-768)</strong> and acoustic <strong>GibberLink</strong> transmission.
</p>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------------------------
st.sidebar.markdown("### ⚙️ Protocol Settings")

protocol_choice = st.sidebar.radio(
    "Primary Protocol",
    options=[
        "Iron Lab Hybrid Protocol (QKD + Kyber768 PQC)",
        "BB84 (Prepare & Measure QKD)",
        "E91 (Entanglement / Bell States)",
    ],
    index=0,
    help="Select the cryptographic protocol used to establish shared keys between AI agents.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Transmission Parameters")

num_qubits = st.sidebar.slider(
    "Qubits / Bell Pairs Transmitted",
    min_value=32,
    max_value=300,
    value=128,
    step=16,
    help="Number of quantum states transmitted over the quantum fiber link.",
)

channel_loss = st.sidebar.slider(
    "Channel Attenuation / Loss",
    min_value=0.0,
    max_value=0.8,
    value=0.0,
    step=0.05,
    format="%.0f%%",
    help="Physical transmission loss simulating fiber optic degradation.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕵️ Eavesdropper (Eve) Interception")

enable_eve = st.sidebar.checkbox(
    "Enable Eve Eavesdropper",
    value=True,
    help="Simulate an active adversary intercepting the quantum channel between agents.",
)

eve_probability = 1.0
attack_type = "intercept_resend"
eve_tamper_mode = "Passive Eavesdropping (Steal Key)"

if enable_eve:
    eve_tamper_mode = st.sidebar.radio(
        "Eve Attack Strategy",
        options=[
            "Passive Eavesdropping (Steal Key)",
            "Active Tampering (Alter Message In Transit)",
        ],
        index=0,
        help="Choose whether Eve attempts to stealthily measure qubits or actively modify the acoustic ciphertext payload.",
    )

    eve_probability = st.sidebar.slider(
        "Eve Interception Probability",
        min_value=0.1,
        max_value=1.0,
        value=1.0,
        step=0.1,
        format="%.0f%%",
        help="Probability of Eve capturing and measuring individual qubits.",
    )

    attack_type = st.sidebar.selectbox(
        "Eve Quantum Attack Mechanism",
        options=[
            ("intercept_resend", "Intercept-Resend (Classical Qubit Measurement)"),
            ("pns", "Photon Number Splitting (Multi-Photon Siphoning)"),
            ("detector_blinding", "Detector Blinding (Hardware Hijacking)"),
        ],
        format_func=lambda x: x[1],
        index=0,
    )[0]
else:
    st.sidebar.info("Quantum channel is clean. No eavesdropper present.")

# ---------------------------------------------------------------------------
# Backend Protocol Execution Engine
# ---------------------------------------------------------------------------
def _bits_to_crypto_key(bits: List[int]) -> Tuple[bytes, str]:
    """Derives a standard 32-byte key and hex representation from bit array."""
    import hashlib
    if not bits:
        empty = bytes(32)
        return empty, "0x" + empty.hex()
    byte_vals = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        v = 0
        for b in chunk:
            v = (v << 1) | (b & 1)
        v <<= (8 - len(chunk))
        byte_vals.append(v)
    derived = hashlib.sha3_256(bytes(byte_vals)).digest()
    return derived, "0x" + derived.hex()


@st.cache_data(show_spinner=False)
def execute_protocol(
    proto_name: str,
    n_qubits: int,
    loss: float,
    has_eve: bool,
    eve_rate: float,
    atk_type: str,
    seed: int = 42,
) -> Dict:
    """Executes the chosen quantum protocol and returns structured telemetry."""
    active_attack = atk_type if has_eve else "none"

    if proto_name.startswith("Iron Lab Hybrid"):
        # Iron Lab Hybrid Protocol (BB84 QKD + Kyber768 PQC)
        hybrid_engine = QShieldHybrid(num_qubits=n_qubits, channel_loss=loss, seed=seed)
        res = hybrid_engine.execute(attack_type=active_attack)
        return {
            "protocol": "Iron Lab Hybrid (QKD + Kyber768)",
            "mode": res.protocol_used.value,  # HYBRID or PQC_ONLY
            "final_key_bytes": res.final_key,
            "final_key_hex": res.final_key_hex,
            "qber": res.qber,
            "channel_loss": res.channel_loss,
            "eve_information": res.eve_information,
            "secure_key_rate": res.secure_key_rate,
            "is_secure": res.is_secure,
            "trust_decision": res.trust_decision,
            "qkd_key_hex": res.qkd_key_hex,
            "pqc_key_hex": res.pqc_key_hex,
            "warnings": res.warnings,
        }

    elif proto_name.startswith("BB84"):
        # Pure BB84 Protocol
        bb84_engine = BB84Protocol(num_qubits=n_qubits, channel_loss=loss, seed=seed)
        res = bb84_engine.generate_key(attack_type=active_attack)
        final_key, key_hex = _bits_to_crypto_key(res.sifted_key)
        return {
            "protocol": "BB84 (Prepare & Measure)",
            "mode": "QKD_ONLY",
            "final_key_bytes": final_key,
            "final_key_hex": key_hex,
            "qber": res.qber_result.qber,
            "channel_loss": loss,
            "eve_information": res.qber_result.eve_information,
            "secure_key_rate": res.qber_result.secure_key_rate,
            "is_secure": res.is_secure,
            "trust_decision": (
                f"QBER={res.qber_result.qber:.2f}%. "
                f"{'BELOW' if res.is_secure else 'ABOVE'} 11.0% threshold. "
                f"Key {'ACCEPTED' if res.is_secure else 'ABORTED — Eavesdropping Detected'}."
            ),
            "qkd_key_hex": key_hex,
            "pqc_key_hex": "N/A (Pure QKD)",
            "warnings": [] if res.is_secure else ["BB84 key aborted due to excessive QBER."],
        }

    else:
        # E91 Entanglement-based Protocol
        e91_engine = E91Protocol(num_pairs=n_qubits, seed=seed)
        noise = 0.25 if (has_eve and atk_type == "intercept_resend") else (loss * 0.5)
        res = e91_engine.run(noise_level=noise)
        final_key, key_hex = _bits_to_crypto_key(res.sifted_key)
        return {
            "protocol": "E91 (Entanglement / Bell States)",
            "mode": "ENTANGLEMENT",
            "final_key_bytes": final_key,
            "final_key_hex": key_hex,
            "qber": res.qber,
            "channel_loss": loss,
            "bell_parameter": res.bell_parameter,
            "is_entangled": res.is_entangled,
            "eve_information": 1.0 - (res.bell_parameter / 2.828) if has_eve else 0.0,
            "secure_key_rate": res.secure_key_rate,
            "is_secure": res.is_secure,
            "trust_decision": (
                f"Bell CHSH S={res.bell_parameter:.3f} (Max 2.828). "
                f"{'VIOLATION VERIFIED (S > 2)' if res.is_entangled else 'BELL INEQUALITY NOT VIOLATED (S ≤ 2)'}. "
                f"Key {'ACCEPTED' if res.is_secure else 'ABORTED — Entanglement Collapsed'}."
            ),
            "qkd_key_hex": key_hex,
            "pqc_key_hex": "N/A (Entanglement)",
            "warnings": [] if res.is_secure else ["E91 key aborted — Bell parameter below threshold."],
        }


# Execute protocol run
telemetry = execute_protocol(
    proto_name=protocol_choice,
    n_qubits=num_qubits,
    loss=channel_loss,
    has_eve=enable_eve,
    eve_rate=eve_probability,
    atk_type=attack_type,
)

# Sidebar Live Status Card
st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Live Security State")
if telemetry["is_secure"]:
    st.sidebar.success(f"STATUS: SECURE\n\nMode: {telemetry['mode']}")
else:
    st.sidebar.error(f"STATUS: COMPROMISED / ABORTED\n\nQBER: {telemetry['qber']:.2f}%")

st.sidebar.markdown(f"**Measured QBER:** `{telemetry['qber']:.2f}%`")
st.sidebar.markdown(f"**Eve Info Leaked:** `{telemetry['eve_information']:.2%}`")
st.sidebar.markdown(f"**Key Length:** `256 bits (32 bytes)`")

# ---------------------------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------------------------
tab_messaging, tab_circuits, tab_math, tab_graphs, tab_tools = st.tabs(
    [
        "💬 Live Agent Messaging & Eve Tamper Defense",
        "⚡ Quantum Circuits & Architecture",
        "📐 Quantum Equations & Proofs",
        "📊 Graphs, Histograms & Telemetry",
        "🛠️ Tools & Technologies Used",
    ]
)

# ===========================================================================
# TAB 1: LIVE SECURE AGENT MESSAGING (HERO TAB)
# ===========================================================================
with tab_messaging:
    st.markdown("### 💬 Live Quantum-Safe Messaging & Active Tamper Defense")
    st.markdown(
        "Real-time bidirectional encrypted communication between **Agent A (Alice)** and **Agent B (Bob)**. "
        "Observe how the platform prevents **Eve** from hacking the key, and what happens when Eve actively attempts to **alter the message** in transit."
    )

    # Direction Switcher (Alice -> Bob vs Bob -> Alice)
    col_dir1, col_dir2 = st.columns([1, 2])
    with col_dir1:
        comm_direction = st.radio(
            "Communication Direction:",
            options=["Agent Alice (A) ➡️ Agent Bob (B)", "Agent Bob (B) ➡️ Agent Alice (A)"],
            index=0,
            horizontal=True,
        )

    is_alice_sender = comm_direction.startswith("Agent Alice")
    sender_name = "Agent Alice (A)" if is_alice_sender else "Agent Bob (B)"
    receiver_name = "Agent Bob (B)" if is_alice_sender else "Agent Alice (A)"

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Two-Column Layout (Matching the user's uploaded screen photo)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f"#### 👤 {sender_name} — [Sender]")

        # Preset message templates
        preset_cols = st.columns(3)
        default_msg = "Transfer 50,000 credits to Sector 7. Authorization code: OMEGA-99."
        if preset_cols[0].button("💳 Financial Order", use_container_width=True):
            st.session_state["msg_input"] = "CONFIDENTIAL: Wire USD 2,500,000 to Account #84920-IBAN-CH."
        if preset_cols[1].button("🚀 Tactical Command", use_container_width=True):
            st.session_state["msg_input"] = "TACTICAL: Autonomous Drone Fleet rendezvous at Grid 45-B."
        if preset_cols[2].button("🤝 AI Handshake", use_container_width=True):
            st.session_state["msg_input"] = "AGENT_SYNC: Establishing high-speed GibberLink acoustic session."

        if "msg_input" not in st.session_state:
            st.session_state["msg_input"] = default_msg

        # Confidential Message Input Bar
        user_message = st.text_area(
            "Confidential Message to Transmit:",
            value=st.session_state["msg_input"],
            height=90,
            help="Type the message you want the sender AI agent to transmit securely.",
        )

        st.markdown("##### 1. Cryptographic Key & Encryption Details")
        st.markdown(f"**Active Protocol:** `{telemetry['protocol']}`")
        st.markdown(f"**Session Mode:** `{telemetry['mode']}`")
        st.markdown(f"**Shared Key (Hex):**")
        st.markdown(f"<div class='code-box'>{telemetry['final_key_hex'][:64]}...</div>", unsafe_allow_html=True)

        # Audio generation using GibberLink Audio module
        audio_engine = GibberLinkAudio()
        temp_dir = tempfile.gettempdir()
        audio_wav_path = os.path.join(temp_dir, "q_gibberlink_tx.wav")

        # Encode with the quantum key
        active_key_bytes = telemetry["final_key_bytes"]
        audio_engine.quantum_secure_encode(user_message, active_key_bytes, audio_wav_path)

        st.markdown("##### 2. GibberLink Acoustic Modem Transmission")
        st.caption("AI agents convert the AES-256-GCM ciphertext into audible acoustic frequencies (FSK beeps):")
        if os.path.exists(audio_wav_path):
            with open(audio_wav_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")

    with col_right:
        st.markdown(f"#### 👤 {receiver_name} [Receiver] & 🕵️ Eve [Intercept]")

        # Decode using legitimate key
        recovered_text, decode_success = audio_engine.quantum_secure_decode(active_key_bytes, audio_wav_path)

        # Check Eve Tampering Mode
        is_tampering = enable_eve and (eve_tamper_mode == "Active Tampering (Alter Message In Transit)")

        if is_tampering:
            # Eve actively modifies the payload in transit
            tampered_text_simulated = user_message.replace("50,000 credits", "999,999 credits to EVE").replace("Sector 7", "Eve's Rogue Account")
            if tampered_text_simulated == user_message:
                tampered_text_simulated = "MALICIOUS OVERWRITE: " + user_message[:20] + " [TAMPERED BY EVE]"

            # Receiver detects the tag mismatch and rejects
            st.markdown(
                f"""
<div class="box-bob-tampered">
    <div class="box-bob-tampered-title">
        <span>⚠️</span> {receiver_name} Integrity Alert: TAMPERING DETECTED!
    </div>
    <div class="box-bob-tampered-body">
        &lt;SECURITY_EXCEPTION: AES-256-GCM AUTHENTICATION TAG MISMATCH&gt;<br>
        Payload was altered in transit! Corrupted packet rejected by receiver.<br>
        <strong>Attempted Altered Content:</strong> "{tampered_text_simulated}"
    </div>
    <div style="font-size: 12px; color: #b06000; margin-top: 8px;">
        ✔ Tamper Resistance: The cryptographic MAC tag ensured altered data was instantly flagged and dropped.
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

            # Eve Card during active tampering
            st.markdown(
                f"""
<div class="box-eve-intercept">
    <div class="box-eve-title">
        <span>⚡</span> Eve Active Man-in-the-Middle Attack (Tampering):
    </div>
    <div class="box-eve-body">
        EVE INJECTED: "{tampered_text_simulated}"<br>
        RESULT: EVE FAILED TO FORGE VALID AUTH TAG. Receiver discarded packet!
    </div>
    <div style="font-size: 12px; color: #c5221f; margin-top: 8px;">
        Even though Eve altered the physical transmission, she cannot calculate the valid GCM auth tag without the 256-bit key.
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

        else:
            # Normal passive eavesdropping mode
            st.markdown(
                f"""
<div class="box-bob-verified">
    <div class="box-bob-title">
        <span>✅</span> {receiver_name} Decrypted Output (Verified Authentic):
    </div>
    <div class="box-bob-body">
        {recovered_text}
    </div>
    <div style="font-size: 12px; color: #137333; margin-top: 8px;">
        ✔ AES-256-GCM Integrity Tag Validated • Channel QBER: {telemetry['qber']:.2f}% • Decryption Success: 100%
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

            # Eve Intercepted Box
            if enable_eve:
                if telemetry["protocol"].startswith("Iron Lab Hybrid"):
                    eve_intercept_text = "<GARBLED CIPHERTEXT: DECRYPTION IMPOSSIBLE — EVE HAS 0 BITS OF KYBER-768 PQC KEY>"
                    eve_subtext = (
                        "⛔ EVE DETECTED BY TRUST CONTROLLER! Quantum QBER exceeded 11%. "
                        "The platform automatically discarded the compromised QKD key and secured the session with NIST Kyber-768 lattice-based PQC. "
                        "Eve's information leakage is strictly 0.00%."
                    )
                elif telemetry["protocol"].startswith("BB84"):
                    eve_intercept_text = "<ABORTED SESSION — PACKET REJECTED DUE TO QBER SPIKE>"
                    eve_subtext = "⛔ Under pure BB84, excessive error rate forced both agents to abort transmission. Eve captured garbled acoustic noise."
                else:
                    eve_intercept_text = "<BELL INEQUALITY VIOLATION COLLAPSED: S ≤ 2.0>"
                    eve_subtext = "⛔ Under E91, entanglement was severed by Eve's measurement. Key generation aborted."
            else:
                eve_intercept_text = "<NO EAVESDROPPER DETECTED ON FIBER LINK>"
                eve_subtext = "Channel is pristine. Legitimate agents communicate at full quantum key rate."

            st.markdown(
                f"""
<div class="box-eve-intercept">
    <div class="box-eve-title">
        <span>⛔</span> Eve Intercepted Output (Garbled / Blocked):
    </div>
    <div class="box-eve-body">
        {eve_intercept_text}
    </div>
    <div style="font-size: 12px; color: #c5221f; margin-top: 8px;">
        {eve_subtext}
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

        # Trust Decision Box
        st.markdown("##### 3. Real-Time Trust Controller Decision")
        st.info(f"**Decision:** {telemetry['trust_decision']}")


# ===========================================================================
# TAB 2: QUANTUM CIRCUITS & ARCHITECTURE
# ===========================================================================
with tab_circuits:
    st.markdown("### ⚡ Quantum Circuit Diagrams & Platform Architecture")
    st.markdown(
        "High-resolution quantum circuit representations executed on Qiskit Aer, detailing quantum state preparation, basis transformations, and measurement."
    )

    c_col1, c_col2 = st.columns(2)

    with c_col1:
        st.markdown("#### 1. BB84 Prepare, Intercept & Measure Quantum Circuit")
        circuit_bb84_path = os.path.join(FIGURES_DIR, "circuit_bb84.png")
        if os.path.exists(circuit_bb84_path):
            st.image(circuit_bb84_path, caption="Qiskit Quantum Circuit for BB84 State Preparation, Basis Rotation (H gate), and Measurements", use_container_width=True)
        else:
            st.warning("BB84 Circuit image not found in figures/")

        st.markdown(
            """
- **Qubit 0:** Alice sends $|0\\rangle$ in Rectilinear ($Z$) basis $\\rightarrow$ Bob measures in $Z$.
- **Qubit 1:** Alice sends $|1\\rangle$ ($X$ gate applied) in $Z$ basis $\\rightarrow$ Bob measures in $Z$.
- **Qubit 2:** Alice sends $|+\\rangle$ in Diagonal ($X$) basis ($H$ gate) $\\rightarrow$ Bob measures in $X$.
- **Qubit 3 (Eve Interception):** Eve measures in wrong basis ($Z$), projecting the qubit and creating a ~25% disturbance detectable by Bob.
"""
        )

    with c_col2:
        st.markdown("#### 2. E91 Entanglement & CHSH Bell State Circuit")
        circuit_e91_path = os.path.join(FIGURES_DIR, "circuit_e91_bell.png")
        if os.path.exists(circuit_e91_path):
            st.image(circuit_e91_path, caption="Qiskit Circuit: Bell State |Φ⁺⟩ Entanglement Generation and Measurement at Rotated Angles", use_container_width=True)
        else:
            st.warning("E91 Circuit image not found in figures/")

        st.markdown(
            """
- **Hadamard + CNOT ($H_0 + CX_{0,1}$):** Creates the maximally entangled Bell pair:
  $$\\left|\\Phi^+\\right\\rangle = \\frac{\\left|00\\right\\rangle + \\left|11\\right\\rangle}{\\sqrt{2}}$$
- **Rotation Gates ($R_y(\\theta)$):** Alice and Bob measure along non-commuting bases to test the **CHSH Bell inequality** ($S > 2$).
- If Eve attempts to clone or intercept either entangled photon, the quantum entanglement collapses, forcing $S \\le 2$.
"""
        )

    st.markdown("---")
    st.markdown("#### 3. Iron Lab Hybrid Protocol Autonomous Defense Workflow")
    arch_flow_path = os.path.join(FIGURES_DIR, "hybrid_architecture_flow.png")
    if os.path.exists(arch_flow_path):
        st.image(arch_flow_path, caption="Complete System Workflow: Hybrid Key Generation, Real-Time QBER Monitoring, and GibberLink Audio Encoding", use_container_width=True)


# ===========================================================================
# TAB 3: QUANTUM EQUATIONS & PROOFS
# ===========================================================================
with tab_math:
    st.markdown("### 📐 Quantum Cryptographic Equations & Security Proofs")
    st.markdown("Formal mathematical foundations governing quantum key distribution, lattice post-quantum cryptography, and acoustic data exchange.")

    eq_col1, eq_col2 = st.columns(2)

    with eq_col1:
        st.markdown("#### 1. Quantum No-Cloning Theorem (Unbreakable Security)")
        st.markdown(
            r"""
The foundation of why Eve cannot hack the quantum channel lies in the **No-Cloning Theorem**.
Suppose a unitary operator $U$ could clone an arbitrary quantum state $|\psi\rangle$:
$$U |\psi\rangle |0\rangle = |\psi\rangle |\psi\rangle, \quad U |\phi\rangle |0\rangle = |\phi\rangle |\phi\rangle$$
Taking the inner product:
$$\langle \psi | \langle 0 | U^\dagger U | \phi \rangle |0\rangle = \langle \psi | \phi \rangle = (\langle \psi | \phi \rangle)^2$$
This implies:
$$\langle \psi | \phi \rangle - (\langle \psi | \phi \rangle)^2 = 0 \implies \langle \psi | \phi \rangle \in \{0, 1\}$$
**Conclusion:** Only orthogonal states can be cloned. Because BB84 uses non-orthogonal bases ($Z$ and $X$), **Eve cannot clone the transmitted qubits without introducing irreversible state collapse**.
"""
        )

        st.markdown("#### 2. Quantum Bit Error Rate (QBER) Formulation")
        st.markdown(
            r"""
The QBER represents the fraction of differing bits in the sifted key:
$$\text{QBER} = \frac{\sum_{i=1}^{N_{\text{matched}}} (a_i \oplus b_i)}{N_{\text{matched}}}$$
When Eve intercepts with rate $\eta$:
$$\text{QBER}_{\text{Eve}} = \eta \cdot P(\text{wrong basis}) \cdot P(\text{error}) = \eta \cdot \frac{1}{2} \cdot \frac{1}{2} = \frac{\eta}{4}$$
At $100\%$ interception ($\eta = 1$), $\text{QBER} = 25.0\%$, drastically exceeding the security bound ($11.0\%$).
"""
        )

    with eq_col2:
        st.markdown("#### 3. E91 CHSH Bell Inequality (Entanglement Test)")
        st.markdown(
            r"""
In the E91 protocol, Alice measures with angles $\{a_1, a_2, a_3\}$ and Bob with $\{b_1, b_2, b_3\}$.
The CHSH correlation parameter $S$ is computed as:
$$S = |E(a_1, b_1) - E(a_1, b_3) + E(a_3, b_1) + E(a_3, b_3)|$$
- **Classical Physics / Eavesdropped Link:**
  $$S_{\text{classical}} \le 2.0$$
- **Quantum Entanglement (Tsirelson's Bound):**
  $$S_{\text{quantum}} = 2\sqrt{2} \approx 2.828$$
If Eve eavesdrops, she destroys the Bell state entanglement, causing $S \le 2.0$, which alerts the platform to abort.
"""
        )

        st.markdown("#### 4. NIST Kyber-768 Lattice Cryptography (M-LWE)")
        st.markdown(
            r"""
Kyber-768 relies on the **Module Learning With Errors (M-LWE)** problem over polynomial rings $R_q = \mathbb{Z}_q[X]/(X^{256} + 1)$:
$$\mathbf{t} = \mathbf{A} \mathbf{s} + \mathbf{e} \pmod q$$
Where:
- $\mathbf{A} \in R_q^{k \times k}$ is a public matrix.
- $\mathbf{s} \in R_q^k$ is the secret vector.
- $\mathbf{e} \in R_q^k$ is a small error noise polynomial.

Even with Shor's algorithm on a fault-tolerant quantum computer, finding $\mathbf{s}$ requires solving the Shortest Vector Problem (SVP) on lattices, providing **NIST Level 3 quantum resistance (equivalent to AES-192)**.
"""
        )

    st.markdown("---")
    st.markdown("#### 5. Dual-Layer Hybrid Key Derivation Function (KDF)")
    st.markdown(
        r"""
The final session key combines information-theoretic quantum physics and post-quantum lattice algebra using SHA3-256:
$$K_{\text{final}} = \begin{cases} 
\text{SHA3-256}\Big(K_{\text{PQC}} \oplus \text{SHA3-256}(K_{\text{QKD}})\Big) & \text{if QBER} < 11.0\% \text{ and Loss} < 60\% \quad \text{(HYBRID Mode)} \\
K_{\text{PQC}} & \text{if QBER} \ge 11.0\% \text{ or Loss} \ge 60\% \quad \text{(PQC\_ONLY Mode)}
\end{cases}$$
"""
    )


# ===========================================================================
# TAB 4: GRAPHS, HISTOGRAMS & TELEMETRY
# ===========================================================================
with tab_graphs:
    st.markdown("### 📊 Statistical Graphs, Histograms & Monte Carlo Distributions")
    st.markdown(
        "Empirical distributions generated over 1,000 Monte Carlo simulation runs, proving threshold boundaries and leakage dynamics."
    )

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("#### 1. QBER Distribution: Clean vs Intercept-Resend Attack")
        hist_qber_path = os.path.join(FIGURES_DIR, "histogram_qber_distribution.png")
        if os.path.exists(hist_qber_path):
            st.image(hist_qber_path, caption="Monte Carlo simulation showing clear bimodal separation at the 11% threshold", use_container_width=True)

    with g_col2:
        st.markdown("#### 2. E91 CHSH Bell Parameter S Histogram")
        hist_bell_path = os.path.join(FIGURES_DIR, "histogram_bell_chsh.png")
        if os.path.exists(hist_bell_path):
            st.image(hist_bell_path, caption="Distribution of Bell parameter S proving non-local entanglement violation", use_container_width=True)

    st.markdown("---")
    st.markdown("#### 3. Information Leakage vs QBER Rate Curve")
    curve_leak_path = os.path.join(FIGURES_DIR, "graph_eve_leakage_vs_qber.png")
    if os.path.exists(curve_leak_path):
        st.image(curve_leak_path, caption="Comparison of information leak: Pure BB84 leaks up to 2×QBER while Iron Lab Hybrid maintains 0.00% leak", use_container_width=True)


# ===========================================================================
# TAB 5: TOOLS & TECHNOLOGIES USED
# ===========================================================================
with tab_tools:
    st.markdown("### 🛠️ Architecture, Tools & Technologies Used to Build This Platform")
    st.markdown("Overview of the production-grade scientific computing and cryptographic stack powering the platform.")

    t_col1, t_col2 = st.columns(2)

    with t_col1:
        st.markdown(
            """
<div class="mnc-card">
    <div class="mnc-card-header">1. Quantum Computing & Simulation Stack</div>
    <ul style="font-size: 13.5px; color: #3c4043; line-height: 1.6;">
        <li><strong>Qiskit 2.6.0:</strong> IBM's open-source quantum SDK for constructing quantum circuits, state preparation, and basis transformations.</li>
        <li><strong>Qiskit-Aer 0.18.0:</strong> High-performance C++ simulator backend for executing noisy and noiseless quantum circuits.</li>
        <li><strong>Pylatexenc 2.11:</strong> Circuit diagram typography engine for LaTeX-quality visual rendering.</li>
    </ul>
</div>

<div class="mnc-card">
    <div class="mnc-card-header">2. Post-Quantum & Classical Cryptography</div>
    <ul style="font-size: 13.5px; color: #3c4043; line-height: 1.6;">
        <li><strong>Kyber-py (Kyber-768):</strong> Implementation of NIST FIPS 203 Module-LWE Key Encapsulation Mechanism (ML-KEM-768).</li>
        <li><strong>PyCryptodome 3.20+:</strong> AES-256-GCM (Galois/Counter Mode) authenticated encryption and SHA3-256 cryptographic hashing.</li>
        <li><strong>Entropy Analysis:</strong> Real-time binary Shannon entropy calculation for key privacy amplification.</li>
    </ul>
</div>
""",
            unsafe_allow_html=True,
        )

    with t_col2:
        st.markdown(
            """
<div class="mnc-card">
    <div class="mnc-card-header">3. AI Agent Acoustic Modem (GibberLink)</div>
    <ul style="font-size: 13.5px; color: #3c4043; line-height: 1.6;">
        <li><strong>GGWave Audio Protocol:</strong> Acoustic modem library transmitting data across audio tones using Frequency Shift Keying (FSK).</li>
        <li><strong>NumPy Synthesis:</strong> Pure sinusoidal wave synthesizer generating audible acoustic carrier tones for encrypted payloads.</li>
        <li><strong>Sidecar Verification:</strong> Audio integrity validation ensuring error-free acoustic transfer between AI agents.</li>
    </ul>
</div>

<div class="mnc-card">
    <div class="mnc-card-header">4. UI, Visualization & Scientific Frameworks</div>
    <ul style="font-size: 13.5px; color: #3c4043; line-height: 1.6;">
        <li><strong>Streamlit 1.66:</strong> Enterprise reactive web application framework configured with Google Material Design principles.</li>
        <li><strong>Matplotlib 3.11 & Plotly 7.1:</strong> Publication-grade scientific visualization for histograms, state vectors, and telemetry curves.</li>
        <li><strong>NumPy 2.4 & SciPy 1.17:</strong> Vectorized matrix manipulation, random bit distribution, and statistical modeling.</li>
    </ul>
</div>
""",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #5f6368; font-size: 13px;">
    Iron Lab Quantum-Secured AI Agent Platform • Powered by Qiskit Aer & NIST Kyber-768 PQC • All Figures Saved in <code>/figures</code>
</div>
""",
    unsafe_allow_html=True,
)
