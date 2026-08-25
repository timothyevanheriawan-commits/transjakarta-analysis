"""
Transjakarta Demand & Service Explorer - interactive companion to the
transjakarta_analysis.ipynb notebook in this repo.

Run with: streamlit run app.py
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# THEME - "Papan Info": the LED departure board bolted to the wall of a
# TransJakarta halte (bus shelter). Ink-navy panel, amber LED digits for the
# numbers that matter, a cyan "route line" color for anything clickable.
#
# Colors for Streamlit's own UI live in .streamlit/config.toml, not here.
# These constants exist only because Plotly is a separate rendering pipeline
# that doesn't read Streamlit's theme, so chart colors still need to be set
# in Python (via style_fig, below) and kept in sync by hand.
# ----------------------------------------------------------------------------
BG = "#0f1b30"
PANEL = "#16273f"
BORDER = "#2c3f5e"
TEXT = "#eef2f8"
TEXT_DIM = "#8fa0c0"
ACCENT = "#f2a93c"   # LED amber - every primary bar/line
LINE = "#5fc9d8"     # route-line cyan - secondary accent, used sparingly
WARN = "#e0607e"     # signal rose - caveats and alerts only

# Route-line palette for multi-category charts (e.g. payment method mix) -
# picked to look like distinct corridor lines on a transit schematic map,
# not a generic chart-library palette.
QUALITATIVE = ["#f2a93c", "#5fc9d8", "#e0607e", "#7cc47f", "#a78bda", "#e8935a", "#4f8fd9", "#d9c25a"]

REFERENCE_YEAR = 2023  # the month this dataset covers (April 2023)


def _make_favicon(bg_hex, accent_hex, line_hex, size=64):
    """
    A small logomark generated at runtime and passed to st.set_page_config
    as a PIL.Image, instead of an emoji character - renders identically
    regardless of which Streamlit version is installed (page_icon has
    accepted a PIL.Image since early versions; the ":material/name:"
    shortcode has not always been supported).

    Mark is a single horizontal route line with three stop markers - the
    same abstraction used on real transit schematic maps - rather than a
    literal bus glyph, which reads as clip-art at 16x16 and says nothing
    that the three-dot line doesn't already say more clearly.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = size // 6
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=bg_hex)

    y = size * 0.5
    line_w = size * 0.09
    draw.line([(size * 0.16, y), (size * 0.84, y)], fill=line_hex, width=int(line_w))

    stop_r = size * 0.095
    for cx in (size * 0.24, size * 0.5, size * 0.76):
        draw.ellipse(
            [cx - stop_r, y - stop_r, cx + stop_r, y + stop_r],
            fill=accent_hex,
        )
    return img


st.set_page_config(
    page_title="Transjakarta Demand & Service Explorer",
    page_icon=_make_favicon(BG, ACCENT, LINE),
    layout="wide",
)

# ----------------------------------------------------------------------------
# CHART THEME (Plotly) - every chart on this page is Plotly rather than a
# static image, so viewers can hover a bar/point and see the exact value
# instead of eyeballing pixel height against gridlines. Plus Jakarta Sans is
# already loaded on the page (via .streamlit/config.toml's font import), so
# Plotly can reference it directly without a separate font-download step.
# ----------------------------------------------------------------------------
FONT_FAMILY = "Plus Jakarta Sans, sans-serif"


def style_fig(fig, height=380, xaxis_title=None, yaxis_title=None, showlegend=False):
    """Apply the shared 'Papan Info' theme to a Plotly figure and return it."""
    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family=FONT_FAMILY, color=TEXT, size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        showlegend=showlegend,
        legend=dict(font=dict(size=11, color=TEXT_DIM), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PANEL, font=dict(family=FONT_FAMILY, color=TEXT, size=12),
                         bordercolor=BORDER),
        bargap=0.25,
    )
    fig.update_xaxes(gridcolor=BORDER, zerolinecolor=BORDER, title=xaxis_title,
                      color=TEXT_DIM, linecolor=BORDER)
    fig.update_yaxes(gridcolor=BORDER, zerolinecolor=BORDER, title=yaxis_title,
                      color=TEXT_DIM, linecolor=BORDER)
    return fig


CONFIDENCE_COLORS = {"Strong": "#7cc47f", "Moderate": ACCENT, "Weak": WARN}


