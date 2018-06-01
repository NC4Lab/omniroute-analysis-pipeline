# omniroute_analysis
Shared code base for Omniroute experiment data preprocessing and analysis.

## Environment Setup

Use within a conda environment `omniroute_analysis` that you create using:
```
conda env create -f omniroute_analysis_env.yml
```

Depending on your terminal run:
```
conda init powershell
```

Close and re-open your current shell

Run the following to activate the environment:
```
conda activate omniroute_analysis_env
```

Create a `.env` file in the repo root with the following variables:
```
TRODES_DIR=
NC4_DATA_DIR=
```

For example (using double backslashes on Windows paths):
```
TRODES_DIR=C:\\Users\\lester\\MeDocuments\\Research\\MadhavLab\\Projects\\SpikeGadgets\\Trodes_2-3-4_Windows64
NC4_DATA_DIR=C:\\Users\\lester\\UBC\\Madhav, Manu - lesterkaur2024gate\\analysis\\gate_ephys_test\\data
PYTHONPATH=.
```

## SpikeInterface Setup

Install `spikeinterface` and related tools using pip:
```
pip install spikeinterface[full] python-dotenv
```

## Trodes Setup

Download and install the `Trodes` software suite from the SpikeGadgets website:
https://www.spikegadgets.com/trodes

## TO DO
- Update .yml to remove unused
- Update .yml to include SpikeInterface

## Interpreter Setup (VS Code)

To run scripts with the correct environment:

1. Open the Command Palette (`Ctrl+Shift+P`)
2. Type `Python: Select Interpreter`
3. Choose: `omniroute_analysis_env` (should show path ending in `...\\envs\\omniroute_analysis_env\\python.exe`)

## Running Scripts

To ensure that all modules (e.g., `utils/`, `pipeline/`) are correctly importable, run scripts using Python’s `-m` module flag from the project root. For example:

```
python -m experiment.example_experiment.scripts.export_csc_to_matlab
```

This guarantees that the root folder is treated as the top-level package, avoiding import errors.

Avoid running scripts directly with `python path/to/script.py`, as this can break relative imports due to how Python sets the module search path.
