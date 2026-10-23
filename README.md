 <div align="center">

# 🛡️ Iron Lab: Q-SHIELD + GibberLink

### **Hybrid Quantum Key Distribution (QKD) & Kyber768 Post-Quantum AI Agent Platform**

**VTU-QFF-HC-0101** &nbsp;|&nbsp; Tier: **Both (Quantum + Classical Application)**

[![Qiskit](https://img.shields.io/badge/Qiskit-1.0+-6929C4?style=for-the-badge&logo=qiskit&logoColor=white)](https://qiskit.org/)
[![Post-Quantum](https://img.shields.io/badge/NIST_PQC-Kyber768_(ML--KEM)-0078D4?style=for-the-badge)](https://csrc.nist.gov/projects/post-quantum-cryptography)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-28%20Passed%20(100%25)-34A853?style=for-the-badge&logo=pytest&logoColor=white)](tests/test_qber.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

<div align="center">

| Attribute | Details |
| :--- | :--- |
| **Team** | **Iron Lab** |
| **Team ID** | **VTU-QFF-HC-0101** |
| **Tier** | **Both** |
| **Repository** | [vtu-hc-iron-lab](https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-iron-lab.git) |
| **Organisation** | [vtu-qiskit-fall-fest-2026](https://github.com/vtu-qiskit-fall-fest-2026) |
| **Event** | **VTU-QFF Hackathon — VTU-Qiskit Fall Fest 2026** |

</div>

---

## 📌 Table of Contents

- [👥 Team Members (GitHub IDs)](#-team-members-github-ids)
- [❓ Problem Statement](#-problem-statement)
- [💡 Proposed Solution](#-proposed-solution)
- [🧩 Approach & Architecture](#-approach--architecture)
- [🔬 Quantum Formulations & Mathematics](#-quantum-formulations--mathematics)
- [🛡️ Attack Marketplace & Threat Defense](#️-attack-marketplace--threat-defense)
- [🛠️ Tech Stack](#️-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 How to Run](#-how-to-run)
- [🧪 Running Test Suite](#-running-test-suite)
- [🔁 How to Push Code](#-how-to-push-code)
- [✅ Submission Checklist](#-submission-checklist)
- [📚 Resources & References](#-resources--references)
- [📄 License](#-license)

---

## 👥 Team Members (GitHub IDs)

| # | Name | GitHub Username | Role |
| :-- | :--- | :--- | :--- |
| 1 | **SAYIL MEHABOOB TORAGAL** | [@p4319592-star](https://github.com/p4319592-star) | _Team Lead & Architecture_ |
| 2 | **SOMAPPA NANDI** | [@darshan2-crypto](https://github.com/darshan2-crypto) | _Quantum Protocols & Developer_ |
| 3 | **SOMALINGAPPA KUMBAR** | NA | _Security Analysis & Developer_ |

---

## ❓ Problem Statement

**Problem:**  
Autonomous AI-to-AI agent workflows communicate across untrusted, multi-tenant public networks and acoustic/ambient environments. Conventional classical cryptography (RSA, ECC, Diffie-Hellman) securing these agent interactions is inherently vulnerable to quantum cryptanalysis via Shor's algorithm (**"Store Now, Decrypt Later"** attacks). While pure Quantum Key Distribution (QKD, e.g., BB84, E91) offers theoretical physical security via the No-Cloning Theorem, real-world QKD is constrained by channel attenuation, physical distance limits, and Denial-of-Service aborts when the Quantum Bit Error Rate (QBER) exceeds 11%. Conversely, pure Post-Quantum Cryptography (PQC) lacks physical tampering detection.

**Why it matters:**  
Next-generation AI agents executing sensitive multi-agent financial settlements, defence communications, and healthcare protocols require **uncompromising zero-trust security**. If an adversary compromises communication keys, synthetic agent communications can be intercepted or maliciously altered. A single cryptographic paradigm is no longer sufficient; systems require **defense-in-depth** that combines physical quantum guarantees with post-quantum mathematical resilience.

**Track / Category:**  
**Tier: Both** · Track: **Quantum Cryptography, Quantum Communications & Quantum-Safe AI Systems**

---

## 💡 Proposed Solution

**Solution:**  
**Iron Lab** presents **Q-SHIELD + GibberLink**: a hybrid quantum-classical security platform for autonomous AI agent communication. The platform integrates:
1. **Q-SHIELD Hybrid Protocol**: A trust-aware controller dynamically pairing Qiskit-simulated Quantum Key Distribution (**BB84** and **E91 Entanglement-based Bell state protocols**) with NIST FIPS 203 **Kyber768 (ML-KEM)** lattice cryptography.
2. **GibberLink Acoustic Modem**: Autonomous AI agent negotiation that detects machine-to-machine interactions and switches communication to acoustic/ultrasonic data-over-sound modem bursts (`ggwave`), authenticated with **AES-256-GCM**.
3. **Attack Marketplace & Quantum Telemetry**: Real-time simulation of quantum and classical attacks (Intercept-Resend, Photon Number Splitting, Detector Blinding, and Active Man-in-the-Middle message tampering) with automatic failover to PQC mode.
4. **Google MNC-Grade Interactive Dashboard**: Real-time bidirectional messaging, quantum circuit visualizations, live CHSH Bell parameter testing, and statistical histograms.

**Key idea:**  
> **Defense-in-depth:** When channel conditions are clean ($QBER < 11\%$), the session key is derived via $K = \text{SHA3-256}(K_{\text{PQC}} \oplus \text{Hash}(K_{\text{QKD}}))$ forcing an adversary to break **both** quantum mechanics and lattice hardness; when an eavesdropper or high attenuation is detected, the trust engine seamlessly fails over to Kyber768 PQC mode with zero session interruption.

**Why this works:**  
- **Dual-Layer Assurance:** Breaking the session key requires simultaneously defeating quantum information limits (No-Cloning Theorem) AND post-quantum lattice shortest vector problems (LWE).
- **Zero-Downtime Resilience:** Unlike brittle standalone QKD networks that completely drop connections when Eve attacks ($QBER \ge 11\%$), Q-SHIELD automatically isolates the quantum link and safeguards agent throughput via Kyber768.
- **Physical Authenticity:** AES-256-GCM verification ensures that active packet tampering by Eve is flagged and rejected at the byte level with 100% cryptographic certainty.

---

## 🧩 Approach & Architecture

```mermaid
flowchart TD
    subgraph AgentLayer["🤖 Autonomous AI Agent Layer"]
        Alice["Agent Alice (A)"]
        Bob["Agent Bob (B)"]
        Handshake{"AI Discovery Handshake"}
        Alice <-->|NLP Pattern Match| Handshake
        Bob <-->|NLP Pattern Match| Handshake
    end

    subgraph TrustEngine["🛡️ Q-SHIELD Trust-Aware Controller"]
        Telemetry["Channel Telemetry: QBER & Attenuation Loss (η)"]
        Decision{"QBER < 11% & Loss < 0.60?"}
        Telemetry --> Decision
    end

    subgraph QuantumLayer["⚛️ Qiskit Quantum Core"]
        BB84["BB84 QKD Simulation (Qiskit Aer)"]
        E91["E91 Bell Entanglement (|Φ⁺⟩ & CHSH S > 2)"]
    end

    subgraph PQCLayer["🔐 Post-Quantum Cryptography"]
        Kyber["Kyber768 (NIST ML-KEM) Key Encapsulation"]
    end

    subgraph KeyDerivation["🔑 Key Derivation & Defense Layer"]
        HybridDerivation["HYBRID Mode: K = SHA3-256( K_PQC ⊕ Hash(K_QKD) )"]
        PQCDefault["PQC_ONLY Mode: K = Kyber768 Shared Secret"]
    end

    subgraph Transport["📡 GibberLink Secure Transport"]
        GCM["AES-256-GCM Payload Encryption & MAC"]
        AudioModem["GGWave Acoustic Modem FSK Audio Transmission"]
    end

    Handshake --> Telemetry
    Decision -- Yes (Clean) --> BB84 & E91
    Decision -- Yes (Clean) --> Kyber
    BB84 & Kyber --> HybridDerivation
    Decision -- No (Eve / Loss) --> Kyber
    Kyber --> PQCDefault
    HybridDerivation --> GCM
    PQCDefault --> GCM
    GCM --> AudioModem
    AudioModem --> Bob
