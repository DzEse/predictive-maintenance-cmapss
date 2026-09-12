# Data Inputs

This project uses the NASA C-MAPSS Turbofan Engine Degradation Simulation Data Set, FD001 subset.

Official NASA source: Prognostics Center of Excellence (PCoE) Data Set Repository, **Turbofan Engine Degradation Simulation**.

The professional rebuild expects these three source files in `data/raw/`:

```text
data/raw/
├── train_FD001.txt
├── test_FD001.txt
└── RUL_FD001.txt
```

## Why all three files are required

- `train_FD001.txt` contains 100 run-to-failure engine trajectories and is used to train the model.
- `test_FD001.txt` contains 100 separate engine trajectories that stop before failure.
- `RUL_FD001.txt` contains the true remaining useful life at the final observed cycle for each test engine.

The test data and RUL truth are used only after model development to measure performance on previously unseen engine trajectories.

## Important methodology rules

1. `unit` identifies the simulated engine and is not used as a predictive feature.
2. `max_cycle` may be calculated on training trajectories to construct the RUL target, but it must **never** be supplied to the model as an input feature because it reveals future failure timing.
3. Train/validation splitting must be performed by engine (`unit`), not by randomly splitting individual cycle rows.
4. The final test evaluation uses NASA's separate FD001 test trajectories and RUL truth.
5. Risk bands produced later in the project are illustrative analytical categories for portfolio decision support, not certified aviation maintenance limits.

## Data provenance

Cite the dataset as:

A. Saxena and K. Goebel (2008), *Turbofan Engine Degradation Simulation Data Set*, NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA.

Raw NASA source files should remain unmodified. Generated analytical files belong in `data/processed/` and `data/powerbi/`.
