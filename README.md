# Phantom Resense 🧠
## EEG Signal Acquisition and Analysis using Muse 2

**Author:** Biniza Verónica Vázquez Moreno  
**Affiliation:** Tecnológico de Monterrey, Campus Puebla  
**Field:** Robotics Engineering | Brain-Computer Interfaces (BCI)  
**Status:** Ongoing Research Project

---

## 1. Project Overview

This repository documents an ongoing research project focused on the **acquisition, preprocessing, and analysis of EEG signals using the Muse 2 headset**.

The project serves as a technical and scientific exploration of how low-cost, consumer-grade EEG devices can be used for **early-stage Brain-Computer Interface (BCI) research**, with a long-term interest in applications related to **motor intent decoding and assistive technologies**, specially those related to mobility impairemtens caused by limb loss.

Rather than presenting a finalized system, this repository is intentionally structured as a **research log**, capturing milestones, experimental decisions, failures, and insights as they occur.

---

## 2. Research Motivation

My interest in EEG and BCI research lies at the intersection of:

- Neuroengineering and signal processing  
- Accessible neurotechnology  
- Assistive and rehabilitative systems  

Consumer EEG devices such as the Muse 2 present both an opportunity and a challenge:  
while they dramatically lower the barrier to entry, they introduce constraints related to **signal quality, noise, and spatial resolution**.

This project explores what is realistically achievable within those constraints.

---

## 3. Research Objectives

**Primary Objective**
- To design and document a reproducible pipeline for EEG signal acquisition and analysis using the Muse 2 headset.

**Secondary Objectives**
- To explore preprocessing techniques suitable for low-SNR EEG signals.
- To extract interpretable features from EEG and IMU data streams.
- To evaluate simple classification strategies for distinguishing basic cognitive or motor-related states.
- To assess limitations of consumer-grade EEG devices in research contexts.

---

## 4. Research Questions

Some of the guiding questions behind this work include:

- What signal characteristics can be reliably extracted from Muse 2 EEG data?
- How does motion (IMU data) interact with EEG signal quality?
- What preprocessing steps most improve signal interpretability?
- Where does a low-cost EEG system fundamentally fail for BCI purposes?

These questions are refined iteratively as experimentation progresses.

---

## 5. Hardware and Software Stack

**Hardware**
- Muse 2 EEG Headset (EEG + IMU)
- Raspberry Pi / Laptop (data acquisition)

**Software**
- Python  
- muselsl / LSL  
- NumPy, Pandas  
- Scikit-learn  
- Jupyter Notebooks  

---

## 6. Methodology (High-Level)

1. EEG and IMU signal acquisition using Muse 2 via LSL  
2. Data storage in CSV format for offline analysis  
3. Signal preprocessing (filtering, windowing, normalization)  
4. Feature extraction (time-domain and statistical features)  
5. Exploratory classification models for state discrimination  

Detailed methodological notes are documented separately in `/docs`.

---

## 7. Current Milestones

- [x] Muse 2 data acquisition via LSL  
- [x] Raw EEG and IMU data logging  
- [x] Initial feature extraction pipeline  
- [x] Binary state classification (REST vs MOVE)  
- [ ] Multiclass state differentiation  
- [ ] EEG-only classification experiments  
- [ ] Robust evaluation under motion artifacts  

Progress is tracked transparently as part of the research process.

---

## 8. Limitations and Challenges

This project explicitly acknowledges limitations such as:

- Low spatial resolution of Muse 2 EEG channels  
- High sensitivity to motion artifacts  
- Limited access to clinical-grade EEG comparison data  

Understanding these constraints is considered a core research outcome.

---

## 9. Collaborations and Mentorship

This project is conducted independently, with informal guidance and discussions with researchers and engineers interested in:

- Brain-Computer Interfaces  
- Signal processing  
- Assistive robotics  

Future academic collaborations are welcome.

---

## 10. Long-Term Vision

The long-term goal of this research is to contribute toward **accessible BCI systems** that can transition from experimental prototypes to real-world assistive applications in the realm of:
- Assisted mobility: BCI - powered prosthetics, and/or wheelchairs.
- Neuroligical Rehabilitation for chronic pain; special interest in Phantom Limb Pain (PLP).

This repository represents an early, foundational step in that direction.

---

## 11. Contact

If you are interested in discussing this work or potential collaborations:

**Biniza Vázquez Moreno**  
📧 LinkedIn: [www.linkedin.com/in/biniza-vazquez]  
🔗 Email: [binizavazquez@gmail.com]

