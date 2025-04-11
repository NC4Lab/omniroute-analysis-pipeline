"""
Module: preprocess_session_start.py

Purpose:
    This module performs initial preprocessing steps required to prepare a session for analysis.
    It includes initialization of session-level and electrophysiology metadata, extraction of
    digital input (DIO) event files, and computation of timestamp alignment between SpikeGadgets
    and ROS timebases. These steps establish the core context—file paths, session type, channel
    metadata, sampling rate, and timebase mapping—that are required for all downstream processing
    and analysis stages.
"""

from pathlib import Path
from utils.metadata import SessionMetadata, EphysMetadata
from utils.path import (
    get_rec_path,
    get_dio_dir,
    get_rosbag_path,
)
from utils.io_trodes import extract_dio_from_rec
from utils.ts_sync import compute_ts_sync_parameters
from utils.omni_anal_logger import omni_anal_logger


def setup_session_metadata(rat_id: str, session_name: str, overwrite: bool = False) -> None:
    """
    Initialize and save SessionMetadata and, if applicable, EphysMetadata for a given session.

    Parameters:
        rat_id (str): Unique animal ID (e.g., "NC40008")
        session_name (str): Session folder name (e.g., "20250328_134136")
        overwrite (bool): If True, overwrite existing metadata pickle files

    Returns:
        None
    """
    omni_anal_logger.info(f"--- Setting up metadata for session: {rat_id}/{session_name} ---")

    session = SessionMetadata(rat_id, session_name)
    session.load_or_initialize()
    session.save_pickle(overwrite=overwrite)
    omni_anal_logger.info("SessionMetadata initialized and saved")

    if session.session_type == "ephys":
        ephys = EphysMetadata(rat_id, session_name)
        ephys.load_or_initialize()
        ephys.save_pickle(overwrite=overwrite)
        omni_anal_logger.info("EphysMetadata initialized and saved")
    else:
        omni_anal_logger.info("Session type is not 'ephys' — skipping EphysMetadata setup")

    omni_anal_logger.info(f"--- Metadata setup complete for session: {rat_id}/{session_name} ---")


def setup_dio_extraction(rat_id: str, session_name: str, overwrite: bool = False) -> None:
    """
    Extract DIO event channel files from a .rec file using SpikeGadgets exportdio.

    Parameters:
        rat_id (str): Unique animal ID
        session_name (str): Session folder name
        overwrite (bool): If True, force re-extraction even if DIO folder exists

    Returns:
        None
    """
    dio_dir = get_dio_dir(rat_id, session_name)
    rec_path = get_rec_path(rat_id, session_name)

    if dio_dir.exists() and not overwrite:
        omni_anal_logger.warning(f"DIO directory already exists at {dio_dir} — skipping extraction.")
        return

    extract_dio_from_rec(rec_path=rec_path, dio_dir=dio_dir, overwrite=overwrite)
    omni_anal_logger.info("DIO extraction complete.")


def setup_timestamp_sync(rat_id: str, session_name: str, dio_channel: int = 2, overwrite: bool = False) -> None:
    """
    Compute and save timestamp synchronization parameters between SpikeGadgets and ROS timebases.

    Parameters:
        rat_id (str): Unique animal ID
        session_name (str): Session folder name
        dio_channel (int): DIO channel to use for sync pulse detection (default = 2)
        overwrite (bool): If True, overwrite existing timestamp_mapping in metadata

    Returns:
        None
    """
    omni_anal_logger.info(f"--- Starting timestamp sync for session: {rat_id}/{session_name} ---")

    session = SessionMetadata(rat_id, session_name)
    session.load_or_initialize()

    if session.session_type != "ephys":
        omni_anal_logger.info("Session type is not 'ephys' — skipping timestamp synchronization.")
        return

    ephys = EphysMetadata(rat_id, session_name)
    ephys.load_or_initialize()

    if ephys.timestamp_mapping is not None and not overwrite:
        omni_anal_logger.warning("Timestamp sync already computed — skipping (use overwrite=True to force).")
        return

    dio_dir = get_dio_dir(rat_id, session_name)
    rec_path = get_rec_path(rat_id, session_name)
    rosbag_path = get_rosbag_path(rat_id, session_name)

    # Ensure DIO has been extracted
    extract_dio_from_rec(rec_path=rec_path, dio_dir=dio_dir, dio_channel=dio_channel, overwrite=overwrite)

    # Compute and store sync parameters
    sync_mapping = compute_ts_sync_parameters(
        dio_path=dio_dir,
        sampling_rate_hz=ephys.sampling_rate_hz,
        rosbag_path=rosbag_path,
    )

    ephys.timestamp_mapping = sync_mapping
    ephys.save_pickle(overwrite=overwrite)

    omni_anal_logger.info("Timestamp sync parameters saved to EphysMetadata")
    omni_anal_logger.info(f"Sync polyfit: {sync_mapping['poly_coeffs']}, R² = {sync_mapping['r_squared']:.5f}")
    omni_anal_logger.info(f"--- Timestamp sync complete for session: {rat_id}/{session_name} ---")
