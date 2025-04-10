"""
Module: io_trodes.py

Purpose:
    Utilities for reading continuous data from SpikeGadgets .rec files using SpikeInterface.
"""

from pathlib import Path
import os
import numpy as np
import subprocess
from typing import Union
import spikeinterface.extractors as se
from spikeinterface import BaseRecording

from utils.omni_anal_logger import omni_anal_logger
from utils.binary_utils import TrodesDIOBinaryLoader
from utils.config import TRODES_DIR

def load_sample_rate_from_rec(rec_path: Path) -> None:
    """
    Load sampling rate from the .rec file and store it in the EphysMetadata.

    Parameters:
        rec_path (Path): Path to the .rec file.
    """
    rec = se.read_spikegadgets(rec_path)
    return rec.get_sampling_frequency()


def load_csc_from_rec(rec_path: Path, trodes_id_include: list[int]) -> None:
    """
    Load CSC data from a .rec file and store it in the EphysMetadata object.

    Parameters:
        rec_path (Path): Path to the .rec file.
        trodes_id_include (list[int]): List of Trodes channel IDs to include.

    Returns:
        BaseRecording: SpikeInterface recording object with selected channels, ready for downstream processing.

    """
    with omni_anal_logger.time_block("Loading CSC data from .rec file"):
        rec = se.read_spikegadgets(rec_path)
        return rec.channel_slice(channel_ids=trodes_id_include)

def extract_dio_from_rec(rec_path: Path, dio_dir: Path, overwrite: bool = False) -> None:
    """
    Extract DIO channels from a .rec file using the SpikeGadgets exportdio tool.

    Parameters:
        rec_path (Path): Path to the .rec file.
        dio_dir (Path): Destination directory to save DIO files.
        overwrite (bool): If True, overwrite existing files. Default is False.
    """
    if dio_dir.exists() and not overwrite:
        omni_anal_logger.info(f"DIO already extracted at {dio_dir}")
        return

    exportdio_exe_path = Path(TRODES_DIR) / "exportdio.exe"
    if not exportdio_exe_path.exists():
        raise FileNotFoundError(f"exportdio.exe not found at {exportdio_exe_path}")

    cmd = [
        str(exportdio_exe_path),
        "-rec", str(rec_path),
        "-outputdirectory", str(dio_dir.parent),
        "-output", dio_dir.stem,  # removes .DIO suffix
    ]

    with omni_anal_logger.time_block("Extracting DIO using exportdio"):
        result = subprocess.run(cmd, capture_output=True, text=True)

    omni_anal_logger.info(f"exportdio stdout:\n{result.stdout}")
    if result.stderr:
        omni_anal_logger.info(f"exportdio stderr:\n{result.stderr}")

    if result.returncode != 0:
        raise RuntimeError(
            f"exportdio.exe failed with return code {result.returncode}.\n"
            f"Command: {' '.join(cmd)}\n"
            f"Stderr:\n{result.stderr}"
        )

def load_dio_binary(dio_dir: Path, channel: int) -> np.ndarray:
    """
    Load a binary DIO trace from a specific channel using TrodesDIOBinaryLoader.

    Parameters:
        dio_dir (Path): Path to the extracted DIO directory.
        channel (int): Channel number to load (e.g., 1 for Din1).

    Returns:
        np.ndarray: 1D array of 0/1 values.
    """
    # Look for a file ending in Din{channel}.dat
    pattern = f"Din{channel}.dat"

    matched_file = None
    for file in dio_dir.iterdir():
        if file.name.endswith(pattern):
            matched_file = file
            break

    if matched_file is None:
        raise FileNotFoundError(f"No Din{channel}.dat file found in {dio_dir}")

    with omni_anal_logger.time_block(f"Loading DIO channel {channel}"):
        return TrodesDIOBinaryLoader(matched_file)
    
def get_dio_sg_ts(dio_df: np.ndarray, sampling_rate_hz: float) -> np.ndarray:
    """
    Compute SpikeGadgets timebase timestamps for each entry in the DIO trace.

    Parameters:
        dio_df (np.ndarray): DIO DataFrame with index as sample numbers (from load_dio_binary(...).dio).
        sampling_rate_hz (float): Sampling rate of the Trodes system in Hz.

    Returns:
        np.ndarray: Array of timestamps in SpikeGadgets timebase (in seconds).
    """
    return dio_df.index.to_numpy() / sampling_rate_hz

def get_csc_sg_ts(n_samples: int, sampling_rate_hz: float) -> np.ndarray:
    """
    Compute SpikeGadgets timebase timestamps for each sample in CSC data.

    Parameters:
        n_samples (int): Number of CSC samples.
        sampling_rate_hz (float): Sampling rate of the CSC recording in Hz.

    Returns:
        np.ndarray: Array of timestamps in SpikeGadgets timebase (in seconds).
    """
    return np.arange(n_samples) / sampling_rate_hz