def confidence_badge(level):
    """Small inline pill next to a 'Quick take' showing how much weight the
    finding can carry - Strong / Moderate / Weak, matching the framework
    used throughout the notebook and the Executive Brief."""
    color = CONFIDENCE_COLORS.get(level, TEXT_DIM)
    st.markdown(
        f'<span style="display:inline-block; font-family:\'JetBrains Mono\',monospace; '
        f'font-size:0.68rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; '
        f'color:{BG}; background:{color}; padding:2px 9px; border-radius:3px; margin-bottom:6px;">'
        f'{level} confidence</span>',
        unsafe_allow_html=True,
    )

# Colors, backgrounds, borders, and the base font are all set natively in
# .streamlit/config.toml - Streamlit's theme engine handles those more
# reliably than DOM selector overrides (it covers widget states like
# focus/hover/selection that hand-written CSS tends to miss). What's left
# below is only what the theme config can't express: the second display
# face (JetBrains Mono, for corridor codes and LED-style numerals), a
# small pixel-perfect section-label style, and the metric value's accent
# color, which is a deliberate design choice rather than something the
# theme's textColor already covers.
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

h1 {{ font-size: 1.7rem; font-weight: 700; }}
h2 {{ font-size: 1.2rem; font-weight: 700; }}
h3 {{ font-size: 1.02rem; font-weight: 600; }}

/* The one deliberate "LED board" touch in the whole app - scoped to short
   section-label text only, never body copy, so the signage nod doesn't
   fight readability on a data-heavy dashboard. */
.section-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {ACCENT};
    border-top: 2px solid {BORDER};
    padding-top: 12px;
    margin-top: 8px;
}}

/* Corridor-code badge - mimics the small monospace route number printed
   on a real halte sign, used wherever a corridor ID appears inline. */
.corridor-badge {{
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.8rem;
    color: {BG};
    background: {ACCENT};
    padding: 1px 8px;
    border-radius: 3px;
    letter-spacing: 0.02em;
}}

.data-disclosure {{
    border: 2px solid {WARN};
    border-left: 6px solid {WARN};
    padding: 14px 18px;
    background: {PANEL};
    font-size: 0.92rem;
    line-height: 1.5;
}}
.data-disclosure b {{ color: {WARN}; }}

[data-testid="stMetric"] {{
    border: 1px solid {BORDER};
    padding: 14px 18px;
    background: {PANEL};
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {TEXT_DIM};
}}
[data-testid="stMetricValue"] {{
    font-family: 'JetBrains Mono', monospace;
    color: {ACCENT};
    font-weight: 700;
    font-size: 1.75rem;
}}

