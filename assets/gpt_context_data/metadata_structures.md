Session Metadata Structure
==========================

The SessionMetadata class
-------------------------

The `SessionMetadata` class is always the first metadata object initialized for any session. It encapsulates key session-level information and standardizes paths used throughout the pipeline.

Serialized as: `session_metadata.pkl`  
Location: `<session_dir>/extracted/session_metadata.pkl`

Fields:
- `rat_id` (`str`): e.g., `"NC40008"`
- `session_name` (`str`): e.g., `"20250328_134136"`
- `rec_path` (`Path`): Full path to the `.rec` file, constructed using standard project folder structure.
- `extracted_dir` (`Path`): Path to the `extracted/` directory for outputs.
- `rat_path` (`Path`): Path to the top-level rat directory (used for metadata CSVs).
- `session_type` (`Literal["behaviour", "ephys"]`): Automatically set based on presence of `.rec` file.
  - `"ephys"`: if `.rec` exists
  - `"behaviour"`: otherwise
- `custom_fields` (`dict[str, Any]`): Optional user-defined metadata fields (e.g., experimental conditions).

Behavior:
- Automatically determines and creates `extracted/` directory for ephys sessions.
- Provides a method to add custom metadata:  
  `set_custom_field(key: str, value: Any)`
- Standardized save/load:
  - `.save()`
  - `.load(rat_id: str, session_name: str)`

Construction:

    rat_folder = "NC40008"
    session_folder = "20250328_134136"
    session = SessionMetadata(rat_folder, session_folder)

Ephys Metadata Structure
========================

The EphysMetadata class
------------------------

The `EphysMetadata` class holds all electrophysiological metadata derived from the channel map CSV and associated `.rec` file. It assumes that a valid `SessionMetadata` instance has already been created and saved.

Serialized as: `ephys_metadata.pkl`  
Location: `<session_dir>/extracted/ephys_metadata.pkl`

This constructor:

- Loads the channel map from `<rat_dir>/ephys_channel_map_metadata.csv`
- Extracts `sampling_rate_hz` from the `.rec` file
- Initializes all non-excluded channels from the map as available
- Sets `trodes_id_include` to match all available channels by default

Fields:
- `trodes_id` (`list[int]`): List of all non-excluded channels defined in the channel map
- `headstage_hardware_id` (`list[int]`): Corresponding SpikeInterface-compatible channel IDs (as integers)
- `trodes_id_include` (`list[int]`): Dynamic list of trodes IDs selected for use in downstream analysis
- `sampling_rate_hz` (`float`): Inferred from `.rec` file using SpikeInterface
- `timestamp_mapping` (`dict[str, Any] | None`): Data for getting ROS-based timestamps for SpikeGadgets data
  - `"poly_coeffs"`: list of polynomial coefficients for time conversion
  - `"r_squared"`: fit quality metric

Behavior:
- Channel selection is dynamic: users set `trodes_id_include` and call a helper to map to internal hardware IDs
- Provides method to convert any list of `trodes_id` values to `headstage_hardware_id` strings for use in SpikeInterface:
  `trodes_to_headstage_ids(ids: list[int]) -> list[str]`
- Provides helper for allocating output space:
  `.add_empty_processed_array(name: str, csc_dataset: np.ndarray)`
- Standardized save/load (excluding CSC data):
  `.save()`
  `.load(session: SessionMetadata)`

Construction:

    ephys = EphysMetadata(session)

Note about `ephys_channel_map_metadata.csv`
-------------------------------------------

The `ephys_channel_map_metadata.csv` file must be located in the top-level rat folder. It includes:

- `trodes_id`
- `headstage_hardware_id`
- `probe_hardware_id`
- `probe_id`
- `shank_id`
- `shank_site`
- `exclude`

CSC data is always read on demand from the original `.rec` file and is never written to disk outside of temporary analysis output.

General Notes About Classes
========================

These classes should never be used as input arguments to any other funcitons directly. Any data needed from them should be passed as an argument.