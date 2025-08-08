"""
Test: check_dio_pulses.py

Purpose:
    Scan all DIO channels for a given session and report how many rising-edge pulses were detected.

Run:
    python -m testing.check_dio_pulses
"""

from utils.path import get_dio_dir
from utils.io_trodes import load_dio_binary
from utils.omni_anal_logger import omni_anal_logger

# ----------------------------
# Set session to check
# ----------------------------
rat_id = "NC40023"
session_name = "20250806_170156"

# ----------------------------
# Parameters
# ----------------------------
max_channels_to_check = 16  # Check Din1...Din16

def count_rising_edges(dio_df):
    """
    Count the number of rising edges (0 -> 1 transitions) in the DIO 'state' column.
    """
    state = dio_df["state"].astype(int)
    edges = (state.diff().fillna(0) == 1)
    return int(edges.sum())

def main():
    dio_dir = get_dio_dir(rat_id, session_name)

    if not dio_dir.exists():
        raise FileNotFoundError(f"DIO directory not found: {dio_dir}")

    omni_anal_logger.info(f"Scanning DIO pulses in: {dio_dir}")

    found_any = False
    for ch in range(1, max_channels_to_check + 1):
        try:
            dio_df = load_dio_binary(dio_dir, channel=ch).dio
        except FileNotFoundError:
            continue  # Skip channels with no file

        found_any = True
        pulse_count = count_rising_edges(dio_df)
        omni_anal_logger.info(f"Din{ch}: {pulse_count} pulses detected")

    if not found_any:
        omni_anal_logger.warning("No DIO channels found to scan.")

if __name__ == "__main__":
    main()
