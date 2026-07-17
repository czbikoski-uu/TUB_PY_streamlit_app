import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

# ── Palette ──────────────────────────────────────────────────────────────────
COUNTRY_COLORS = {
    "Finland":  "#440154",
    "Poland":   "#414487",
    "Germany":  "#2a788e",
    "Romania":  "#22a884",
    "Italy":    "#7ad151",
    "Spain":    "#fde725",
}
RICHNESS_COLORS = px.colors.sample_colorscale("Viridis", 5)
COUNTRY_ORDER   = ["Finland", "Poland", "Germany", "Romania", "Italy", "Spain"]
RICHNESS_ORDER  = {"richness_class": ["1", "2", "3", "4", "5"]}

pio.templates.default = "plotly_white"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FunDivEUROPE: BEF Dashboard",
    page_icon="🌳",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }

    .compare-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.25rem;
    }
    .compare-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #22a884;
        margin-bottom: 0.15rem;
    }
    .compare-note {
        font-size: 0.72rem;
        color: #9ca3af;
    }

    .biome-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
        margin-top: 0.5rem;
    }
    .biome-table td {
        padding: 0.3rem 0.6rem;
        border-bottom: 1px solid #f0f0f0;
    }
    .biome-table td:first-child {
        font-weight: 600;
        white-space: nowrap;
    }
    .biome-table td:last-child {
        color: #6b7280;
    }

    .stAlert { padding: 0.65rem 1rem; border-radius: 6px; }

    div[data-testid="metric-container"] {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.9rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Load & cache data ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("FunDivEUROPE_alldata_exploratory-platform_2023.xlsx")
    df = df.rename(columns={
        "soil_c_ff_10":  "soil_C_ff_10",
        "soil_cn_ff_10": "soil_CN_ff_10",
        "lai":           "LAI",
        "wue":           "WUE",
    })
    df["slope"] = df["slope"].replace({1: "flat", 2: "medium", 3: "steep"})
    df["no_pathogen_damage"] = df["no_pathogen_damage"] * 100
    df["richness_category"] = pd.cut(
        df["target_species_richness"],
        bins=[0, 1, 3, 5],
        labels=["monoculture", "low", "high"],
        include_lowest=True,
    )
    df["richness_class"] = df["target_species_richness"].astype(str)
    df["biome"] = df["country"].replace({
        "Finland": "Boreal",
        "Poland":  "Hemiboreal",
        "Germany": "Temperate Deciduous",
        "Romania": "Mountainous Deciduous",
        "Italy":   "Thermophilous Deciduous",
        "Spain":   "Mediterranean Mixed",
    })
    return df

data = load_data()

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🌳 FunDivEUROPE: Biodiversity & Ecosystem Functioning")
st.markdown(
    "**Does tree diversity improve ecosystem functioning in European forests?** "
    "Exploring BEF relationships across 209 mature forest plots in six European countries — "
    "from boreal Finland to Mediterranean Spain."
)

# ── Biome reference table ─────────────────────────────────────────────────────
with st.expander("🗺️ Study regions — click to see the six biomes"):
    st.markdown("""
    <table class="biome-table">
        <tr><td> Finland</td><td>Boreal</td><td>Cold, conifer-dominated, low diversity</td></tr>
        <tr><td> Poland</td><td>Hemiboreal</td><td>Transitional boreal-temperate mixed forest</td></tr>
        <tr><td> Germany</td><td>Temperate Deciduous</td><td>Broadleaf forest, moderate climate</td></tr>
        <tr><td> Romania</td><td>Mountainous Deciduous</td><td>High-altitude broadleaf, highest biomass</td></tr>
        <tr><td> Italy</td><td>Thermophilous Deciduous</td><td>Warm-adapted broadleaf, drought-sensitive</td></tr>
        <tr><td>☀ Spain</td><td>Mediterranean Mixed</td><td>Drought-adapted, lowest resistance, highest recovery</td></tr>
    </table>
    <p style="font-size:0.72rem; color:#9ca3af; margin-top:0.5rem;">
        Countries are ordered cold → warm throughout the dashboard.
    </p>
    """, unsafe_allow_html=True)

st.divider()

# ── Sidebar filter ───────────────────────────────────────────────────────────
st.sidebar.header("Filter plots 🔍")
st.sidebar.markdown("All charts update live.")

selected_countries = st.sidebar.multiselect(
    "Country",
    options=COUNTRY_ORDER,
    default=COUNTRY_ORDER,
)
selected_richness = st.sidebar.multiselect(
    "Target species richness",
    options=["1", "2", "3", "4", "5"],
    default=["1", "2", "3", "4", "5"],
)

filtered = data.loc[
    data["country"].isin(selected_countries)
    & data["richness_class"].isin(selected_richness)
]

# ── KPI section ───────────────────────────────────────────────────────────────
st.subheader("The study at a glance")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Forest plots",       f"{len(filtered)}",
          help="Each plot is a 30×30 m mature stand.")
