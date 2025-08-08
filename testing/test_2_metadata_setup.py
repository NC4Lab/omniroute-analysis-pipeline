"""
Test: Setup and validate SessionMetadata, EphysMetadata, and CSC loading.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.metadata import SessionMetadata, EphysMetadata
from utils.io_trodes import load_csc_from_rec
from utils.omni_anal_logger import omni_anal_logger

# --- Test parameters ---
rat_id = "NC40008"
session_name = "20250328_134136"

# --- Step 1: Create and save SessionMetadata ---
session = SessionMetadata(rat_id, session_name)
session.load_or_initialize_pickle()
omni_anal_logger.info("Initialized SessionMetadata")

# Add custom fields before saving
session.set_custom_field("experimenter", "Ward")
session.set_custom_field("conditions", ["baseline", "stim"])
omni_anal_logger.info("Custom fields set in SessionMetadata")

session.save_pickle()
omni_anal_logger.info("SessionMetadata saved")

# --- Step 2: Reload and validate SessionMetadata ---
loaded_session = SessionMetadata(rat_id, session_name)
loaded_session.load_or_initialize_pickle()

# Validate built-in fields
assert loaded_session.rat_id == rat_id
assert loaded_session.session_name == session_name

# Validate custom fields
assert loaded_session.custom.experimenter == "Ward"
assert loaded_session.custom.conditions == ["baseline", "stim"]
omni_anal_logger.info("SessionMetadata reload and custom fields validated")

# --- Step 3: Create and save EphysMetadata ---

ephys = EphysMetadata(rat_id, session_name)
ephys.load_or_initialize_pickle()
omni_anal_logger.info(f"EphysMetadata initialized: {len(ephys.channel_trodes_id)} channels available")
omni_anal_logger.info(f"Sampling rate: {ephys.sampling_rate_hz:.2f} Hz")

# Add custom fields before saving
ephys.set_custom_field("notch_filter_applied", True)
ephys.set_custom_field("filter_params", {"low": 1, "high": 100})
omni_anal_logger.info("Custom fields set in EphysMetadata")

ephys.save_pickle()
omni_anal_logger.info("EphysMetadata saved")

# --- Step 4: Reload and validate EphysMetadata ---
reloaded_ephys = EphysMetadata(rat_id, session_name)
reloaded_ephys.load_or_initialize_pickle()

# Validate built-in fields
assert reloaded_ephys.sampling_rate_hz == ephys.sampling_rate_hz
assert reloaded_ephys.channel_trodes_id == ephys.channel_trodes_id

# Validate custom fields
assert reloaded_ephys.custom.notch_filter_applied is True
assert reloaded_ephys.custom.filter_params == {"low": 1, "high": 100}
omni_anal_logger.info("EphysMetadata reload and custom fields validated")

# --- Done ---
omni_anal_logger.info("All tests passed.")
