# Transjakarta Demand & Service Analysis: Executive Brief

**Prepared for:** Transjakarta Operations & Planning Division (framing)
**Data:** Synthetic transaction data (Faker) built on Transjakarta's real network structure, April 2023.
See `README.md` for the full data disclosure.

---

## At a glance

| # | Finding | Confidence | What would confirm it |
|---|---|---|---|
| 1 | Weekday demand about 4.6x higher than weekend | **Strong** | Already holds across a full month, would carry over directly to real ridership data |
| 2 | Cibubur to Balai Kota is busiest and most volatile | **Moderate** | Real bus counts and schedule data, to tell demand apart from actual capacity pressure |
| 3 | Evening peak trips take longer than morning peak | **Moderate** | Real GPS/AVL data, since duration here is generated within a fixed 15 to 180 min range, not measured |
| 4 | Gender split varies notably by corridor | **Moderate** | Real, non-synthetic demographic data before it can inform any service decision |
| 5 | Missing-record rate is slightly higher in some corridors | **Weak** | A larger or real sample, current gap (8.6% to 11% vs. 6% baseline) sits close to noise on small n |

Full reasoning for each finding is below. The short version: only #1 is strong enough to act
on directly. Everything else needs real operational data before it should drive a decision.

## Findings

Each finding is labeled by how much you should trust it: **Strong** (large sample, clear
pattern), **Moderate** (a real pattern, but you'd want more context before acting on it), or
**Weak** (a pattern exists, but the sample size or data limits mean it shouldn't drive
decisions yet).

### 1. Weekday demand is about 4.6 times higher than weekend demand. Strong.
Weekday average: 1,709.9 trips per day. Weekend average: 370.2 trips per day. This gap holds
across a full month of data, so it's not a small sample fluke.

### 2. Cibubur to Balai Kota is the busiest and most unpredictable corridor. Moderate.
It has the highest transaction volume in the dataset (391 trips) and the most day to day
swings of any top corridor. That combination, high and uneven demand, is a reasonable
signal of possible capacity pressure. But it doesn't confirm actual overcrowding, since we
don't have bus counts or schedule data to check against.

### 3. Evening peak trips take longer than morning peak or off peak trips. Moderate.
Average duration: 83.8 minutes in the evening peak, versus 60.1 minutes in the morning peak
and 71.9 minutes off peak. This is an interesting pattern in the data, but trip duration
here is generated within a fixed 15 to 180 minute range rather than measured from real
buses. So treat this as something worth checking again with real GPS data, not as proof of
evening congestion.

### 4. Gender split varies a lot by corridor. Moderate.
Most top corridors lean male (Ciputat to CSW: 67.1% male, Cibubur to Balai Kota: 59.3% male,
Harmoni to Jakarta International Stadium: 62.4% male). But two corridors are close to
balanced or lean female (Kebayoran Lama to Tanah Abang: 52.3% female, Pulo Gadung to Monas:
51.3% female). This kind of split is exactly what you'd want to know before deciding where
to add services like priority seating or women only buses. But since this is synthetic
data, it can't justify a real decision on its own.

### 5. Missing records are slightly higher in some corridors, but are not strongly concentrated. Weak.
Some corridors show incomplete-record rates around 8.6% to 11%, compared with a dataset wide
average of about 6%. But these corridors have relatively small sample sizes, and the rates
are fairly close together. The pattern is also consistent across days of the week:
incomplete-record rates range from 10.12% on Tuesday to 11.59% on Sunday, a difference of
only 1.47 percentage points. This suggests incomplete records are not strongly concentrated
in a particular corridor or day.

Treat this as a data quality monitoring issue rather than an immediate operational problem.
Keep tracking incomplete records across corridors and time periods, and investigate further
using a larger or real transaction dataset before allocating resources to a specific
location or day.

---

## Recommendations

### 1. Review peak hour capacity on high demand, high swing corridors, but confirm first
Corridors like Cibubur to Balai Kota show demand patterns worth a closer look for possible
schedule or fleet changes. Before moving any buses around, check this against real bus
counts and schedules. The transaction data shows demand, not capacity, so it can point you
toward the right corridors to check, not confirm there's actually a shortage.

### 2. Adjust weekend schedules to match the much lower weekend demand
This is the strongest, best supported finding here. If weekend schedules aren't already
scaled down to match, this is a low risk place to start, since the demand gap is large
enough to hold up even with the usual caveats about synthetic data.

### 3. Monitor incomplete transaction records rather than targeting a specific corridor or day
Incomplete-record rates vary only modestly across both corridors and days of the week.
Rather than reacting to small differences in the current synthetic sample, keep monitoring
data completeness and validate the pattern using a larger or real transaction dataset before
directing maintenance or inspection resources to a specific corridor or day.

---

## What this analysis can't tell us

- Whether any corridor is actually overcrowded (would need real bus counts and seat capacity)
- Whether the longer evening trip times reflect real congestion (would need real GPS data)
- Whether the missing record pattern is a genuine tap system problem (would need a bigger or real sample)
- Anything about actual Transjakarta ridership, since the transaction data itself is synthetic

These limits are stated directly instead of glossed over. The point of this project is to
show the analytical process: asking good questions, checking sample sizes before drawing
conclusions, and being clear about the line between what the data shows and what it would
take to act on it.