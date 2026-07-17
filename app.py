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

# ── Load & cache data ────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("FunDivEUROPE_alldata_exploratory-platform_2023 copy.xlsx")
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
    "**Does tree diversity improve ecosystem functioning in European forests?**  "
    "This dashboard explores BEF relationships across 209 mature forest plots "
    "in six European countries — from boreal Finland to Mediterranean Spain."
)
st.divider()

# ── Sidebar filter ───────────────────────────────────────────────────────────
st.sidebar.header("Filter plots 🔍")
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

# ── KPI row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Plots shown",       f"{len(filtered)}")
k2.metric("Countries",         f"{filtered['country'].nunique()}")
k3.metric("Avg biomass",       f"{filtered['tree_biomass'].mean():.0f} Mg C ha⁻¹")
k4.metric("Avg growth",        f"{filtered['tree_growth'].mean():.2f} Mg C ha⁻¹ yr⁻¹")
k5.metric("Avg Shannon index", f"{filtered['shannon_diversity'].mean():.2f}")

st.divider()

# ── Section 1: Where are these forests? ─────────────────────────────────────
st.header("1: Where are these forests?")
st.info(
    "📍 Six countries, six biomes — from boreal conifer forests in Finland down to "
    "drought-adapted Mediterranean woodlands in Spain. The plots were deliberately "
    "chosen to span Europe's full climate gradient."
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
    height=600,
)
fig_map.update_geos(
    fitbounds="locations",
    showcountries=True,
    showcoastlines=True,
    lataxis_range=[35, 72],
    lonaxis_range=[-10, 40],
)
fig_map.update_layout(legend_title_text="Country", margin={"t": 40, "b": 0})
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ── Section 2: Richness distribution ────────────────────────────────────────
st.header("2: How much richness variation is there?")
st.info(
    "🌿 Target richness ranges from 1 to 5 species per plot, by design. "
    "Higher richness levels are rarer and concentrated in central Europe — "
    "and the Shannon index confirms that more target species means genuinely more diverse stands."
)

col_left, col_right = st.columns(2)

data_richness = (
    filtered.groupby(["country", "richness_class"], observed=True)
    .size()
    .reset_index(name="count")
)
fig_richness_bar = px.bar(
    data_richness,
    x="country",
    y="count",
    color="richness_class",
    color_discrete_sequence=RICHNESS_COLORS,
    barmode="stack",
    category_orders={"country": COUNTRY_ORDER, **RICHNESS_ORDER},
    labels={"richness_class": "Target richness", "count": "Number of plots", "country": "Country"},
    title="Richness Distribution Across Countries",
    height=420,
)
col_left.plotly_chart(fig_richness_bar, use_container_width=True)

fig_shannon = px.box(
    filtered,
    x="richness_class",
    y="shannon_diversity",
    color="richness_class",
    color_discrete_sequence=RICHNESS_COLORS,
    category_orders=RICHNESS_ORDER,
    labels={"richness_class": "Target species richness", "shannon_diversity": "Shannon diversity index"},
    title="Shannon Diversity Across Target Richness Classes",
    height=420,
)
fig_shannon.update_layout(showlegend=False)
col_right.plotly_chart(fig_shannon, use_container_width=True)

st.divider()

# ── Section 3: BEF question ──────────────────────────────────────────────────
st.header("3: Does richness drive biomass? The BEF question")
st.info(
    "⚖️ Richness moves biomass only modestly (1.3× from richness 1 to 5). "
    "Country, by contrast, drives a 3.7× range — Romania and Germany store far more carbon "
    "than Finland or Spain. **The dominant story is region, not richness.**"
)

col_a, col_b = st.columns(2)

fig_biomass_richness = px.box(
    filtered,
    x="richness_class",
    y="tree_biomass",
    color="richness_class",
    color_discrete_sequence=RICHNESS_COLORS,
    category_orders=RICHNESS_ORDER,
    points="all",
    labels={"richness_class": "Target species richness", "tree_biomass": "Tree biomass [Mg C ha⁻¹]"},
    title="Tree Biomass Across Richness Levels",
    height=440,
)
fig_biomass_richness.update_traces(boxmean=True)
fig_biomass_richness.update_layout(showlegend=False)
col_a.plotly_chart(fig_biomass_richness, use_container_width=True)

fig_biomass_country = px.box(
    filtered,
    x="country",
    y="tree_biomass",
    color="country",
    color_discrete_map=COUNTRY_COLORS,
    category_orders={"country": COUNTRY_ORDER},
    points="all",
    labels={"country": "Country", "tree_biomass": "Tree biomass [Mg C ha⁻¹]"},
    title="Tree Biomass Across Countries",
    height=440,
)
fig_biomass_country.update_traces(boxmean=True)
fig_biomass_country.update_layout(showlegend=False)
col_b.plotly_chart(fig_biomass_country, use_container_width=True)

st.divider()

# ── Section 4: What drives biomass? ─────────────────────────────────────────
st.header("4: What actually drives biomass?")
st.info(
    "📐 Tree diameter alone correlates 0.77 with biomass — bigger trees store more carbon, "
    "unsurprisingly. Precipitation comes next at 0.40. "
    "Richness? Just 0.15. Biomass is a story about tree size and water, not diversity."
)

corr_vars = [
    "tree_biomass",
    "tree_growth",
    "target_species_richness",
    "average_tree_diameter",
    "total_soil_N",
    "total_soil_C",
    "temperature_annual_mean",
    "precipitation_annual",
]
corr = filtered[corr_vars].corr()

fig_corr = px.imshow(
    corr,
    text_auto=".2f",
    color_continuous_scale=px.colors.diverging.RdBu,
    color_continuous_midpoint=0,
    title="Correlations Among Biodiversity, Climate and Ecosystem Functions",
    height=520,
)
st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

# ── Section 5: Drought resilience ────────────────────────────────────────────
st.header("5: Drought resilience — resistance vs. recovery")
st.info(
    "💧 There is a clear resistance–recovery trade-off across regions. "
    "Spain barely holds its ground during drought (resistance = 0.64) but bounces back hardest (recovery = 1.68). "
    "Finland does the reverse. Despite opposite strategies, overall resilience is high everywhere."
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
    x="country",
    y="mean_value",
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
    height=480,
)
st.plotly_chart(fig_drought, use_container_width=True)

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "Data: FunDivEUROPE Exploratory Platform (Baeten et al. 2013; 2019), published 2023.  "
    "Analysis: Cand Zbikoski, 2026."
)
