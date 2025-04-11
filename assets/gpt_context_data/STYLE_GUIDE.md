# OMNIROUTE_ANALYSIS Code Style Guide

This guide outlines code commenting and structuring standards for collaborative development within the lab.

## Function and Class Docstrings

All public functions and classes should have a docstring following this structure:

```
def example_function(param1: int, param2: str) -> bool:
    """
    One-line summary of what the function does.

    Parameters:
        param1 (int): Description of first parameter.
        param2 (str): Description of second parameter.

    Returns:
        bool: Description of the return value.
    """
```

## Module-Level Docstrings

At the top of every `.py` file, include a brief summary (Note: don't include dependencies):

```
"""
Module: io_trodes.py

Purpose:
    Utilities for reading continuous data from SpikeGadgets .rec files using SpikeInterface.
"""
```

## Main Script Commenting

### Block-Level Comments

Use short **header comments** to describe the purpose of each code block. Focus on the *why* or *what this block does*, not line-by-line detail.

### Inline Comments

Use inline comments **only when necessary** to explain non-obvious logic. Prioritize *why* over *what*.

### Example

```python
# Load CSC data from .rec and keep only active channels
rec = load_continuous_from_rec(rec_path)
rec = rec.channel_slice(channel_ids=active_channels)  # Remove unused or empty channels

# Export to .dat + .json for future SI-compatible reuse
export_csc_to_binary(rec, out_dir)

# Bandpass filter the CSC data in parallel
filtered = bandpass_filter(
    rec, freq_min=1, freq_max=100,
    n_jobs=4  # Use 4 parallel workers
)

# Extract theta band and save
theta = bandpass_filter(filtered, freq_min=6, freq_max=10)
np.save(out_dir / "theta_filtered.npy", theta.get_traces())  # Save raw theta traces
```

Use consistent formatting to make script structure easy to scan and reason about.


## Naming Conventions

- Use `snake_case` for variables and function names
- Use `UPPER_CASE` for constants
- Use `CamelCase` for class names
