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

from utils.io_trodes import load_sample_rate_from_rec
from utils.path import (
    get_rec_path,
    get_rat_path,
    get_ephys_channel_map_path,
    get_extracted_dir,
    get_session_metadata_path,
    get_ephys_metadata_path,
)


class BaseMetadata(ABC):
    """
    Shared base class for all metadata types.
    Handles save/load logic and custom fields.
    """

    def __init__(self, rat_id: str, session_name: str):
        self.rat_id = rat_id
        self.session_name = session_name
        self.custom = SimpleNamespace()

    def load_or_initialize(self) -> None:
        """
        Load from disk if pickle exists, else initialize and call post_initialize().
        """
        pickle_path = self._get_pickle_path()
        if pickle_path.exists():
            with open(pickle_path, "rb") as f:
                loaded = pickle.load(f)
            self.__dict__.update(loaded.__dict__)
            if not hasattr(self, "custom") or self.custom is None:
                self.custom = SimpleNamespace()
        else:
            get_extracted_dir(self.rat_id, self.session_name).mkdir(parents=True, exist_ok=True)
            self.custom = SimpleNamespace()
            self.post_initialize()

    def save(self) -> None:
        """
        Save this metadata object to its pickle path.
        """
        pickle_path = self._get_pickle_path()
        with open(pickle_path, "wb") as f:
            pickle.dump(self, f)

    @abstractmethod
    def post_initialize(self) -> None:
        """
        Optional hook to initialize values when creating new metadata object.
        """
        pass

    @abstractmethod
    def _get_pickle_path(self) -> Path:
        """
        Return the pickle path for this metadata object.
        """
        pass

    def set_custom_field(self, key: str, value: Any) -> None:
        """
        Add or update a custom metadata field.
        """
        setattr(self.custom, key, value)


class SessionMetadata(BaseMetadata):
    """
    Holds session-level context and identifiers.
    """

    def __init__(self, rat_id: str, session_name: str):
        super().__init__(rat_id, session_name)
        self.rat_path: Path | None = None
        self.rec_path: Path | None = None
        self.extracted_dir: Path | None = None
        self.session_type: Literal["ephys", "behaviour"] | None = None

    def post_initialize(self) -> None:
        self.rat_path = get_rat_path(self.rat_id)
        self.rec_path = get_rec_path(self.rat_id, self.session_name)
        self.extracted_dir = get_extracted_dir(self.rat_id, self.session_name)

        self.session_type = "ephys" if self.rec_path.exists() else "behaviour"

    def _get_pickle_path(self) -> Path:
        return get_session_metadata_path(self.rat_id, self.session_name)


class EphysMetadata(BaseMetadata):
    """
    Holds electrophysiological metadata derived from channel map and .rec file.
    """

    def __init__(self, rat_id: str, session_name: str):
        super().__init__(rat_id, session_name)
        self.trodes_id: list[int] = []
        self.headstage_hardware_id: list[int] = []
        self.trodes_id_include: list[int] = []

        self.raw_csc_data: dict[str, Any] = {}
        self.processed_csc_data: dict[str, Any] = {}

        self.sampling_rate_hz: float | None = None

        self.timestamp_mapping: dict[str, Any] | None = None

    def post_initialize(self) -> None:
        rec_path = get_rec_path(self.rat_id, self.session_name)
        channel_map_path = get_ephys_channel_map_path(self.rat_id)

        self.sampling_rate_hz = load_sample_rate_from_rec(rec_path)
        self._load_channel_map(channel_map_path)

    def _load_channel_map(self, channel_map_path: Path) -> None:
        if not channel_map_path.exists():
            raise FileNotFoundError(f"Channel map not found: {channel_map_path}")
        df = pd.read_csv(channel_map_path)
        filtered = df[df["exclude"] == False]
        self.trodes_id = filtered["trodes_id"].tolist()
        self.headstage_hardware_id = filtered["headstage_hardware_id"].tolist()
        self.trodes_id_include = self.trodes_id.copy()

    def trodes_to_headstage_ids(self, ids: list[int]) -> list[str]:
        """
        Convert a list of trodes_id values to headstage_hardware_id strings.
        """
        mapping = {tid: str(hid) for tid, hid in zip(self.trodes_id, self.headstage_hardware_id)}
        try:
            return [mapping[tid] for tid in ids]
        except KeyError as e:
            raise ValueError(f"Invalid trodes_id: {e.args[0]} not found in known mapping.")

    def _get_pickle_path(self) -> Path:
        return get_ephys_metadata_path(self.rat_id, self.session_name)