[data-testid="stAlert"] {{
    border-left: 4px solid {LINE};
}}
</style>
""", unsafe_allow_html=True)


def section_label(number, name):
    st.markdown(f'<div class="section-label">{number} &middot; {name}</div>', unsafe_allow_html=True)


def corridor_badge(text):
    return f'<span class="corridor-badge">{text}</span>'


# ----------------------------------------------------------------------------
# DATA LOADING
# ----------------------------------------------------------------------------
BANK_LABELS = {
    "emoney": "e-money (Mandiri)",
    "dki": "JakCard (Bank DKI)",
    "flazz": "Flazz (BCA)",
    "brizzi": "Brizzi (BRI)",
    "bni": "TapCash (BNI)",
    "online": "Online / QR payment",
}


def classify_peak(hour):
    if pd.isna(hour):
        return np.nan
    hour = int(hour)
    if 5 <= hour <= 9:
        return "Morning peak (05:00-09:59)"
    if 16 <= hour <= 20:
        return "Evening peak (16:00-20:59)"
    return "Off-peak"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    df["tapInTime"] = pd.to_datetime(df["tapInTime"], errors="coerce")
    df["tapOutTime"] = pd.to_datetime(df["tapOutTime"], errors="coerce")

    df["_duration_min"] = (df["tapOutTime"] - df["tapInTime"]).dt.total_seconds() / 60
    df["_age"] = REFERENCE_YEAR - df["payCardBirthDate"]
    df["_age_bucket"] = pd.cut(
        df["_age"], bins=[0, 17, 24, 34, 44, 54, 120],
        labels=["Under 18", "18-24", "25-34", "35-44", "45-54", "55+"],
    )
    df["_hour"] = df["tapInTime"].dt.hour
    df["_date"] = df["tapInTime"].dt.date
    df["_day_name"] = df["tapInTime"].dt.day_name()
    df["_is_weekend"] = df["tapInTime"].dt.dayofweek >= 5
    df["_peak_period"] = df["_hour"].apply(classify_peak)
    df["_gender"] = df["payCardSex"].map({"M": "Male", "F": "Female"}).fillna(df["payCardSex"])
    df["_bank_label"] = df["payCardBank"].map(BANK_LABELS).fillna(df["payCardBank"])

    return df


CSV_PATH = "Transjakarta.csv"
if not os.path.exists(CSV_PATH):
    st.error(f"Can't find **{CSV_PATH}** next to app.py. Make sure the dataset CSV ships with the repo.")
    st.stop()

df = load_data(CSV_PATH)
total_trips = len(df)

# Inline SVG instead of an emoji or icon-font shortcode - renders exactly
# the same on every Streamlit version, since it's raw HTML/SVG rather than
# depending on a feature that may or may not be present. Same route-line
# mark as the favicon, for one consistent logomark instead of two unrelated
# icons.
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
            <line x1="3" y1="12" x2="21" y2="12" stroke="{LINE}" stroke-width="2.2"/>
            <circle cx="5.5" cy="12" r="2.4" fill="{ACCENT}"/>
            <circle cx="12" cy="12" r="2.4" fill="{ACCENT}"/>
            <circle cx="18.5" cy="12" r="2.4" fill="{ACCENT}"/>
        </svg>
        <span style="font-size:1.7rem; font-weight:700; color:{TEXT};">Transjakarta Demand &amp; Service Explorer</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    "A plain-language, interactive look at a month of Transjakarta bus-card transactions: "
    "who's riding, when, on which corridors, and how reliable the tap-in/tap-out data itself "
    "is. Everything below is calculated directly from the CSV bundled with this app - nothing "
    "is pulled from the internet or added from outside sources."
)

st.markdown(
    f"""
    <div class="data-disclosure">
    <b>Data disclosure - read this first.</b> This dashboard uses the Kaggle dataset
    <code>dikisahkan/transjakarta-transportation-transaction</code>. The individual passenger
    records were generated with the Faker library, layered on top of Transjakarta's real
    corridor and stop structure - so the routes, stop names, and coordinates are real, but no
    individual trip below reflects an actual rider. That means this app is best read as a
    demonstration of analysis and data-quality thinking, not as a report of real Transjakarta
    ridership. Anywhere a finding would need real operational data to confirm (bus counts,
    schedules, fare revenue), that's called out directly instead of implied.
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# ----------------------------------------------------------------------------
# GLOBAL FILTERS - applied once here, so every tab below reflects the same
# slice of the month instead of each tab silently using the full dataset.
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-weight:700; '
        f'letter-spacing:0.05em; color:{ACCENT};">FILTERS</span>',
        unsafe_allow_html=True,
    )
    st.caption("Applies to every tab. April 1-30, 2023.")

    day_type = st.radio(
        "Day type", ["All days", "Weekdays only", "Weekends only"], index=0, horizontal=False,
    )

    corridor_options = sorted(df["corridorName"].dropna().unique())
    selected_corridors = st.multiselect(
        "Corridor", corridor_options, default=[],
        help="Leave empty to include every corridor.",
    )

    bank_options = sorted(df["_bank_label"].dropna().unique())
    selected_banks = st.multiselect(
        "Payment method", bank_options, default=[],
        help="Leave empty to include every payment method.",
    )

    gender_options = sorted(df["_gender"].dropna().unique())
    selected_genders = st.multiselect(
        "Passenger gender (from card registration)", gender_options, default=[],
    )

    date_min, date_max = df["_date"].min(), df["_date"].max()
    selected_dates = st.slider(
        "Date range", date_min, date_max, (date_min, date_max),
    )

if day_type == "Weekdays only":
    df = df[~df["_is_weekend"]]
elif day_type == "Weekends only":
    df = df[df["_is_weekend"]]
if selected_corridors:
    df = df[df["corridorName"].isin(selected_corridors)]
if selected_banks:
    df = df[df["_bank_label"].isin(selected_banks)]
