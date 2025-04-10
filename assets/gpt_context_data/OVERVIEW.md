Overview of Project
===================

You are helping me develop a neuroscience data analysis pipeline for working with SpikeGadgets `.rec` files and ROS `.bag` files. The goal is to analyze both spike data and continuous LFP-like data (CSC — Continuous Sampled Channels), and to synchronize all data streams into a common timebase using digital sync pulses. This codebase will likely be extended to include behavioral data. The final goal is a modular, efficient, and reproducible pipeline for large-scale neural data processing in Python, designed around SpikeInterface (v0.102.1) and tailored to our lab’s fixed environment and workflows.

Ephys Data
----------

We are using SpikeGadgets wireless headstages and silicon probes, not tetrodes. The main data types of interest are:

- CSC (LFP-like) data from Trodes `.rec` files.
- Spikes (via SpikeInterface sorting modules).
- DIO sync events from both `.rec` and `.bag` files.
- Timebase mappings from SpikeGadgets time to ROS time.

CSC signals are accessed using SpikeInterface. Users reference channels by their `trodes_id` as defined in the channel map metadata CSV. Internally, these are mapped to `headstage_hardware_id` values — the identifiers recognized by SpikeInterface — using a helper method in `EphysMetadata`.

EphysMetadata supports dynamic channel selection through `trodes_id_include`, a maskable list that allows analysis to be performed on a flexible subset of available channels. The full set of channels (defined by `trodes_id`) remains unchanged, and all mappings to SpikeInterface-compatible IDs are handled internally.

Spike sorting will be handled through SpikeInterface-compatible sorter modules (e.g., Kilosort2/3), with waveform feature extraction and curation to follow in downstream analysis notebooks.

Pipeline and Workflow
---------------------

The pipeline is implemented in Python and structured to separate core utilities, user-facing scripts, and session-specific notebooks. It emphasizes:

- Modularity: All core operations are implemented as minimal, testable functions in the `utils/` directory.
- Metadata-driven workflows: `SessionMetadata` and `EphysMetadata` objects propagate session-specific paths, parameters, and configuration.
- Canonical sources: `.rec` files are treated as the authoritative input; derived data is not persisted unless explicitly exported.
- Robust timestamp alignment: Sync pulses are extracted from `.rec` and `.bag` files, then aligned via polynomial mapping and validated.
- Logging: Time-stamped, indented logging is handled via `omni_anal_logger`, providing structure and runtime visibility without external dependencies.
- Config consistency: All global paths (e.g., to SpikeGadgets tools) are loaded from a `.env` file parsed by `config.py`.

### Workflow Execution

- Scripts layer (`scripts/`): Mid-level scripts such as `setup_metadata.py` and `setup_ts_sync.py` provide accessible entry points for initializing sessions and computing sync parameters, without needing to touch internal logic.
- Analysis notebooks (`experiment/`): Jupyter notebooks perform exploratory and publication-ready analysis using the standardized pipeline.
- Core utilities (`utils/`): Low-level components for I/O, metadata, sync alignment, CSC extraction, spike sorting, event parsing and analysis.

This structure supports reproducible, modular, and transparent neuroscience analysis, with clear boundaries between reusable components and user workflows.


Timestamp Synchronization
-------------------------

All data will be aligned to the ROS `.bag` timebase using digital sync pulses embedded in both data streams. This involves:
- Extracting sync pulse onsets from both `.rec` and `.bag` files
- Fitting a polynomial regression model to align SpikeGadgets time to ROS time
- Applying this mapping to spikes, CSC, and any behavioral or event data

Key Design Principles
---------------------

- This codebase is not intended to be general-purpose — it is built around fixed expectations and conventions specific to our lab.
- Simplicity is preferred over flexibility — hardcoded structure is fine if it’s clean.
- Your role is to help write minimal, readable, well-contained functions that follow the architecture I’ve laid out.
- Minimize unnecessary parameters — assume the environment is correctly configured.
- Only rely on `SessionMetadata` for path and context propagation.
- All session directories follow the conventions in `codebase_folder_structure.txt` and `session_level_folder_structure.txt`.

Reference Documents
-------------------

- `metadata_structures.md` — describes the metadata object structures and how they relate to session data.
- `STYLE_GUIDE.md` — outlines code formatting, comment structure, and naming conventions.
- `codebase_folder_structure.txt` — describes the high-level organization of the repo.
- `session_level_folder_structure.txt` — describes per-session directory layout.

Useful Links
------------

- SpikeInterface repo: [https://github.com/SpikeInterface/spikeinterface?utm_source=chatgpt.com](https://github.com/SpikeInterface/spikeinterface?utm_source=chatgpt.com)

General Notes About Classes
========================

Utils Input Convention: Utility functions in utils/ modules should not take metadata classes (e.g., SessionMetadata, EphysMetadata) as arguments. Instead, pass only the minimal required values (e.g., sampling_rate_hz, timestamp_mapping, etc.).