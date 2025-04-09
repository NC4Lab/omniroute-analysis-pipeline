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

The pipeline is built with Python in VS Code and emphasizes:

- Modularity — each function and utility is its own clean unit.
- Integration with SpikeInterface — for filtering, waveform extraction, spike sorting, and curation.
- Use of `.rec` files as the canonical source — avoid unnecessary saving of derived data that can be recomputed.
- Consistent folder and naming convention for all data exports.
- Lightweight logging via `utils/omni_anal_logger.py` — used to visualize the structure and timing of operations.
- Static path resolution — controlled through a `.env` file parsed by `config.py`.
- Use of metadata objects — `SessionMetadata` and `EphysMetadata` — for managing paths, configuration, and shared state between functions.

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