if selected_genders:
    df = df[df["_gender"].isin(selected_genders)]
if selected_dates != (date_min, date_max):
    df = df[df["_date"].between(selected_dates[0], selected_dates[1])]

if len(df) == 0:
    st.warning(
        "No trips match this combination of filters. Try widening the date range, "
        "or clearing the corridor / payment method / gender selections in the sidebar."
    )
    st.stop()

if len(df) == total_trips:
    st.write(f"**{len(df):,} trips** loaded, spanning April 1 to 30, 2023.")
else:
    st.write(
        f"**{len(df):,} trips** match your filters, out of **{total_trips:,} total** "
        f"in this file. Every tab below reflects this filtered set."
    )

tabs = st.tabs([
    "Overview", "Demand Patterns", "Corridors & Map",
    "Passengers", "Trip Duration", "Data Quality", "Executive Brief",
])

# ============================================================ TAB: OVERVIEW
with tabs[0]:
    section_label("01", "Overview")
    st.subheader("What's in this file")
    st.markdown(
        "Before looking at any chart below, it helps to know how *complete* the data actually "
        "is. Real-world exports almost always have gaps - a trip with no logged tap-out, a "
        "corridor name that never got filled in, and so on. The numbers below give a sense of "
        "how solid the foundation is before drawing conclusions from it."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trips in view", f"{len(df):,}")
    c2.metric("Unique corridors", f"{df['corridorName'].nunique():,}")
    c3.metric("Unique cardholders", f"{df['payCardID'].nunique():,}")
    avg_fare = df["payAmount"].mean()
    c4.metric("Average fare", f"Rp {avg_fare:,.0f}" if pd.notna(avg_fare) else "N/A")

    d1, d2, d3, d4 = st.columns(4)
    free_share = (df["payAmount"] == 0).mean() * 100
    d1.metric("Rp 0 fare trips", f"{free_share:.0f}%", help="Likely transfers within the free-transfer window, not confirmed fare waivers.")
    d2.metric("Female riders", f"{(df['_gender'] == 'Female').mean() * 100:.0f}%")
    weekend_share = df["_is_weekend"].mean() * 100
    d3.metric("Trips on weekends", f"{weekend_share:.0f}%")
    no_tapout = df["tapOutTime"].isna().mean() * 100
    d4.metric("Missing tap-out", f"{no_tapout:.0f}%", help="Trips with a tap-in but no recorded tap-out.")

    st.markdown(
        "**How complete is each column?** The chart below shows the percentage of *missing* "
        "values in the columns that have the most gaps - lower means more reliable to draw "
        "conclusions from."
    )
    missing = (df.isna().mean() * 100).round(1)
    missing = missing[missing > 0].sort_values(ascending=False).head(15).sort_values()
    if len(missing) > 0:
        fig = go.Figure(go.Bar(
            x=missing.values, y=missing.index, orientation="h",
            marker_color=ACCENT,
            hovertemplate="%{y}<br>%{x:.1f}% missing<extra></extra>",
        ))
        style_fig(fig, height=max(220, len(missing) * 32), xaxis_title="% missing")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("No missing values in the current filtered view.")

    st.markdown(
        "**Payment methods in this data.** Six card brands appear, all real Indonesian "
        "e-money products layered onto the synthetic transactions:"
    )
    bank_counts = df["_bank_label"].value_counts()
    fig = go.Figure(go.Bar(
        x=bank_counts.index, y=bank_counts.values,
        marker_color=QUALITATIVE[:len(bank_counts)],
        hovertemplate="%{x}<br>%{y:,} trips<extra></extra>",
    ))
    style_fig(fig, height=340, yaxis_title="Trips")
    st.plotly_chart(fig, use_container_width=True)

# ============================================================ TAB: DEMAND
with tabs[1]:
    section_label("02", "Demand Patterns")
    st.subheader("When people actually ride")

    daily = df.groupby(["_date", "_is_weekend"]).size().reset_index(name="trips")
    wd_avg = daily.loc[~daily["_is_weekend"], "trips"].mean()
    we_avg = daily.loc[daily["_is_weekend"], "trips"].mean()
    if pd.notna(wd_avg) and pd.notna(we_avg) and we_avg > 0:
        ratio = wd_avg / we_avg
        confidence_badge("Strong")
        st.markdown(
            f"**Quick take:** weekday demand averages **{wd_avg:,.0f} trips/day**, versus "
            f"**{we_avg:,.0f} trips/day** on weekends - about **{ratio:.1f}x higher**. This "
            "gap is large enough and consistent enough across the month that it's the single "
            "most trustworthy finding in this dataset (it would very likely hold on real "
            "ridership data too, since day-of-week commuting rhythm isn't something Faker "
            "invents from nothing - it follows the real timestamps in the source data)."
        )
    else:
        st.info("Not enough weekday and weekend data in the current filter to compare the two.")

    st.markdown(
        "**Daily trip volume across April.** Every point is one day's total trips - this is "
        "the shape of the whole month, not just an hour-of-day or day-of-week average."
    )
    daily_all = df.groupby("_date").size().reset_index(name="trips").sort_values("_date")
    fig = go.Figure(go.Scatter(
        x=daily_all["_date"], y=daily_all["trips"], mode="lines+markers",
        line=dict(color=ACCENT, width=2), marker=dict(size=5, color=ACCENT),
        hovertemplate="%{x|%a, %b %d}<br>%{y:,} trips<extra></extra>",
    ))
    # Cuti bersama Idul Fitri 2023 ran Apr 19-25 - shaded so the dip (or lack of
    # one, in this synthetic sample) is visible in context, since a real analyst
    # would ask about this before trusting a weekday/weekend average from this month.
    lebaran_start, lebaran_end = pd.Timestamp("2023-04-19"), pd.Timestamp("2023-04-25")
    if daily_all["_date"].min() <= lebaran_end.date() and daily_all["_date"].max() >= lebaran_start.date():
        fig.add_vrect(x0=lebaran_start, x1=lebaran_end, fillcolor=WARN, opacity=0.12, line_width=0)
    style_fig(fig, height=360, yaxis_title="Trips")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Shaded band: Idul Fitri cuti bersama (Apr 19-25, 2023), the largest national travel "
        "disruption of the month. Worth checking before trusting any weekday/weekend average "
        "from this dataset - a real Lebaran period would depress or reshape weekday ridership, "
        "and this synthetic dataset may or may not model that (see Data Quality tab for how "
        "much to trust findings drawn from a single month)."
    )

    st.markdown(
        "**Trips by hour of day.** The two humps below are the morning and evening commute - "
        "shaded to match the peak windows used throughout this app."
    )
    hourly = df["_hour"].value_counts().reindex(range(24), fill_value=0).sort_index()
    fig = go.Figure(go.Bar(
        x=hourly.index, y=hourly.values, marker_color=ACCENT,
        hovertemplate="%{x}:00<br>%{y:,} trips<extra></extra>",
    ))
    fig.add_vrect(x0=4.5, x1=9.5, fillcolor=LINE, opacity=0.12, line_width=0)
    fig.add_vrect(x0=15.5, x1=20.5, fillcolor=LINE, opacity=0.12, line_width=0)
    style_fig(fig, height=360, xaxis_title="Hour of day (tap-in)", yaxis_title="Trips")
    fig.update_xaxes(dtick=2)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Shaded bands mark the morning peak (05:00-09:59) and evening peak (16:00-20:59) used "
        "on the Trip Duration tab. Everything outside those bands is treated as off-peak."
    )

    st.markdown("**Trips by day of week.**")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = df["_day_name"].value_counts().reindex(order, fill_value=0)
    colors = [ACCENT if d not in ("Saturday", "Sunday") else LINE for d in order]
    fig = go.Figure(go.Bar(
        x=by_day.index, y=by_day.values, marker_color=colors,
        hovertemplate="%{x}<br>%{y:,} trips<extra></extra>",
    ))
    style_fig(fig, height=360, yaxis_title="Trips")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Amber bars are weekdays, cyan bars are the weekend, so the drop is visible at a glance.")

