# PID Stops Cleaning & EDA

**Dataset**: [PID Stops JSON](https://data.pid.cz/stops/json/stops.json)

## About
This project demonstrates a complete data‑cleaning workflow using public transportation stop data from Prague Integrated Transport (PID).
We will:
1. Load the raw JSON feed.
2. Inspect and understand the schema.
3. Clean duplicates, handle missing fields, and normalise data types.
4. Export a tidy CSV/XLSX.
5. Generate an automated EDA report.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the notebooks
1. Download `stops.json` into `data/raw/`.
2. Launch JupyterLab:
   ```bash
   jupyter lab
   ```
3. Open `notebooks/01_overview.ipynb` and execute cells in order.
4. Continue with `02_cleaning.ipynb` and `03_report.ipynb`.

## Outputs
* Cleaned data → `data/clean/`
* PDF/HTML EDA report → `output/` (generated later)

## License
The source dataset is public domain (PID). All code here is MIT‑licensed.
