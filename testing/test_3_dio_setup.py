"""
Test: DIO extraction and loading from .rec file.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np  # Required for validation

from utils.omni_anal_logger import omni_anal_logger
from utils.path import get_rec_path, get_dio_dir
from utils.io_trodes import extract_dio_from_rec, load_dio_binary
from utils.metadata import SessionMetadata, EphysMetadata

# --- Test parameters ---
rat_id = "NC40008"
session_name = "20250328_134136"
overwrite = True
dio_channel = 2

rec_path = get_rec_path(rat_id, session_name)
dio_dir = get_dio_dir(rat_id, session_name)

# --- Setup metadata objects ---
session = SessionMetadata(rat_id, session_name)
session.load_or_initialize()
omni_anal_logger.info("Initialized SessionMetadata")

ephys = EphysMetadata(rat_id, session_name)
ephys.load_or_initialize()
omni_anal_logger.info("Initialized EphysMetadata")

# --- Run DIO extraction ---
extract_dio_from_rec(
    rec_path=rec_path,
    dio_dir=dio_dir,
    overwrite=overwrite,
)
omni_anal_logger.info("DIO extraction complete")

# --- Load a specific DIO channel ---
dio_loader = load_dio_binary(dio_dir, dio_channel)
dio_df = dio_loader.dio  # this is a pandas DataFrame

omni_anal_logger.info(f"Loaded Din{dio_channel} DIO trace: {dio_df.shape[0]} samples")

# --- Validate DIO content ---
assert dio_df["state"].dtype == bool, "DIO trace 'state' column must be boolean"
assert set(dio_df["state"].unique()).issubset({True, False}), "DIO trace must contain only True/False values"
omni_anal_logger.info("DIO trace content validated")

# --- Done ---
omni_anal_logger.info("DIO extraction and loading test passed.")
