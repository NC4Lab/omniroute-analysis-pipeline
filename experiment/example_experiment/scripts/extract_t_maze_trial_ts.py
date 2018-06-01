#!/usr/bin/env python
"""
Trial Times Extractor for Omniroute Behavioral Data
---------------------------------------------------

Parses .bag files to extract trial timing information from ROS log messages.
Generates per-session trial_times.csv files for use in trajectory and performance analysis.

Author: AWL & ChatGPT (2025)

Run script:
    python -m experiment.example_experiment.scripts.extract_t_maze_trial_ts
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from rosbags.highlevel import AnyReader
import re

# ---------------- USER CONFIG ----------------
# Rats to process
RATS = [23, 24, 25]     # will map to NC40023, NC40024, NC40025
MAX_SESSIONS = None     # set to small int for quick testing, None for all

# Paths
RAW_BASE = r"Y:\nc4_rat_data\Maze_Rats"
OUTPUT_BASE = r"Y:\nc4_rat_data\lester_manuscript_recordings\preprocess"

# ------------------------------------------------

def load_date_window(rat_id: int):
    """Return start and surgery dates for session filtering."""
    date_windows = {
        23: {"p1_start": "250404", "surgery": None},
        24: {"p1_start": "250403", "surgery": None},
        25: {"p1_start": "250403", "surgery": None},
    }

    if rat_id not in date_windows:
        raise ValueError(f"No hardcoded date window for rat {rat_id}")

    start_date = date_windows[rat_id]["p1_start"]
    surgery_date = date_windows[rat_id]["surgery"]
    return start_date, surgery_date

def parse_rosout_messages(bag_path: Path):
    """Extract (timestamp, msg) pairs from rosout topic."""
    msgs = []
    with AnyReader([bag_path]) as reader:
        connections = [x for x in reader.connections if x.topic == '/rosout']
        for conn, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, conn.msgtype)
            msgs.append((timestamp, msg.msg))
    return msgs

def extract_trials_from_msgs(msgs):
    """
    Parse trial-related events from rosout logs.
    Returns a list of dicts (one per trial).
    Handles both legacy messages ("START OF TRIAL", "SUCCESS", "ERROR", "END_TRIAL")
    and newer mode-based messages ("Switching to mode: Mode.START_TRIAL", etc.).
    """
    trials = []
    current = None

    for ts, m in msgs:
        # --- Start of trial ---
        if m.startswith("START OF TRIAL") or m.startswith("Switching to mode: Mode.START_TRIAL"):
            if current:  # save previous if not already closed
                trials.append(current)
            current = {"StartTime": ts, "StartMsg": m}
            # parse cues if present (only in legacy START OF TRIAL logs)
            if "START OF TRIAL" in m:
                cues = re.findall(r"\[(.*?)\]", m)
                if cues:
                    parts = cues[0].replace("'", "").split(",")
                    parts = [p.strip() for p in parts]
                    if len(parts) >= 3:
                        current["LeftCue"], current["RightCue"], current["FloorCue"] = parts

        # --- Trial number ---
        elif m.startswith("Current trial number"):
            if current:
                tn = re.findall(r"\d+", m)
                if tn:
                    current["TrialNumber"] = int(tn[0])

        # --- Success / error outcomes ---
        elif m in ("SUCCESS", "ERROR"):
            if current:
                current["Result"] = m
                current["EndTime"] = ts

        elif m.startswith("Switching to mode: Mode.SUCCESS"):
            if current:
                current["Result"] = "SUCCESS"
                current["EndTime"] = ts

        elif m.startswith("Switching to mode: Mode.ERROR"):
            if current:
                current["Result"] = "ERROR"
                current["EndTime"] = ts

        # --- Choice events ---
        elif m.startswith("Left chamber selected") or m.startswith("Right chamber selected"):
            if current:
                current["Choice"] = m
                # existing: extract chamber number
                match = re.search(r"(\d+)", m)
                if match:
                    current["ChoiceChamber"] = int(match.group(1))

                # parse into two clean columns
                match = re.search(r"(Left|Right) chamber selected.*?(\d+)", m)
                if match:
                    current["ChamberSelected"] = match.group(1)       # "Left" or "Right"
                    current["ChamberNumber"]  = int(match.group(2))   # e.g. 3
                else:
                    current["ChamberSelected"] = None
                    current["ChamberNumber"]  = None

        # --- Projection / rotation / gate events ---
        elif m == "Projecting images" or m == "Projecting wall images":
            if current:
                current["CueProjectTime"] = ts

        elif "Lowering" in m or "Chamber" in m:
            if current:
                if "Lowering" in m:
                    current.setdefault("GateEvents", []).append((ts, m))
                if "Chamber" in m and "selected" in m:
                    current["MazeRotation"] = m
                    current["MazeRotationTime"] = ts

        # --- Error sound ---
        elif m == "Error sound played":
            if current:
                current["ErrorSoundTime"] = ts

        # --- End of trial ---
        elif m == "END_TRIAL" or m.startswith("Switching to mode: Mode.END_TRIAL"):
            if current:
                current["EndTrialTime"] = ts

    if current:
        trials.append(current)

    return trials

def save_trials(trials, outpath: Path):
    """Save trial dicts as a CSV."""
    df = pd.DataFrame(trials)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(outpath, index=False)
    print(f"Saved {len(df)} trials → {outpath}")

def main():
    for rat in RATS:
        rat_dir = Path(RAW_BASE) / f"NC4{rat:04d}"
        out_dir = Path(OUTPUT_BASE) / f"NC4{rat:04d}"
        start_date, surgery_date = load_date_window(rat)

        # collect valid session dirs
        sessions = sorted([d for d in rat_dir.iterdir() if d.is_dir() and d.name.isdigit()])
        sessions = [s for s in sessions if s.name >= start_date and (surgery_date is None or s.name <= surgery_date)]
        if MAX_SESSIONS:
            sessions = sessions[:MAX_SESSIONS]

        print(f"Rat {rat}: {len(sessions)} sessions to process")

        for sess in sessions:
            outpath = out_dir / sess.name / "trial_times.csv"
            if outpath.exists():
                print(f"  Skipping {sess.name} (already processed)")
                continue

            bagdir = sess / "Raw" / "ROS"
            bags = list(bagdir.glob("*.bag"))
            if not bags:
                print(f"  No bag files in {bagdir}")
                continue

            bag_path = bags[0]  # assume single bag per session
            print(f"  Reading {bag_path.name}...")

            msgs = parse_rosout_messages(bag_path)
            trials = extract_trials_from_msgs(msgs)

            save_trials(trials, outpath)

if __name__ == "__main__":
    main()