k2.metric("Countries / biomes", f"{filtered['country'].nunique()} / 6",
          help="Ordered Finland → Spain, coldest to warmest.")
k3.metric("Avg tree biomass",   f"{filtered['tree_biomass'].mean():.0f} Mg C ha⁻¹",
          help="Aboveground carbon stock.")
k4.metric("Avg annual growth",  f"{filtered['tree_growth'].mean():.2f} Mg C ha⁻¹ yr⁻¹",
          help="Annual wood production — a flux, not a stock.")
k5.metric("Avg Shannon index",  f"{filtered['shannon_diversity'].mean():.2f}",
          help="0 = one species dominant; higher = more evenly diverse.")

# BEF comparison row
mono_biomass  = data.loc[data["richness_class"] == "1",          "tree_biomass"].mean()
high_biomass  = data.loc[data["richness_class"].isin(["4","5"]), "tree_biomass"].mean()
mono_growth   = data.loc[data["richness_class"] == "1",          "tree_growth"].mean()
high_growth   = data.loc[data["richness_class"].isin(["4","5"]), "tree_growth"].mean()
biomass_delta = high_biomass - mono_biomass
growth_delta  = high_growth  - mono_growth

st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 1, 2])

c1.markdown(f"""
    <div class="compare-label">🌿 Biomass — diverse vs. monoculture</div>
    <div class="compare-value">+{biomass_delta:.0f} Mg C ha⁻¹</div>
    <div class="compare-note">richness 4–5 vs. richness 1, all 209 plots</div>
""", unsafe_allow_html=True)

c2.markdown(f"""
    <div class="compare-label">📈 Growth — diverse vs. monoculture</div>
    <div class="compare-value">+{growth_delta:.2f} Mg C ha⁻¹ yr⁻¹</div>
    <div class="compare-note">richness 4–5 vs. richness 1, all 209 plots</div>
""", unsafe_allow_html=True)

c3.info(
    "💡 Diverse plots store and produce modestly more carbon than monocultures — "
    "but this effect is much smaller than the differences between countries. "
    "**The dominant story turns out to be region, not richness.**"
)

st.divider()

# ── Section 1: Where are these forests? ──────────────────────────────────────
st.header("1: Where are these forests?")
st.info(
    "📍 The six regions span Europe's full climate gradient, from cold boreal Finland "
    "to drought-adapted Mediterranean Spain. Plots were selected to separate richness "
    "from topography and soil — mimicking a controlled experiment in real forests."
)

fig_map = px.scatter_geo(
    filtered,
    lat="latitude",
    lon="longitude",
    color="country",
    color_discrete_map=COUNTRY_COLORS,
    category_orders={"country": COUNTRY_ORDER},
    hover_name="country",
    hover_data={"target_species_richness": True, "tree_biomass": ":.1f"},
    projection="natural earth",
    title="FunDivEUROPE Plot Locations",
    labels={"country": "Country"},
    height=580,
)
fig_map.update_geos(
    showcountries=True,
    showcoastlines=True,
    showland=True,
    landcolor="#f3f4f6",
    countrycolor="#d1d5db",
    coastlinecolor="#d1d5db",
    lataxis_range=[35, 72],
    lonaxis_range=[-10, 40],
)
fig_map.update_layout(
    legend_title_text="Country",
    margin={"t": 40, "b": 0, "l": 0, "r": 0},
    paper_bgcolor="white",
)
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ── Section 2: Species composition & richness ─────────────────────────────────
st.header("2: Who grows where — and how diverse are these forests?")
st.info(
    "🌿 Each country hosts a distinct set of tree species shaped by its climate. "
    "The sunburst shows which target species dominate each region. "
    "The Shannon index confirms that higher target richness translates to genuinely more diverse stands."
)

