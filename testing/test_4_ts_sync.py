"""
Test: Timestamp sync computation and visual validation.
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.omni_anal_logger import omni_anal_logger
from utils.path import get_rec_path, get_dio_dir
from utils.metadata import SessionMetadata, EphysMetadata
from utils.io_trodes import load_dio_binary
from utils.ts_sync import compute_ts_sync_parameters, convert_sg_ts_to_ros_time
from utils.io_rosbag import load_ros_sync_ts, print_all_topics, print_unique_strings_from_topic

# --- Setup ---
rat_id = "NC40008"
session_name = "20250328_134136"

rec_path = get_rec_path(rat_id, session_name)
dio_dir = get_dio_dir(rat_id, session_name)

session = SessionMetadata(rat_id, session_name)
session.load_or_initialize()
omni_anal_logger.info("Initialized SessionMetadata")

ephys = EphysMetadata(rat_id, session_name)
ephys.load_or_initialize()
omni_anal_logger.info("Initialized EphysMetadata")

# --- ROS bag path ---
rosbag_path = Path(rec_path).parents[1] / "ROS" / "ros_session_20250328_134222.bag"

# --- Compute sync parameters ---
sync_result = compute_ts_sync_parameters(
    dio_path=dio_dir,
    sampling_rate_hz=ephys.sampling_rate_hz,
    rosbag_path=rosbag_path
)
ephys.timestamp_mapping = sync_result
ephys.save()
omni_anal_logger.info(f"Saved sync parameters to EphysMetadata: {sync_result}")

# --- Extract Trodes DIO timestamps (rising edges) ---
dio_loader = load_dio_binary(dio_dir, channel=2)
dio_df = dio_loader.dio
trodes_ts = dio_df[dio_df["state"] == True].index.to_numpy() / ephys.sampling_rate_hz

# --- Convert Trodes timestamps to ROS timebase ---
transformed_ts = convert_sg_ts_to_ros_time(trodes_ts, sync_result)

# --- Load ROS timestamps ---
ros_ts = load_ros_sync_ts(rosbag_path)

# --- Evaluate match quality ---
min_len = min(len(transformed_ts), len(ros_ts))
residuals = ros_ts[:min_len] - transformed_ts[:min_len]
rms_error = np.sqrt(np.mean(residuals ** 2))
omni_anal_logger.info(f"RMS error after sync: {rms_error:.6f} seconds")

# --- Generate diagnostic plot ---
omni_anal_logger.info("Generating validation plot...")

trace_array = dio_df["state"].to_numpy()
trace_timestamps = dio_df.index.to_numpy() / ephys.sampling_rate_hz
trace_timestamps_ros = convert_sg_ts_to_ros_time(trace_timestamps, sync_result)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(trace_timestamps_ros, trace_array, lw=0.5, label="DIO Trace")
ax.vlines(ros_ts, ymin=0, ymax=1, color="red", linestyle="-", label="ROS Sync Pulses", alpha=0.6)

ax.set_title("Timestamp Alignment Validation")
ax.set_xlabel("ROS Time (s)")
ax.set_ylabel("DIO State")
ax.legend()
fig.tight_layout()

output_file = Path(__file__).resolve().parent / "plots" / "ts_sync_validation_plot.png"
output_file.parent.mkdir(exist_ok=True)
fig.savefig(output_file)
omni_anal_logger.info(f"Validation plot saved: {output_file}")

omni_anal_logger.info("Timestamp sync test complete.")
