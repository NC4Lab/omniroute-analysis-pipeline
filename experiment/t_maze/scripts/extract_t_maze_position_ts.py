#!/usr/bin/env python
"""
Position Times Extractor for Omniroute Behavioral Data
------------------------------------------------------

Parses .bag files to extract rat position time series from ROS pose topics.
Generates per-session position_times.csv files for use in trajectory analyses.

Checks both harness and headstage pose topics (implanted rats will have headstage).
If neither topic exists, the session is skipped.

Author: AWL & ChatGPT (2025)

Run script:
    python -m experiment.example_experiment.scripts.extract_t_maze_position_ts
"""

import os
import pandas as pd
from pathlib import Path
from rosbags.highlevel import AnyReader

# ---------------- USER CONFIG ----------------
# Rats to process
RATS = [23, 24, 25]     # maps to NC40023, NC40024, NC40025
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

def extract_pose_timeseries(bag_path: Path):
    """Extract (timestamp, x, y, z) from harness or headstage pose topics."""
    records = []

    with AnyReader([bag_path]) as reader:
        # Get available topics
        topics = [c.topic for c in reader.connections]

        # Priority: check for headstage, then harness
        topic = None
        source = None
        if '/headstage_pose_in_maze' in topics:
            topic = '/headstage_pose_in_maze'
            source = 'headstage'
        elif '/harness_pose_in_maze' in topics:
            topic = '/harness_pose_in_maze'
            source = 'harness'
        else:
            return []  # nothing found

        connections = [x for x in reader.connections if x.topic == topic]
        for conn, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, conn.msgtype)
            pose = msg.pose.position
            records.append({
                "Time": timestamp,
                "X": pose.x,
                "Y": pose.y,
                "Z": pose.z,
                "Source": source,
            })

    return records

def save_positions(records, outpath: Path):
    """Save position records as a CSV."""
    if not records:
        print(f"    No pose data found, skipping save.")
        return
    df = pd.DataFrame(records)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(outpath, index=False)
    print(f"    Saved {len(df)} positions → {outpath}")

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
            outpath = out_dir / sess.name / "position_times.csv"
            if outpath.exists():
                print(f"  Skipping {sess.name} (already has position_times.csv)")
                continue

            bagdir = sess / "Raw" / "ROS"
            bags = list(bagdir.glob("*.bag"))
            if not bags:
                print(f"  No bag files in {bagdir}")
                continue

            bag_path = bags[0]  # assume single bag per session
            print(f"  Reading {bag_path.name}...")

            records = extract_pose_timeseries(bag_path)
            if not records:
                print(f"    No harness/headstage pose topic in {bag_path.name}")
                continue

            save_positions(records, outpath)

if __name__ == "__main__":
    main()