# Sunburst data prep (uses full filtered data, species columns only)
species_cols = list(data.loc[:, "Pinus.sylvestris":"Pinus.nigra"].columns)

data_sunburst = filtered[["country"] + species_cols].copy()
data_sunburst_long = pd.melt(
    data_sunburst,
    id_vars=["country"],
    var_name="species",
    value_name="count",
)
# Only keep species actually present in selected countries
data_sunburst_long = data_sunburst_long[data_sunburst_long["count"] > 0]

col_sun, col_shannon = st.columns([1.1, 0.9])

fig_sunburst = px.sunburst(
    data_sunburst_long,
    path=["country", "species"],
    values="count",
    color="country",
    color_discrete_map=COUNTRY_COLORS,
    title="Target Species Composition by Country",
    height=520,
)
fig_sunburst.update_traces(
    textinfo="label+percent parent",
    insidetextorientation="radial",
)
fig_sunburst.update_layout(margin={"t": 40, "b": 0, "l": 0, "r": 0})
col_sun.plotly_chart(fig_sunburst, use_container_width=True)

fig_shannon = px.box(
    filtered,
    x="richness_class", y="shannon_diversity",
    color="richness_class",
    color_discrete_sequence=RICHNESS_COLORS,
    category_orders=RICHNESS_ORDER,
    labels={"richness_class": "Target species richness", "shannon_diversity": "Shannon diversity index"},
    title="Shannon Diversity Across Target Richness Classes",
    height=520,
)
fig_shannon.update_layout(showlegend=False)
col_shannon.plotly_chart(fig_shannon, use_container_width=True)

st.divider()

# ── Section 3: BEF question ───────────────────────────────────────────────────
st.header("3: Does richness drive biomass? The BEF question")
st.info(
    "⚖️ Richness moves biomass modestly — a 1.3× range from richness 1 to 5. "
    "Country drives a 3.7× range (51 to 187 Mg C ha⁻¹). "
    "**The BEF signal exists, but it is overwhelmed by where in Europe the forest is.**"
)

# Biomass by richness and by country — side by side
col_a, col_b = st.columns(2)

fig_biomass_richness = px.box(
    filtered,
    x="richness_class", y="tree_biomass",
    color="richness_class",
    color_discrete_sequence=RICHNESS_COLORS,
    category_orders=RICHNESS_ORDER,
    points="all",
    labels={"richness_class": "Target species richness", "tree_biomass": "Tree biomass [Mg C ha⁻¹]"},
    title="Tree Biomass Across Richness Levels",
    height=400,
)
fig_biomass_richness.update_traces(boxmean=True)
fig_biomass_richness.update_layout(showlegend=False)
col_a.plotly_chart(fig_biomass_richness, use_container_width=True)

fig_biomass_country = px.box(
    filtered,
    x="country", y="tree_biomass",
    color="country",
    color_discrete_map=COUNTRY_COLORS,
    category_orders={"country": COUNTRY_ORDER},
    points="all",
    labels={"country": "Country", "tree_biomass": "Tree biomass [Mg C ha⁻¹]"},
    title="Tree Biomass Across Countries",
    height=400,
)
fig_biomass_country.update_traces(boxmean=True)
fig_biomass_country.update_layout(showlegend=False)
col_b.plotly_chart(fig_biomass_country, use_container_width=True)

# Biomass heatmap: country × richness
st.markdown("#### Mean tree biomass by country and richness class")
st.markdown(
    "Each cell shows the mean biomass (Mg C ha⁻¹) with plot count. "
    "Empty cells are richness–country combinations that were never sampled. "
    "Within Germany and Romania a richness effect is visible; elsewhere it is flat or inconsistent."
)

