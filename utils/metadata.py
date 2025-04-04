"""
Module: metadata.py

Purpose:
    Metadata structures for handling session-level and electrophysiological context.
"""

import pickle
from typing import Any, Literal

import numpy as np
import pandas as pd
from pathlib import Path
from types import SimpleNamespace

from utils.path import get_rec_path, get_rat_path
from utils.io_trodes import load_sample_rate_from_rec


class SessionMetadata:
    """
    Holds session-level context and paths used across the pipeline.
    Use `load_extract_data(rat_id, session_name)` to populate after init.
    """

    def __init__(self):
        self.rat_id: str = ""
        self.session_name: str = ""

        self.rat_path: Path | None = None
        self.rec_path: Path | None = None
        self.extracted_dir: Path | None = None
        self.pickle_path: Path | None = None

        self.session_type: Literal["ephys", "behaviour"] | None = None

        self.custom = None

    def load_extract_data(self, rat_id: str, session_name: str) -> None:
        """
        Load this SessionMetadata instance from disk if a saved pickle exists.
        Otherwise, populate its fields based on the session folder structure.
        """
        self.rat_id = rat_id
        self.session_name = session_name

        self.rat_path = get_rat_path(rat_id)
        self.rec_path = get_rec_path(rat_id, session_name)
        self.extracted_dir = self.rat_path / session_name / "extracted"

        self.pickle_path = self.extracted_dir / "session_metadata.pkl"

        if self.pickle_path.exists():
            with open(self.pickle_path, "rb") as f:
                loaded: SessionMetadata = pickle.load(f)
            self.__dict__.update(loaded.__dict__)

            if not hasattr(self, "custom") or self.custom is None:
                self.custom = SimpleNamespace()
        else:
            self.session_type = "ephys" if self.rec_path.exists() else "behaviour"
            self.extracted_dir.mkdir(parents=True, exist_ok=True)
            self.custom = SimpleNamespace()

    def set_custom_field(self, key: str, value: Any) -> None:
        setattr(self.custom, key, value)

    def save(self) -> None:
        if not self.extracted_dir:
            raise ValueError("Cannot save without calling load_extract_data first.")
        with open(self.pickle_path, "wb") as f:
            pickle.dump(self, f)


class EphysMetadata:
    """
    Holds electrophysiological channel metadata and maps available vs. active channels.
    Use `load_extract_data(rec_path, channel_map_path, save_path)` to populate after init.
    """

    def __init__(self):
        self.extracted_dir: Path | None = None
        self.pickle_path: Path | None = None
        self.channel_map_path: Path | None = None

        self.trodes_id: list[int] = []
        self.headstage_hardware_id: list[int] = []
        self.trodes_id_include: list[int] = []

        self.sampling_rate_hz: float | None = None
        self.raw_csc_data: dict[str, Any] = {}
        self.processed_csc_data: dict[str, Any] = {}
        self.timestamp_mapping: dict[str, Any] | None = None

        self.custom = None

    def load_extract_data(self, rat_id: str, session_name: str) -> None:
        """
        Load from disk if a pickle exists; otherwise populate fields from inputs.
        """
        rat_path = get_rat_path(rat_id)
        rec_path = get_rec_path(rat_id, session_name)
        self.extracted_dir = rat_path / session_name / "extracted"

        self.pickle_path = self.extracted_dir / "ephys_metadata.pkl"
        self.channel_map_path = rat_path / "ephys_channel_map_metadata.csv"

        if self.pickle_path.exists():
            with open(self.pickle_path, "rb") as f:
                loaded: EphysMetadata = pickle.load(f)
            self.__dict__.update(loaded.__dict__)

            if not hasattr(self, "custom") or self.custom is None:
                self.custom = SimpleNamespace()
        else:
            self.extracted_dir.mkdir(parents=True, exist_ok=True)
            self.custom = SimpleNamespace()
            self.sampling_rate_hz = load_sample_rate_from_rec(rec_path)

    def _load_channel_map(self) -> None:
        if not self.channel_map_path.exists():
            raise FileNotFoundError(f"Channel map not found: {self.channel_map_path}")

        df = pd.read_csv(self.channel_map_path)
        filtered = df[df["exclude"] == False]

        self.trodes_id = filtered["trodes_id"].tolist()
        self.headstage_hardware_id = filtered["headstage_hardware_id"].tolist()
        self.trodes_id_include = self.trodes_id.copy()

    def trodes_to_headstage_ids(self, ids: list[int]) -> list[str]:
        """
        Convert a list of trodes_id values to headstage_hardware_id strings.

        Parameters:
            ids (list[int]): Subset of trodes_id to convert.

        Returns:
            list[str]: Corresponding headstage_hardware_id values as strings.
        """
        mapping = {tid: str(hid) for tid, hid in zip(self.trodes_id, self.headstage_hardware_id)}
        try:
            return [mapping[tid] for tid in ids]
        except KeyError as e:
            raise ValueError(f"Invalid trodes_id: {e.args[0]} not found in known mapping.")

    def add_empty_processed_array(self, name: str, csc_dataset: np.ndarray) -> None:
        self.processed_csc_data[name] = csc_dataset

    def set_custom_field(self, key: str, value: Any) -> None:
        setattr(self.custom, key, value)

    def save(self) -> None:
        if not self.extracted_dir:
            raise ValueError("Cannot save without calling load_extract_data first.")
        with open(self.pickle_path, "wb") as f:
            pickle.dump(self, f)



