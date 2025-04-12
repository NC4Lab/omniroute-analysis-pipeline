# Overview

This pipeline provides a modular framework for processing, synchronizing and analyzing multimodal neuroscience data, including SpikeGadgets `.rec` files and ROS `.bag` files. It supports continuous signals (CSC), spike sorting, and event-aligned behavioral data, unifying all streams into a shared timebase. Built around fixed lab conventions, it emphasizes reproducibility, metadata-driven organization, and clean workflow orchestration.

---

## Data Types

- CSC (LFP-like) traces from `.rec`
- Sorted spikes (via SpikeInterface)
- Digital sync events from both `.rec` and `.bag`
- Timebase mapping between SpikeGadgets and ROS

---

## Pipeline Structure

- **`utils/`** — Reusable low-level functions for I/O, sync, metadata, logging
- **`pipeline/`** — Session-level orchestration (e.g. metadata setup, timestamp sync)
- **`experiment/`** — Batch-level CSV (`experiment_metadata.csv`) and analysis notebooks
- **`testing/`** — Standalone test scripts
- See `session_level_folder_structure.txt` for per-session layout

---

## Metadata System

Each session is described using serialized metadata objects:

- **SessionMetadata** — Session type and resolved paths
- **EphysMetadata** — Sampling rate, channel maps, timestamp sync
- **ExperimentMetadata** — Batch inclusion via CSV (not serialized)

Metadata objects provide all session context. Do not pass them into utility functions — instead, extract only the values needed (e.g. `sampling_rate_hz`, `timestamp_mapping`, etc.).

---

## Timestamp Synchronization

SpikeGadgets and ROS data streams are aligned using sync pulses. A polynomial fit maps all neural timestamps to the ROS timebase. This mapping is stored in `EphysMetadata`.

---

## Configuration and Environment

- All global paths (e.g. `TRODES_DIR`, `NC4_DATA_DIR`) are set in a `.env` file and loaded via `config.py`
- File and folder paths are resolved consistently using `path.py`
- Version info (git hash + processing timestamp) is stored alongside all outputs using `versioning.py`
- Logging is handled through `omni_anal_logger` for structured, timestamped output

---

## Principles

- Not general-purpose — built for a fixed environment
- Hardcoded structure is fine if it's clean and consistent
- Emphasize clarity, not flexibility
- Prefer small, testable functions
- Metadata is the single source of truth
- Derived data is not persisted unless explicitly exported

---

## Reference Files

- `metadata_structures.md` — Metadata object overview
- `STYLE_GUIDE.md` — Code formatting and comment conventions
- `codebase_folder_structure.txt` — High-level repo layout
- `session_level_folder_structure.txt` — Session-level folder layout

## Useful Links

- SpikeInterface repo: [https://github.com/SpikeInterface/spikeinterface?utm_source=chatgpt.com](https://github.com/SpikeInterface/spikeinterface?utm_source=chatgpt.com)