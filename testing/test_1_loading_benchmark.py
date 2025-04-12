"""
Script: test_csc_io_benchmark.py

Purpose:
    Benchmark 3 methods for reading and processing CSC data:
    1. Directly from .rec file
    2. From a single interleaved .dat file
    3. From multiple single-channel .dat files

    Each method logs:
    - Time to load from .rec
    - Time to save/load intermediate binary
    - Time to process with bandpass_filter()
    - Combined times for both prep and analysis

Usage:
    Run from project root: `python testing/test_csc_io_benchmark.py`

Dependencies:
    - SpikeInterface
    - numpy
    - Optional: tabulate (for pretty table output)
"""

import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import time
import numpy as np
from spikeinterface.preprocessing import bandpass_filter, common_reference, normalize_by_quantile
from spikeinterface.extractors import read_spikegadgets, BinaryRecordingExtractor, NumpyRecording
from spikeinterface import write_binary_recording

from utils.omni_anal_logger import omni_anal_logger
from utils.metadata import SessionMetadata
from utils.config import NC4_DATA_DIR

RAT_ID = "NC40001"
SESSION_NAME = "20250328_134136"
N_CHANNELS = 0
DURATION_SECONDS = 0
BENCHMARK_DIR = Path("testing/temp_benchmark_data")
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

def process_csc_data(recording):
    start = time.perf_counter()

    # Bandpass filter
    r = bandpass_filter(recording, freq_min=1, freq_max=300)
    # Common average reference (median)
    r = common_reference(r, reference='global', operator='median')
    # Common average reference (average)
    r = common_reference(r, reference='global', operator='average')

    duration = time.perf_counter() - start
    return r, duration

def get_rec_path():
    #return Path(NC4_DATA_DIR) / RAT_ID / SESSION_NAME / "raw" / "Trodes" / f"{SESSION_NAME}_merged.rec"
    return Path(r"Z:\NC40014\240209_training\raw\Trodes\240209_merged.rec")


def method_from_rec():
    omni_anal_logger.info("Starting: Method A - Direct from .rec")
    t0 = time.perf_counter()
    recording = read_spikegadgets(get_rec_path())
    recording = recording.channel_slice(channel_ids=recording.channel_ids[:N_CHANNELS])
    recording = recording.frame_slice(start_frame=0, end_frame=int(recording.get_sampling_frequency() * DURATION_SECONDS))
    load_time = time.perf_counter() - t0

    _, process_time = process_csc_data(recording)

    return {
        "method": "rec",
        "load_rec": load_time,
        "process": process_time,
        "total": load_time + process_time
    }

def method_interleaved_dat():
    omni_anal_logger.info("Starting: Method B - Interleaved .dat")
    dat_path = BENCHMARK_DIR / "interleaved.dat"

    # Step 1: Load + Save .rec -> .dat
    t0 = time.perf_counter()
    recording = read_spikegadgets(get_rec_path())
    recording = recording.channel_slice(channel_ids=recording.channel_ids[:N_CHANNELS])
    recording = recording.frame_slice(start_frame=0, end_frame=int(recording.get_sampling_frequency() * DURATION_SECONDS))
    load_rec_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    write_binary_recording(
        recording=recording,
        file_paths=dat_path,
        dtype="int16"
    )
    save_bin_time = time.perf_counter() - t1

    # Step 2: Load .dat + Process
    t2 = time.perf_counter()
    loaded = BinaryRecordingExtractor(
        file_paths=dat_path,
        sampling_frequency=recording.get_sampling_frequency(),
        dtype="int16",
        num_chan=N_CHANNELS,
        time_axis=1
    )
    load_bin_time = time.perf_counter() - t2

    _, process_time = process_csc_data(loaded)

    return {
        "method": "interleaved",
        "load_rec": load_rec_time,
        "save_bin": save_bin_time,
        "prep_total": load_rec_time + save_bin_time,
        "load_bin": load_bin_time,
        "process": process_time,
        "analysis_total": load_bin_time + process_time
    }

def method_split_dats():
    omni_anal_logger.info("Starting: Method C - Split .dat files")
    split_paths = []

    # Step 1: Load .rec + Save split .dat
    t0 = time.perf_counter()
    recording = read_spikegadgets(get_rec_path())
    recording = recording.channel_slice(channel_ids=recording.channel_ids[:N_CHANNELS])
    recording = recording.frame_slice(start_frame=0, end_frame=int(recording.get_sampling_frequency() * DURATION_SECONDS))
    load_rec_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    traces = recording.get_traces()
    for ch in range(N_CHANNELS):
        out_path = BENCHMARK_DIR / f"csc{ch+1}.dat"
        traces[ch].astype("int16").tofile(out_path)
        split_paths.append(out_path)
    save_split_time = time.perf_counter() - t1

    # Step 2: Load split .dat + Process
    t2 = time.perf_counter()
    loaded_traces = [np.fromfile(p, dtype="int16")[None, :] for p in split_paths]
    stacked = np.vstack(loaded_traces).T
    loaded = NumpyRecording(
        traces_list=[stacked.T],
        sampling_frequency=recording.get_sampling_frequency()
    )
    load_split_time = time.perf_counter() - t2

    _, process_time = process_csc_data(loaded)

    return {
        "method": "split",
        "load_rec": load_rec_time,
        "save_bin": save_split_time,
        "prep_total": load_rec_time + save_split_time,
        "load_bin": load_split_time,
        "process": process_time,
        "analysis_total": load_split_time + process_time
    }

def run_all(n_channels, duration_seconds):
    global N_CHANNELS, DURATION_SECONDS
    N_CHANNELS = n_channels
    DURATION_SECONDS = duration_seconds

    all_results = [method_from_rec(), method_interleaved_dat(), method_split_dats()]

    print(f"\nDetailed Benchmark Results (Channels: {N_CHANNELS}, Duration: {DURATION_SECONDS}s):\n")
    for res in all_results:
        print(f"Method: {res['method']}")
        if res['method'] == 'rec':
            print(f"  Load .rec:       {res['load_rec']*1e6:.0f} µs")
            print(f"  Process:         {res['process']*1e6:.0f} µs")
            print(f"  Total:           {res['total']*1e6:.0f} µs")
        else:
            print(f"  Load .rec:       {res['load_rec']*1e6:.0f} µs")
            print(f"  Save binary:     {res['save_bin']*1e6:.0f} µs")
            print(f"  Prep total:      {res['prep_total']*1e6:.0f} µs")
            print(f"  Load binary:     {res['load_bin']*1e6:.0f} µs")
            print(f"  Process:         {res['process']*1e6:.0f} µs")
            print(f"  Analysis total:  {res['analysis_total']*1e6:.0f} µs")
        print()

def sweep_benchmarks():
    test_configs = [
        (100, 60*10),
        (100, 60*20),
        (100, 60*30),
    ]
    for n_channels, duration in test_configs:
        run_all(n_channels, duration)

if __name__ == "__main__":
    sweep_benchmarks()

