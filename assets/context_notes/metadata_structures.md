# Metadata Class Overview

This document summarizes the core metadata classes used in the omniroute_analysis pipeline. Each class serves a specific purpose in organizing session-specific or experiment-level configuration, derived paths, and data context. The classes are serialized to disk for reuse and are designed to support reproducible, metadata-driven workflows across SpikeGadgets `.rec` files, ROS `.bag` files, and related derived data.

All these classes are stored in `utils\metadata.py`.

These objects are designed to load and propagate context, but should not be passed  
directly into utility functions. Instead, extract the specific values those functions need  
(e.g., `sampling_rate_hz`, `timestamp_mapping`, etc.).

## BaseMetadata

All metadata classes inherit from `BaseMetadata`, which provides:

- Serialization to and from `.pkl` files
- Version tagging with git hash and processing timestamp
- A `.custom` field (a `SimpleNamespace`) for arbitrary user-defined fields  
  (e.g., `meta.custom.my_flag = True`). This is useful for interactive workflows  
  but is **not used in `ExperimentMetadata`**, which is CSV-based.

## SessionMetadata

The `SessionMetadata` class captures session-level information, including resolved paths, session type (e.g., "ephys" or "behaviour"), and any user-defined fields. It is the first metadata object initialized in any session workflow and is saved as a pickle file within the session’s `processed/` directory.

This object determines the structure and classification of a session and exposes its root directories and file locations for all downstream tools to use.

## EphysMetadata

The `EphysMetadata` class stores information specific to electrophysiological recordings. It is initialized only if the session contains a `.rec` file (i.e., is classified as `"ephys"`). It handles channel mapping, dynamic channel inclusion masks, sample rate extraction, and timestamp alignment metadata.

It is derived from the per-rat channel map CSV and the `.rec` file, and supports utilities to convert Trodes IDs into SpikeInterface-compatible hardware IDs.

Like `SessionMetadata`, it is serialized to a pickle file and saved within the session's `processed/` directory.

## ExperimentMetadata

The `ExperimentMetadata` class is used to define and manage experiment-level batch processing scope. It loads and manipulates a CSV file (`experiment_metadata.csv`) that resides inside each experiment folder. This file specifies which `(rat_id, session_name)` pairs are to be included in a given experiment’s batch processing workflow and also includes an `include` column.

Typical use includes:
- Initializing a list of all available sessions by scanning the raw data directory
- Marking which sessions should be included or excluded from processing
- Loading or filtering that list as input to a script or notebook

Unlike `SessionMetadata` and `EphysMetadata`, `ExperimentMetadata` is not per-session and is not serialized as a pickle file. It is designed to operate over many sessions and support clean, reproducible experiment boundaries.

## Notes on Usage

- Metadata classes should not be passed directly into downstream functions. Instead, pass the specific values (e.g., sampling rate, timestamp map) those functions require.
- Metadata is the **single source of truth** for all file paths, parameters, and structural info across the pipeline.
- Avoid hardcoding paths or values in analysis scripts; instead, load and query the appropriate metadata object.

