"""
Module: path.py

Purpose:
    Utilities for constructing paths and/or resolving metadata.
"""

from pathlib import Path
from utils.config import NC4_DATA_DIR

def get_rec_path(rat_id: str, session_name: str) -> Path:
    return (
        Path(NC4_DATA_DIR) /
        rat_id /
        session_name /
        "raw" /
        "Trodes" /
        f"{session_name}_merged.rec"
    )

def get_rat_path(rat_id: str) -> Path:
    return Path(NC4_DATA_DIR) / rat_id

def get_extracted_dir(rat_id: str, session_name: str) -> Path:
    return get_rat_path(rat_id) / session_name / "extracted"

def get_rosbag_path(rat_id: str, session_name: str) -> Path:
    ros_dir = get_rat_path(rat_id) / session_name / "raw" / "ROS"

    bag_files = list(ros_dir.glob("*.bag"))
    if not bag_files:
        raise FileNotFoundError(f"No .bag file found in: {ros_dir}")

    return bag_files[0]

def get_session_metadata_path(rat_id: str, session_name: str) -> Path:
    return get_extracted_dir(rat_id, session_name) / "session_metadata.pkl"

def get_ephys_metadata_path(rat_id: str, session_name: str) -> Path:
    return get_extracted_dir(rat_id, session_name) / "ephys_metadata.pkl"

def get_ephys_channel_map_path(rat_id: str) -> Path:
    return get_rat_path(rat_id) / "ephys_channel_map_metadata.csv"

def get_dio_dir(rat_id: str, session_name: str) -> Path:
    return get_extracted_dir(rat_id, session_name) / f"{session_name}.DIO"

def get_spike_dir(rat_id: str, session_name: str) -> Path:
    return get_extracted_dir(rat_id, session_name) / f"{session_name}.spikes"