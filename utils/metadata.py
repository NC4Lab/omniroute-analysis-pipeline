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

from utils.omni_anal_logger import omni_anal_logger
from utils.versioning import get_version_info
from utils.io_trodes import load_sample_rate_from_rec
from utils.path import (
    get_rec_path,
    get_rat_dir,
    get_ephys_channel_map_csv_path,
    get_processed_dir,
    get_session_metadata_path,
    get_ephys_metadata_path,
    get_dio_dir,
    get_spike_dir,
    get_experiment_metadata_csv_path,
    get_data_dir,
)


#------------------------------------------------------------------
# Base class for all metadata types
#------------------------------------------------------------------

class BaseMetadata:
    """
    Shared base class for SessionMetadata and EphysMetadata metadata objects.

    Provides:
    - Serialization/deserialization via pickle
    - Optional custom fields (stored as SimpleNamespace)
    - Automatically tags all metadata with version_info
    """

    def __init__(self):
        self.custom = SimpleNamespace()
        self.version_info: dict[str, str] = {}

    def load_or_initialize_pickle(self) -> None:
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

    def print_metadata_fields(self) -> None:
        """
        Log all non-private metadata fields and their contents using omni_anal_logger.
        This function adapts automatically to any added attributes.
        """
        from pprint import pformat

        omni_anal_logger.info(f"--- {self.__class__.__name__} contents ---")
        for key, val in self.__dict__.items():
            if key.startswith("_"):
                continue  # Skip private/internal attributes
            formatted = pformat(val, indent=4, width=100)
            omni_anal_logger.info(f"{key}:\n{formatted}")
        omni_anal_logger.info(f"--- End {self.__class__.__name__} ---")

    def post_initialize(self) -> None:
        """
        Hook for initializing values when creating a new metadata object.
        Called only if no pickle file exists.
        """
        pass

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
        """
        Parameters:
            rat_id (str): Unique animal identifier (e.g., 'NC40001')
            session_name (str): Timestamped session name (e.g., '20250328_134136')
        """
        super().__init__()

        self.rat_id = rat_id
        self.session_name = session_name
        self.rat_path: Path | None = None
        self.rec_path: Path | None = None
        self.processed_dir: Path | None = None
        self.dio_dir: Path | None = None
        self.spike_dir: Path | None = None
        self.session_type: Literal["ephys", "behaviour"] | None = None

    def post_initialize(self) -> None:
        """
        Initialize directory paths and determine session type.
        """
        self.rat_path = get_rat_dir(self.rat_id)
        self.rec_path = get_rec_path(self.rat_id, self.session_name)
        self.processed_dir = get_processed_dir(self.rat_id, self.session_name)
        self.dio_dir = get_dio_dir(self.rat_id, self.session_name)
        self.spike_dir = get_spike_dir(self.rat_id, self.session_name)
        self.session_type = "ephys" if self.rec_path.exists() else "behaviour"

        self.processed_dir.mkdir(parents=True, exist_ok=True)

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
        """
        Parameters:
            rat_id (str): Unique animal identifier (e.g., 'NC40001')
            session_name (str): Timestamped session name (e.g., '20250328_134136')
        """
        super().__init__()

        self.rat_id = rat_id
        self.session_name = session_name
        self.channel_trodes_id: list[int] = []               # Logical Trodes channel IDs
        self.channel_headstage_hardware_id: list[int] = []   # Corresponding hardware channel IDs
        self.channel_trodes_id_include: list[int] = []       # Active analysis mask
        self.sampling_rate_hz: float | None = None
        self.timestamp_mapping: dict[str, Any] | None = None

    def post_initialize(self) -> None:
        """
        Load sampling rate and channel map from disk.
        """
        rec_path = get_rec_path(self.rat_id, self.session_name)
        channel_map_path = get_ephys_channel_map_csv_path(self.rat_id)

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

        self.channel_trodes_id = filtered["trodes_id"].tolist()
        self.channel_headstage_hardware_id = filtered["headstage_hardware_id"].tolist()
        self.channel_trodes_id_include = self.channel_trodes_id.copy()

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
        mapping = {tid: str(hid) for tid, hid in zip(self.channel_trodes_id, self.channel_headstage_hardware_id)}
        try:
            return [mapping[tid] for tid in ids]
        except KeyError as e:
            raise ValueError(f"Invalid trodes_id: {e.args[0]} not found in known mapping.")

    def _get_pickle_path(self) -> Path:
        return get_ephys_metadata_path(self.rat_id, self.session_name)


#------------------------------------------------------------------
# Experiment-level metadata (batch processing scope)
#------------------------------------------------------------------

class ExperimentMetadata(BaseMetadata):
    """
    Handles experiment-level batch processing metadata via CSV.
    Loads and structures session inclusion data from
    'data/experiment_metadata.csv'.

    This class does not inherit from BaseMetadata and is not serialized.
    """

    def __init__(self):
        super().__init__()

        self.df: pd.DataFrame | None = None
        self.batch_rat_list: list[dict[str, list[str]]] = []
        self.version_info: dict[str, str] = get_version_info()

    @classmethod
    def initialize_experiment_metadata_csv(cls, overwrite: bool = False) -> None:
        """
        Create an initial experiment_metadata.csv file in the experiment folder
        by scanning NC4_DATA_DIR for all available (rat_id, session_name) pairs.

        Parameters:
            overwrite (bool): If True, overwrite the file if it already exists
        """
        csv_path = get_experiment_metadata_csv_path()

        # Skip generation if file already exists and overwrite is False
        if csv_path.exists() and not overwrite:
            omni_anal_logger.warning(f"experiment_metadata.csv already exists at {csv_path} — skipping generation.")
            return

        # Scan for available rat/session pairs under the data directory
        records = []
        data_dir = get_data_dir()
        for rat_path in sorted(data_dir.glob("NC*")):
            rat_id = rat_path.name
            for session_dir in sorted(rat_path.glob("20*/")):
                session_name = session_dir.name
                records.append({
                    "rat_id": rat_id,
                    "session_name": session_name,
                    "include": 1
                })

        # Raise error if no valid sessions were found
        if not records:
            raise RuntimeError("No sessions found when scanning NC4_DATA_DIR — cannot create experiment_metadata.csv.")

        # Write CSV to disk
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False)
        omni_anal_logger.info(f"Wrote {len(df)} session entries to: {csv_path}")

    def load_experiment_metadata_csv(self) -> None:
        """
        Load the experiment_metadata.csv into memory and populate
        internal data structures for batch queries.
        """
        csv_path = get_experiment_metadata_csv_path()

        # Check that the CSV file exists
        if not csv_path.exists():
            raise FileNotFoundError(f"experiment_metadata.csv not found at: {csv_path}")

        # Load the CSV into a DataFrame
        self.df = pd.read_csv(csv_path)

        # Ensure required columns are present
        required_cols = {"rat_id", "session_name", "include"}
        if not required_cols.issubset(set(self.df.columns)):
            raise ValueError(f"experiment_metadata.csv missing required columns: {required_cols}")

        # Cast 'include' column to integer to ensure consistent filtering
        self.df["include"] = self.df["include"].astype(int)

        # Group included sessions by rat_id
        grouped = (
            self.df[self.df["include"] == 1]
            .groupby("rat_id")["session_name"]
            .apply(list)
            .reset_index()
            .rename(columns={"session_name": "batch_session_list"})
        )

        # Store grouped structure for downstream batch processing
        self.batch_rat_list = grouped.to_dict("records")

