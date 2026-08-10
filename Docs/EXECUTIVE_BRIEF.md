# Transjakarta Demand & Service Analysis: Executive Brief

**Prepared for:** Transjakarta Operations & Planning Division (framing)
**Data:** Synthetic transaction data (Faker) built on Transjakarta's real network structure, April 2023.
See `README.md` for the full data disclosure.

---

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

### 5. Missing records are a bit higher in some corridors, but not clearly concentrated. Weak.
The corridors with the most missing transaction data sit around 8.6% to 11%, compared to
the dataset wide average of about 6%. But these corridors only have 82 to 244 records each,
and the rates are all close together rather than showing one or two clear standouts. This
is more likely just random noise around the average, not a real problem specific to those
corridors. Worth keeping an eye on, not worth acting on yet.

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

### 3. Treat the missing data pattern as something to monitor, not something to act on
Rather than reacting to which corridors have slightly more missing records right now, log
it and check again with a bigger or real dataset later. Acting on a pattern this close to
random noise risks sending maintenance or inspection resources to the wrong places.

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
