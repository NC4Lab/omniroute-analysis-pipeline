"""
Script: analysis_csc.py

Purpose:
    Run standalone tests of CSC-related functionality on a single preprocessed session.
    This script loads the first (rat_id, session_name) from the experiment metadata CSV
    and walks through the CSC pipeline: loading from .rec, saving as .dat, and reloading.
"""

# ------------------------------
# Imports and Setup
# ------------------------------

from utils.metadata import ExperimentMetadata, SessionMetadata, EphysMetadata
from utils.io_trodes import (
    load_sample_rate_from_rec,
    load_num_samples_from_rec,
    load_csc_from_rec,
    save_csc_binary,
    load_csc_binary,
)
from utils.omni_anal_logger import omni_anal_logger


# ------------------------------
# Load First Session from ExperimentMetadata
# ------------------------------

omni_anal_logger.info("--- Loading experiment metadata and selecting first session ---")
experiment_meta = ExperimentMetadata()
experiment_meta.load_experiment_metadata_csv()

if not experiment_meta.batch_rat_list:
    raise RuntimeError("No included sessions found in experiment metadata.")

first_entry = experiment_meta.batch_rat_list[0]
rat_id = first_entry["rat_id"]
session_name = first_entry["batch_session_list"][0]

omni_anal_logger.info(f"Selected session: {rat_id}/{session_name}")


# ------------------------------
# Load Metadata
# ------------------------------

# Load session and ephys metadata (assumes they were already created during preprocessing)
session_meta = SessionMetadata(rat_id, session_name)
session_meta.load_or_initialize_pickle(overwrite=False)

ephys_meta = EphysMetadata(rat_id, session_name)
ephys_meta.load_or_initialize_pickle(overwrite=False)


# ------------------------------
# Test 1: Sampling Rate and Sample Count from .rec
# ------------------------------

rec_path = session_meta.rec_path
sampling_rate_hz = ephys_meta.sampling_rate_hz
num_samples = load_num_samples_from_rec(rec_path)
omni_anal_logger.info(f"Sampling rate: {sampling_rate_hz} Hz")
omni_anal_logger.info(f"Total samples in recording: {num_samples}")


# ------------------------------
# Test 2: Load CSC from .rec File
# ------------------------------

omni_anal_logger.info("--- Loading CSC data from .rec ---")
recording = load_csc_from_rec(
    rec_path=rec_path,
    channel_trodes_id=ephys_meta.channel_trodes_id,
    channel_headstage_hardware_id=ephys_meta.channel_headstage_hardware_id,
    trodes_id_include=None  # Load all available channels
)

omni_anal_logger.info(f"Loaded CSC recording with shape: {recording.get_traces().shape}")


# ------------------------------
# Test 3: Save CSC to Binary Files
# ------------------------------

omni_anal_logger.info("--- Saving CSC traces to binary .dat files ---")
save_csc_binary(
    csc_dir=session_meta.csc_dir,
    recording=recording,
    overwrite=True
)


# ------------------------------
# Test 4: Reload CSC Binary Files
# ------------------------------

omni_anal_logger.info("--- Reloading CSC traces from saved binary files ---")
recording_reloaded = load_csc_binary(
    csc_dir=session_meta.csc_dir,
    channel_trodes_id=ephys_meta.channel_trodes_id,
    sampling_rate_hz=ephys_meta.sampling_rate_hz,
    trodes_id_include=None  # Load all channels
)

traces = recording_reloaded.get_traces()
omni_anal_logger.info(f"Reloaded CSC traces shape: {traces.shape}")
omni_anal_logger.info(f"First trace (channel 0) first 10 samples: {traces[:10, 0]}")