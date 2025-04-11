"""
Module: metadata.py

Purpose:
    Metadata structures for handling session-level and electrophysiological context.
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal
from abc import ABC, abstractmethod

from utils import config as _config
from utils.omni_anal_logger import omni_anal_logger
from utils.versioning import get_version_info
from utils.io_trodes import load_sample_rate_from_rec
from utils.path import (
    get_rec_path,
    get_rat_path,
    get_ephys_channel_map_path,
    get_extracted_dir,
    get_session_metadata_path,
    get_ephys_metadata_path,
    get_dio_dir,
    get_spike_dir,
)


#------------------------------------------------------------------
# Base class for all metadata types
#------------------------------------------------------------------

class BaseMetadata(ABC):
    """
    Shared base class for metadata objects.

    Provides:
    - Serialization/deserialization via pickle
    - Optional custom fields (stored as SimpleNamespace)
    - Automatically tags all metadata with version_info
    """

    def __init__(self, rat_id: str, session_name: str):
        """
        Parameters:
            rat_id (str): Unique animal identifier (e.g., 'NC40008')
            session_name (str): Timestamped session name (e.g., '20250328_134136')
        """
        self.rat_id = rat_id
        self.session_name = session_name
        self.custom = SimpleNamespace()
        self.version_info: dict[str, str] = {}

    def load_or_initialize(self) -> None:
        """
        Load object from pickle if it exists; otherwise call post_initialize().
        Also attaches version metadata (git hash and processing timestamp).
        """
        pickle_path = self._get_pickle_path()

        # Load from disk if pickle exists
        if pickle_path.exists():
            with open(pickle_path, "rb") as f:
                loaded = pickle.load(f)
            self.__dict__.update(loaded.__dict__)

            # Ensure custom and version fields are present
            if not hasattr(self, "custom") or self.custom is None:
                self.custom = SimpleNamespace()
            if not hasattr(self, "version_info") or self.version_info is None:
                self.version_info = get_version_info()

        # Initialize from scratch if no file exists
        else:
            self.custom = SimpleNamespace()
            self.version_info = get_version_info()
            self.post_initialize()

    def save_pickle(self, overwrite: bool = False) -> None:
        """
        Save this metadata object to disk as a pickle file.

        Parameters:
            overwrite (bool): If True, overwrite existing file. Default is False.
        """
        pickle_path = self._get_pickle_path()

        if pickle_path.exists() and not overwrite:
            omni_anal_logger.warning(f"Pickle already exists at {pickle_path} — skipping save.")
            return

        with open(pickle_path, "wb") as f:
            pickle.dump(self, f)

    def set_custom_field(self, key: str, value: Any) -> None:
        """
        Add or update a user-defined custom metadata field.

        Parameters:
            key (str): Name of the field
            value (Any): Value to store
        """
        setattr(self.custom, key, value)

    @abstractmethod
    def post_initialize(self) -> None:
        """
        Hook for initializing values when creating a new metadata object.
        Called only if no pickle file exists.
        """
        pass

    @abstractmethod
    def _get_pickle_path(self) -> Path:
        """
        Returns:
            Path: Where this metadata object should be serialized
        """
        pass


#------------------------------------------------------------------
# Session-level metadata (e.g., paths, session type)
#------------------------------------------------------------------

class SessionMetadata(BaseMetadata):
    """
    Stores session-level metadata and derived paths.
    """

    def __init__(self, rat_id: str, session_name: str):
        super().__init__(rat_id, session_name)
        self.rat_path: Path | None = None
        self.rec_path: Path | None = None
        self.extracted_dir: Path | None = None
        self.dio_dir: Path | None = None
        self.spike_dir: Path | None = None
        self.session_type: Literal["ephys", "behaviour"] | None = None

    def post_initialize(self) -> None:
        """
        Initialize directory paths and determine session type.
        """
        self.rat_path = get_rat_path(self.rat_id)
        self.rec_path = get_rec_path(self.rat_id, self.session_name)
        self.extracted_dir = get_extracted_dir(self.rat_id, self.session_name)
        self.dio_dir = get_dio_dir(self.rat_id, self.session_name)
        self.spike_dir = get_spike_dir(self.rat_id, self.session_name)
        self.session_type = "ephys" if self.rec_path.exists() else "behaviour"

        self.extracted_dir.mkdir(parents=True, exist_ok=True)

    def _get_pickle_path(self) -> Path:
        return get_session_metadata_path(self.rat_id, self.session_name)


#------------------------------------------------------------------
# Electrophysiology metadata (e.g., channels, sample rate)
#------------------------------------------------------------------

class EphysMetadata(BaseMetadata):
    """
    Stores ephys-specific metadata, including channel mappings and sampling rate.
    """

    def __init__(self, rat_id: str, session_name: str):
        super().__init__(rat_id, session_name)

        self.trodes_id: list[int] = []               # Logical Trodes channel IDs
        self.headstage_hardware_id: list[int] = []   # Corresponding hardware channel IDs
        self.trodes_id_include: list[int] = []       # Active analysis mask
        self.sampling_rate_hz: float | None = None
        self.timestamp_mapping: dict[str, Any] | None = None

    def post_initialize(self) -> None:
        """
        Load sampling rate and channel map from disk.
        """
        rec_path = get_rec_path(self.rat_id, self.session_name)
        channel_map_path = get_ephys_channel_map_path(self.rat_id)

        self.sampling_rate_hz = load_sample_rate_from_rec(rec_path)
        self._load_channel_map(channel_map_path)

    def _load_channel_map(self, channel_map_path: Path) -> None:
        """
        Load and filter the per-rat channel map CSV.

        Parameters:
            channel_map_path (Path): Path to channel map CSV
        """
        if not channel_map_path.exists():
            raise FileNotFoundError(f"Channel map not found: {channel_map_path}")

        df = pd.read_csv(channel_map_path)
        filtered = df[df["exclude"] == False]

        self.trodes_id = filtered["trodes_id"].tolist()
        self.headstage_hardware_id = filtered["headstage_hardware_id"].tolist()
        self.trodes_id_include = self.trodes_id.copy()

    def trodes_to_headstage_ids(self, ids: list[int]) -> list[str]:
        """
        Convert Trodes IDs to hardware channel ID strings.

        Parameters:
            ids (list[int]): Trodes channel IDs to convert

        Returns:
            list[str]: Corresponding hardware IDs as strings

        Raises:
            ValueError: If any ID is not found in the map
        """
        mapping = {tid: str(hid) for tid, hid in zip(self.trodes_id, self.headstage_hardware_id)}
        try:
            return [mapping[tid] for tid in ids]
        except KeyError as e:
            raise ValueError(f"Invalid trodes_id: {e.args[0]} not found in known mapping.")

    def _get_pickle_path(self) -> Path:
        return get_ephys_metadata_path(self.rat_id, self.session_name)