data_heatmap = (
    filtered.groupby(["country", "richness_class"], observed=True)["tree_biomass"]
    .mean()
    .reset_index()
)
heatmap_pivot = (
    data_heatmap.pivot(index="country", columns="richness_class", values="tree_biomass")
    .reindex(COUNTRY_ORDER)
)

cell_counts = (
    filtered.groupby(["country", "richness_class"], observed=True)["tree_biomass"]
    .count()
    .reset_index()
    .pivot(index="country", columns="richness_class", values="tree_biomass")
    .reindex(COUNTRY_ORDER)
)
cell_labels = (
    heatmap_pivot.round(1).astype(str)
    + "<br>n="
    + cell_counts.fillna(0).astype(int).astype(str)
)
cell_labels = cell_labels.where(heatmap_pivot.notna(), "")

fig_heatmap = px.imshow(
    heatmap_pivot,
    labels={"x": "Target species richness", "y": "Country", "color": "Mean tree biomass [Mg C ha⁻¹]"},
    title="Mean Tree Biomass Across Countries and Richness Classes",
    color_continuous_scale="Viridis_r",
    height=380,
)
fig_heatmap.update_traces(text=cell_labels.values, texttemplate="%{text}")
fig_heatmap.update_layout(margin={"t": 40, "b": 20})
st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# ── Section 4: What drives biomass? ──────────────────────────────────────────
st.header("4: What actually drives biomass?")
st.info(
    "Tree diameter correlates 0.77 with biomass, precipitation 0.40. "
    "Richness sits at just 0.15. "
    "Biomass is primarily a story of how big the trees are and how much water they get."
)

corr_vars = [
    "tree_biomass", "tree_growth", "target_species_richness",
    "average_tree_diameter", "total_soil_N", "total_soil_C",
    "temperature_annual_mean", "precipitation_annual",
]
corr = filtered[corr_vars].corr()

fig_corr = px.imshow(
    corr,
    text_auto=".2f",
    color_continuous_scale=px.colors.diverging.RdBu,
    color_continuous_midpoint=0,
    title="Correlations Among Biodiversity, Climate and Ecosystem Functions",
    height=500,
)
fig_corr.update_layout(margin={"t": 40, "b": 20})
st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

# ── Section 5: Drought resilience ────────────────────────────────────────────
st.header("5: Drought resilience — resistance vs. recovery")
st.info(
    "A clear trade-off: Spain resists drought least (0.64) but rebounds hardest (1.68). "
    "Finland does the reverse — high resistance, little need to recover. "
    "Despite opposite strategies, overall resilience is high across all regions."
)

data_drought = (
    filtered.groupby("country")[
        ["tree_growth_resistance", "tree_growth_recovery", "tree_growth_resilience"]
    ]
    .mean()
    .reset_index()
)
data_drought_long = data_drought.melt(
    id_vars="country",
    value_vars=["tree_growth_resistance", "tree_growth_recovery", "tree_growth_resilience"],
    var_name="drought_metric",
    value_name="mean_value",
)

fig_drought = px.bar(
    data_drought_long,
    x="country", y="mean_value",
    color="drought_metric",
    barmode="group",
    category_orders={"country": COUNTRY_ORDER},
    labels={
        "country": "Country",
        "mean_value": "Mean drought response (ratio)",
        "drought_metric": "Metric",
    },
    title="Drought Response Metrics Across Forest Regions",
    color_discrete_sequence=px.colors.sample_colorscale("Viridis", 3),
    height=460,
)
fig_drought.update_layout(legend_title_text="Drought metric")
st.plotly_chart(fig_drought, use_container_width=True)

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<p style='font-size:0.78rem; color:#9ca3af;'>"
    "Data: FunDivEUROPE Exploratory Platform (Baeten et al. 2013; 2019), published 2023. "
    "Analysis: Candelaria Zbikoski, 2026."
    "</p>",
    unsafe_allow_html=True,
)
