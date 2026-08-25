
# Transjakarta Demand & Service Analysis

A data analysis project looking at passenger demand, service access, and data quality
across the Transjakarta bus network. Framed as if the analysis was done for Transjakarta's
Operations & Planning team.

## Data disclosure

This project uses the dataset **`dikisahkan/transjakarta-transportation-transaction`**
(Kaggle). The transaction records were generated using the Faker library, on top of
Transjakarta's real corridor, stop, and route structure. In short: the routes and stops are
real, but the individual passenger transactions are not.

Because of that, this project is meant to show analytical skill (cleaning data, exploring
it, and turning findings into recommendations) rather than report real Transjakarta
ridership numbers. Anywhere a finding would need real operational data to confirm (bus
counts, schedules, fare revenue), that is stated clearly instead of implied.

Dataset source: https://www.kaggle.com/datasets/dikisahkan/transjakarta-transportation-transaction

## Objective

Analyze passenger transaction data to understand demand patterns across corridors and time
periods, spot signals of possible capacity pressure, flag data quality issues, and turn all
of that into clear recommendations, while being upfront about what the data can and can't
prove. Note: this covers demand density (where trips are concentrated), not a true service
access-gap analysis - that would require population/census data cross-referenced against stop
coverage, which is out of scope here and called out as such in the dashboard's Data Quality tab.

## Dataset

* 37,900 transaction records from April 2023
* 22 columns: transaction ID, pay card details (bank, sex, birth year), corridor and stop
  IDs and names, tap in and tap out coordinates and timestamps, fare amount
* About 6% of records are missing data, mostly in the corridor, stop, and tap out fields
  (this is a consistent pattern, not random corruption)

## Methodology

1. **Load** the data with DuckDB (`read_csv_auto`) for fast SQL based exploration, checked
   again with pandas
2. **Clean** it: parse timestamps, calculate trip duration, calculate passenger age, and
   flag peak hours and weekday/weekend
3. **Flag data quality** : use missing tap out/corridor/timestamp records as a signal for
   possible system reliability issues, not as an outlier detector. (Trip duration in this
   dataset is capped between 15 and 180 minutes by design, so there are no real outliers to
   find there.)
4. **Analyze** : 12 structured questions covering demand patterns, service access, data
   quality, and recommendations (see `transjakarta_analysis.ipynb`) - all 12 questions are
   reflected in the dashboard (`app.py`), including the daily volume trend (Q2), payment mix
   by corridor (Q7), and an Idul Fitri cuti bersama annotation added to the daily trend chart
   as a reminder to check demand patterns against known calendar disruptions
5. **Summarize** : findings are labeled by how confident we can be in them: directly
   supported by the data, or a hypothesis that would need real operational data to confirm

## Tech stack

Python, DuckDB, pandas, matplotlib (notebook charts), Plotly (interactive dashboard charts),
Streamlit

## Repository structure

```
app.py                          interactive Streamlit dashboard (see "Run the dashboard" below)
.streamlit/config.toml          dashboard theme
transjakarta.csv                dataset copy used by app.py
transjakarta_analysis.ipynb     the full analysis notebook (Q1 to Q12)
README.md                       this file
Docs/EXECUTIVE_BRIEF.md         summary of findings and recommendations
Transjakarta.csv                the dataset (or fetch it from Kaggle, see above)
```

language## How to run the notebook

```bash
pip install duckdb pandas matplotlib jupyter scipy
jupyter notebook transjakarta_analysis.ipynb
```

bashOn Kaggle, add the dataset through "Add Data" and point `read_csv_auto()` at the path shown
under `/kaggle/input/`. Double check the exact filename first: Kaggle reuploads sometimes
rename the source CSV.

## Run the dashboard

```bash
pip install -r requirements.txt
streamlit run app.py
```

bashOr deploy directly on Streamlit Community Cloud pointed at `app.py` - `transjakarta.csv` and
the theme in `.streamlit/config.toml` ship with the repo, so it works with zero setup.

## Related project

This project pairs with an [Olist Brazilian E-Commerce](https://github.com/timothyevanheriawan-commits/olist-ecommerce-analysis) analysis in the same portfolio.
That one covers e-commerce and logistics analytics on real transaction data. This one covers
transit and urban mobility analytics on synthetic data built over a real network structure.
Together they show range across domains, and an honest approach to where the data actually
comes from.