# ============================================================ TAB: CORRIDORS
with tabs[2]:
    section_label("03", "Corridors & Map")
    st.subheader("Which routes carry the most people")

    corridor_counts = df["corridorName"].value_counts()
    if len(corridor_counts) > 0:
        busiest_name = corridor_counts.index[0]
        busiest_count = int(corridor_counts.iloc[0])

        top10 = corridor_counts.head(10)
        daily_by_corridor = df[df["corridorName"].isin(top10.index)].groupby(
            ["corridorName", "_date"]
        ).size().reset_index(name="trips")
        volatility = daily_by_corridor.groupby("corridorName")["trips"].std().sort_values(ascending=False)
        most_volatile = volatility.index[0] if len(volatility) > 0 else None

        confidence_badge("Moderate")
        st.markdown(
            f"**Quick take:** {corridor_badge(busiest_name)} is the busiest corridor in this "
            f"view, with **{busiest_count:,} trips**. Among the top 10 by volume, "
            f"{corridor_badge(most_volatile) if most_volatile else 'N/A'} swings the most from "
            "day to day - a combination of high and uneven demand that's worth a closer look, "
            "though this alone can't confirm actual overcrowding without real bus-count data.",
            unsafe_allow_html=True,
        )

    st.markdown("**Top 15 corridors by trip volume.**")
    top15 = corridor_counts.head(15).sort_values()
    fig = go.Figure(go.Bar(
        x=top15.values, y=top15.index, orientation="h", marker_color=ACCENT,
        hovertemplate="%{y}<br>%{x:,} trips<extra></extra>",
    ))
    style_fig(fig, height=460, xaxis_title="Trips")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Day-to-day volatility, top 10 corridors.** A higher bar means that corridor's daily "
        "trip count swings more from one day to the next - useful for spotting corridors where "
        "a fixed schedule might be a worse fit than one built for high demand variance."
    )
    if len(volatility) > 0:
        vol_sorted = volatility.sort_values()
        fig = go.Figure(go.Bar(
            x=vol_sorted.values, y=vol_sorted.index, orientation="h", marker_color=LINE,
            hovertemplate="%{y}<br>std. dev. %{x:.1f} trips/day<extra></extra>",
        ))
        style_fig(fig, height=360, xaxis_title="Std. dev. of trips/day")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Where trips start.** Every dot is a real stop location, sized by how many tap-ins happened there.")
    stop_points = (
        df.dropna(subset=["tapInStopsLat", "tapInStopsLon"])
        .groupby(["tapInStopsName", "tapInStopsLat", "tapInStopsLon"])
        .size()
        .reset_index(name="trips")
        .rename(columns={"tapInStopsLat": "lat", "tapInStopsLon": "lon"})
    )
    if len(stop_points) > 0:
        st.map(stop_points, latitude="lat", longitude="lon", size="trips", color="#f2a93c")
        st.caption(
            f"{len(stop_points):,} distinct tap-in stops shown, covering the corridors in the "
            "current filter. Stop names and coordinates are real Transjakarta network data; "
            "only the trip counts riding on top of them are synthetic."
        )
    else:
        st.info("No tap-in coordinates available for the current filter.")

