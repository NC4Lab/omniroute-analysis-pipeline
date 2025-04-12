"""
Script: preprocessing.py

Purpose:
    Initialize and load experiment-level metadata for batch session preprocessing.
    Eventually will dispatch session-level processing via preprocess_session_start.py.
"""

from utils.metadata import ExperimentMetadata
from utils.omni_anal_logger import omni_anal_logger
from pipeline.preprocess_session_start import (
    setup_session_metadata,
    setup_dio_extraction,
    setup_timestamp_sync,
)

#-----------------------------------------------
# Setup ExperimentMetadata 
#-----------------------------------------------
omni_anal_logger.info(f"=== Initializing ExperimentMetadata ===")

# Initialize ExperimentMetadata instance
exp_meta = ExperimentMetadata()

# Generate experiment_metadata.csv if needed
ExperimentMetadata.initialize_experiment_metadata_csv(
    overwrite=False
)

# Load CSV into memory and group by rat/session
exp_meta.load_experiment_metadata_csv()
omni_anal_logger.info(f"Loaded batch session structure:\n{exp_meta.batch_rat_list}")

#-----------------------------------------------
# Batch session preprocessing
#-----------------------------------------------

for rat_block in exp_meta.batch_rat_list:
    rat_id = rat_block["rat_id"]
    for session_name in rat_block["batch_session_list"]:
        omni_anal_logger.info(f"=== Processing session: {rat_id}/{session_name} ===")

        # Step 1: Generate and save session/ephys metadata
        setup_session_metadata(rat_id, session_name, overwrite=False)

        # Step 2: Extract DIO if needed
        setup_dio_extraction(rat_id, session_name, overwrite=False)

        # Step 3: Compute timestamp sync if needed
        setup_timestamp_sync(rat_id, session_name, dio_channel=2, overwrite=False)