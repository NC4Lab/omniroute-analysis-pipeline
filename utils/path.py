"""
Module: path.py

Purpose:
    Utilities for constructing paths and/or resolving metadata.
"""

from pathlib import Path
from utils.config import NC4_DATA_PATH

def get_rec_path(rat_id: str, session_name: str) -> Path:
    return (
        Path(NC4_DATA_PATH) /
        rat_id /
        session_name /
        "raw" /
        "Trodes" /
        f"{session_name}_merged.rec"
    )

def get_rat_path(rat_id: str) -> Path:
    return Path(NC4_DATA_PATH) / rat_id

def get_extracted_dir(rat_id: str, session_name: str) -> Path:
    return get_rat_path(rat_id) / session_name / "extracted"

def get_session_metadata_path(rat_id: str, session_name: str) -> Path:
    return get_extracted_dir(rat_id, session_name) / "session_metadata.pkl"

def get_ephys_metadata_path(rat_id: str, session_name: str) -> Path:
    return get_extracted_dir(rat_id, session_name) / "ephys_metadata.pkl"

def get_ephys_channel_map_path(rat_id: str) -> Path:
    return get_rat_path(rat_id) / "ephys_channel_map_metadata.csv"