# ============================================================ TAB: PASSENGERS
with tabs[3]:
    section_label("04", "Passengers")
    st.subheader("Who's on the card")
    st.caption(
        "Card registration data (gender, birth year) - not a survey of who's physically riding, "
        "just who the card is registered to."
    )

    gender_counts = df["_gender"].value_counts()
    if len(gender_counts) > 0:
        top_gender = gender_counts.index[0]
        top_share = gender_counts.iloc[0] / gender_counts.sum() * 100
        confidence_badge("Moderate")
        st.markdown(
            f"**Quick take:** **{top_gender}**-registered cards account for **{top_share:.0f}%** "
            "of trips in the current filter. This split varies a fair amount by corridor - try "
            "filtering to a single corridor in the sidebar to see it shift."
        )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Gender split.**")
        fig = go.Figure(go.Bar(
            x=gender_counts.index, y=gender_counts.values,
            marker_color=[ACCENT, LINE][:len(gender_counts)],
            hovertemplate="%{x}<br>%{y:,} trips<extra></extra>",
        ))
        style_fig(fig, height=340, yaxis_title="Trips")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("**Age distribution.**")
        ages = df["_age"].dropna()
        ages = ages[(ages >= 10) & (ages <= 85)]
        fig = go.Figure(go.Histogram(
            x=ages, nbinsx=25, marker_color=ACCENT, marker_line_color=BG, marker_line_width=1,
            hovertemplate="Age %{x}<br>%{y:,} trips<extra></extra>",
        ))
        style_fig(fig, height=340, xaxis_title="Age (years)", yaxis_title="Trips")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Fare paid per trip.** A large cluster at Rp 0 is expected - Transjakarta's transfer window lets riders continue a trip without paying again.")
    fares = df["payAmount"].dropna()
    fig = go.Figure(go.Histogram(
        x=fares, nbinsx=30, marker_color=ACCENT, marker_line_color=BG, marker_line_width=1,
        hovertemplate="Rp %{x:,.0f}<br>%{y:,} trips<extra></extra>",
    ))
    style_fig(fig, height=320, xaxis_title="Fare (Rp)", yaxis_title="Trips")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "**Payment method mix, top 5 corridors.** Whether one payment brand dominates a "
        "corridor, or riders there use a healthier mix - relevant if a bank partnership or "
        "top-up campaign were ever being considered for a specific route."
    )
    top5_corridors = df["corridorName"].value_counts().head(5).index
    pay_mix = (
        df[df["corridorName"].isin(top5_corridors)]
        .groupby(["corridorName", "_bank_label"]).size()
        .unstack(fill_value=0)
    )
    pay_mix = pay_mix.loc[top5_corridors]  # keep corridors ordered by overall volume
    pay_mix_pct = pay_mix.div(pay_mix.sum(axis=1), axis=0) * 100
    if len(pay_mix_pct) > 0:
        fig = go.Figure()
        for i, bank in enumerate(pay_mix_pct.columns):
            fig.add_trace(go.Bar(
                name=bank, x=pay_mix_pct.index, y=pay_mix_pct[bank],
                marker_color=QUALITATIVE[i % len(QUALITATIVE)],
                hovertemplate=f"{bank}" + "<br>%{x}<br>%{y:.0f}%<extra></extra>",
            ))
        fig.update_layout(barmode="stack")
        style_fig(fig, height=400, yaxis_title="% of trips", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough corridors in the current filter to show a payment-method breakdown.")

# ============================================================ TAB: DURATION
with tabs[4]:
    section_label("05", "Trip Duration")
    st.subheader("How long trips take")
    st.markdown(
        f"""
        <div class="data-disclosure">
        <b>Caveat.</b> Trip duration in this dataset is generated within a fixed 15-180 minute
        range by design, not measured from real GPS or AVL data. Patterns below are worth
        checking again against real operational data - they're not proof of actual congestion
        or schedule performance.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    durations = df["_duration_min"].dropna()
    by_peak = df.dropna(subset=["_duration_min", "_peak_period"]).groupby("_peak_period")["_duration_min"].mean()
    order = ["Morning peak (05:00-09:59)", "Off-peak", "Evening peak (16:00-20:59)"]
    by_peak = by_peak.reindex([o for o in order if o in by_peak.index])

    if len(by_peak) >= 2:
        longest = by_peak.idxmax()
        shortest = by_peak.idxmin()
        confidence_badge("Moderate")
        st.markdown(
            f"**Quick take:** average trip duration is longest in the **{longest}** window "
            f"(**{by_peak.max():.0f} min**) and shortest in the **{shortest}** window "
            f"(**{by_peak.min():.0f} min**) among the current filter."
        )

    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown("**Average duration by time window.**")
        if len(by_peak) > 0:
            fig = go.Figure(go.Bar(
                x=by_peak.index, y=by_peak.values,
                marker_color=[LINE, ACCENT, WARN][:len(by_peak)],
                hovertemplate="%{x}<br>%{y:.0f} min avg<extra></extra>",
            ))
            style_fig(fig, height=380, yaxis_title="Avg. duration (min)")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("**Overall duration distribution.**")
        fig = go.Figure(go.Histogram(
            x=durations, nbinsx=30, marker_color=ACCENT, marker_line_color=BG, marker_line_width=1,
            hovertemplate="%{x:.0f} min<br>%{y:,} trips<extra></extra>",
        ))
        style_fig(fig, height=380, xaxis_title="Duration (minutes)", yaxis_title="Trips")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================ TAB: DATA QUALITY
with tabs[5]:
    section_label("06", "Data Quality")
    st.subheader("How much to trust each finding")
    st.markdown(
        "This project labels every finding by how much weight it can carry, borrowed from the "
        "notebook's own framework:"
    )
    st.markdown(
        "- **Strong** - a large, consistent pattern that would very likely hold on real data too "
        "(e.g. the weekday/weekend gap on the Demand Patterns tab).\n"
        "- **Moderate** - a real pattern in this sample, but one that needs real operational data "
        "before it should drive a decision (e.g. corridor volatility, trip duration by time of day).\n"
        "- **Weak** - a pattern exists, but the sample size is small enough that it's closer to "
        "noise than signal (e.g. small differences in missing-record rates below)."
    )

    st.markdown("**Missing tap-out or corridor data, by corridor (top 10 highest rate, min. 20 trips).**")
    corridor_group = df.groupby("corridorName")
    missing_by_corridor = corridor_group.apply(
        lambda g: g[["tapOutTime", "corridorID"]].isna().any(axis=1).mean() * 100
    )
    sizes = corridor_group.size()
    missing_by_corridor = missing_by_corridor[sizes >= 20].sort_values(ascending=False).head(10).sort_values()
    if len(missing_by_corridor) > 0:
        confidence_badge("Weak")
        fig = go.Figure(go.Bar(
            x=missing_by_corridor.values, y=missing_by_corridor.index, orientation="h",
            marker_color=WARN,
            hovertemplate="%{y}<br>%{x:.1f}% of trips have a gap<extra></extra>",
        ))
        style_fig(fig, height=360, xaxis_title="% of trips with a gap")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Weak signal by design: these corridors have relatively small sample sizes, so a "
            "few incomplete records move the percentage a lot. Read this as something to keep "
            "monitoring, not a corridor to act on directly."
        )
    else:
        st.info("Not enough corridors with 20+ trips in the current filter to compare.")

    st.markdown("**Missing tap-out or corridor data, by day of week.**")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    missing_by_day = df.groupby("_day_name").apply(
        lambda g: g[["tapOutTime", "corridorID"]].isna().any(axis=1).mean() * 100
    ).reindex(order)
    colors = [ACCENT if d not in ("Saturday", "Sunday") else LINE for d in order]
    fig = go.Figure(go.Bar(
        x=missing_by_day.index, y=missing_by_day.values, marker_color=colors,
        hovertemplate="%{x}<br>%{y:.1f}% of trips have a gap<extra></extra>",
    ))
    style_fig(fig, height=320, yaxis_title="% of trips with a gap")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "If these bars sit close together (as they typically do across the full month), that's "
        "itself the finding: incomplete records aren't concentrated on a particular day, which "
        "points toward a general data-capture issue rather than a day-specific one."
    )

    st.markdown(
        """
        <div class="data-disclosure">
        <b>Scope note.</b> The Corridors & Map tab shows where trip <i>demand</i> is concentrated,
        not where service <i>access</i> is genuinely weak. A true access-gap analysis - identifying
        underserved areas relative to population - would need census or population-density data
        cross-referenced against stop coverage, which isn't part of this dataset. Treat the map as
        a demand-density view, not a service-equity finding.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================ TAB: EXECUTIVE BRIEF
with tabs[6]:
    section_label("07", "Executive Brief")
    st.subheader("Findings and recommendations, synthesized")
    st.caption(
        "The same document that lives at `Docs/EXECUTIVE_BRIEF.md` in the repository, rendered "
        "here so it's visible without leaving the dashboard."
    )
    brief_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Docs", "EXECUTIVE_BRIEF.md")
    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_text = f.read()
        st.markdown(brief_text)
    except FileNotFoundError:
        st.warning(
            "Couldn't find `Docs/EXECUTIVE_BRIEF.md` next to app.py - make sure the `Docs` "
            "folder ships with the repo alongside app.py."
        )

st.divider()
st.caption(
    "This dashboard filters and re-aggregates live from the bundled CSV - nothing shown here "
    "is pre-computed or cached from the notebook. For the full 12-question analysis and the "
    "executive brief this app is based on, see `transjakarta_analysis.ipynb` and "
    "`Docs/EXECUTIVE_BRIEF.md` in the repository."
)
st.caption(
    "Data: [Transjakarta Transportation Transaction](https://www.kaggle.com/datasets/dikisahkan/transjakarta-transportation-transaction) "
    "by dikisahkan on Kaggle - synthetic transaction records generated with Faker, over "
    "Transjakarta's real corridor and stop network."
)