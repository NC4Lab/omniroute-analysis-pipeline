"""
Test: Setup and validate SessionMetadata, EphysMetadata, and CSC loading.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.metadata import SessionMetadata, EphysMetadata
from utils.io_trodes import load_csc_from_rec
from utils.logger import logger

# --- Test parameters ---
rat_id = "NC40008"
session_name = "20250328_134136"

# --- Step 1: Create and save SessionMetadata ---
session = SessionMetadata(rat_id, session_name)
session.load_or_initialize()
logger.log("Initialized SessionMetadata")

# Add custom fields before saving
session.set_custom_field("experimenter", "Ward")
session.set_custom_field("conditions", ["baseline", "stim"])
logger.log("Custom fields set in SessionMetadata")

session.save()
logger.log("SessionMetadata saved")

# --- Step 2: Reload and validate SessionMetadata ---
loaded_session = SessionMetadata(rat_id, session_name)
loaded_session.load_or_initialize()

# Validate built-in fields
assert loaded_session.rat_id == rat_id
assert loaded_session.session_name == session_name

# Validate custom fields
assert loaded_session.custom.experimenter == "Ward"
assert loaded_session.custom.conditions == ["baseline", "stim"]
logger.log("SessionMetadata reload and custom fields validated")

# --- Step 3: Create and save EphysMetadata ---

ephys = EphysMetadata(rat_id, session_name)
ephys.load_or_initialize()
logger.log(f"EphysMetadata initialized: {len(ephys.trodes_id)} channels available")
logger.log(f"Sampling rate: {ephys.sampling_rate_hz:.2f} Hz")

# Add custom fields before saving
ephys.set_custom_field("notch_filter_applied", True)
ephys.set_custom_field("filter_params", {"low": 1, "high": 100})
logger.log("Custom fields set in EphysMetadata")

ephys.save()
logger.log("EphysMetadata saved")

# --- Step 4: Reload and validate EphysMetadata ---
reloaded_ephys = EphysMetadata(rat_id, session_name)
reloaded_ephys.load_or_initialize()

# Validate built-in fields
assert reloaded_ephys.sampling_rate_hz == ephys.sampling_rate_hz
assert reloaded_ephys.trodes_id == ephys.trodes_id
assert reloaded_ephys.trodes_id_include == ephys.trodes_id_include

# Validate custom fields
assert reloaded_ephys.custom.notch_filter_applied is True
assert reloaded_ephys.custom.filter_params == {"low": 1, "high": 100}
logger.log("EphysMetadata reload and custom fields validated")

# --- Step 5: Load CSC data and assign directly ---
hardware_ids = ephys.trodes_to_headstage_ids(ephys.trodes_id_include)
ephys.raw_csc_data = load_csc_from_rec(
    rec_path=loaded_session.rec_path,
    trodes_id_include=hardware_ids,  # now correctly mapped and string-typed
)

# --- Step 6: Validate CSC structure ---
assert ephys.raw_csc_data is not None
num_channels = ephys.raw_csc_data.get_num_channels()
num_frames = ephys.raw_csc_data.get_num_frames()
assert num_channels == len(ephys.trodes_id_include)
logger.log(f"Loaded CSC data: {num_channels} channels x {num_frames} samples")

# --- Done ---
logger.log("All tests passed.")
