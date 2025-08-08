"""
Script: preprocess_session.py

Purpose:
    Run the per-session preprocessing pipeline for a single session:
      1) Initialize and save SessionMetadata and EphysMetadata
      2) Extract DIO from the .rec/.bag files (as configured in pipeline)
      3) Compute SpikeGadgets↔ROS timestamp synchronization and persist mapping

Prerequisite:
    Ensure your .env is correctly configured (NC4_DATA_DIR, TRODES_DIR).
    This script is typically run before export_csc_to_matlab.py.

Run script:
    python -m experiment.example_experiment.scripts.preprocess_session
"""

from utils.omni_anal_logger import omni_anal_logger
from pipeline.preprocess_session_start import (
    setup_session_metadata,
    setup_dio_extraction,
    setup_timestamp_sync,
)

# ----------------------------
# Session selection (edit these)
# ----------------------------
rat_id = "NC40023"
#session_name = "20250806_164955"
session_name = "20250806_170156"

# ----------------------------
# Pipeline options
# ----------------------------

# DIO channel index used for sync pulses (as per your rig conventions)
dio_channel = 1

# Overwrite existing pickles (.pkl) for SessionMetadata/EphysMetadata
metadata_overwrite = False

# Overwrite previously extracted DIO
dio_overwrite = False

# Overwrite previously computed timestamp sync artifacts
ts_sync_overwrite = False

# Persist binary artifacts for sync (timestamps, fit, diagnostics)
save_ts_binary = False


def main() -> None:
    omni_anal_logger.info("========== PREPROCESS SESSION ==========")
    omni_anal_logger.info(f"Session: {rat_id}/{session_name}")

    # 1) Session/Ephys metadata
    omni_anal_logger.info("Step 1: Initializing session/ephys metadata...")
    setup_session_metadata(rat_id, session_name, overwrite=metadata_overwrite)

    # 2) DIO extraction
    omni_anal_logger.info("Step 2: Extracting DIO...")
    setup_dio_extraction(rat_id, session_name, overwrite=dio_overwrite)

    # 3) Timestamp synchronization
    omni_anal_logger.info("Step 3: Computing timestamp synchronization...")
    setup_timestamp_sync(
        rat_id,
        session_name,
        dio_channel=dio_channel,
        overwrite=ts_sync_overwrite,
        save_ts_binary=save_ts_binary,
    )

    omni_anal_logger.info("========== PREPROCESS COMPLETE ==========")


if __name__ == "__main__":
    main()
