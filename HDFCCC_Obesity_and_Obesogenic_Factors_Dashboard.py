# HDFCCC - Obesity Supplement - Obesogenic Factor Dashboard #
# Code by Nelson Wu #
# These codes read in the requisite shape files and CHIS obesity #
# source data; clean and categorize the obesogenic factor data; #
# merge the shapefiles with specific, year-over-year obesogenic #
# data; plot this out in specific visualizations; and output this #
# in a user-friendly, toggle-able set of visualizations. #

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import openpyxl
import sys

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from shapely.geometry import Polygon, MultiPolygon

#==============================================================================
# READ IN SOURCE DATA & CATCHMENT CLASSIFICATIONS
#==============================================================================
workstation = "remote"

if workstation == "local":
    county_2010 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/US_county_2010.shp")
    county_2020 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/US_county_2020.shp")
    censustract_2010 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/US_tract_2010.shp")
    censustract_2020 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/US_tract_2020.shp")
    obesogenicfactors_filepath = "C:/Users/nelso/Downloads/Source Data/"
    checkpoint_outputdatapath_counties = "C:/users/nelso/Desktop/University of California San Francisco/DREAM Lab/Git Staging Area/HDFCCC-Obesity-and-Obesogenic-Factors-Dashboard/Output Data/WuNelson_HDFCCC_obesogenicfactors_counties_20260525.xlsx"
    checkpoint_outputdatapath_censustracts = "C:/users/nelso/Desktop/University of California San Francisco/DREAM Lab/Git Staging Area/HDFCCC-Obesity-and-Obesogenic-Factors-Dashboard/Output Data/WuNelson_HDFCCC_obesogenicfactors_censustracts_20260525.xlsx"
elif workstation == "remote":
    county_2010 = gpd.read_file("Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/County_level/nhgis0035_shape/US_county_2010.shp")
    county_2020 = gpd.read_file("Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/County_level/nhgis0039_shape/US_county_2020.shp")
    censustract_2010 = gpd.read_file("Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/ALL_US_CT/US_tract_2010.shp")
    censustract_2020 = gpd.read_file("Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/ALL_US_CT/US_tract_2020.shp")
    obesogenicfactors_filepath = "M:/DREAM Lab/Obesity Supplement/Source Data/"
    checkpoint_outputdatapath_counties = "M:/DREAM Lab/Obesity Supplement/Output Data/WuNelson_HDFCCC_obesogenicfactors_counties_20260526.xlsx"
    checkpoint_outputdatapath_censustracts = "M:/DREAM Lab/Obesity Supplement/Output Data/WuNelson_HDFCCC_obesogenicfactors_censustracts_20260526.xlsx"

# Project coordinates to metric Web Mercator for accurate, uniform distance calculation
county_projected_2010 = county_2010.to_crs(epsg=3857)
county_projected_2020 = county_2020.to_crs(epsg=3857)
censustract_projected_2010 = censustract_2010.to_crs(epsg=3857)
censustract_projected_2020 = censustract_2020.to_crs(epsg=3857)

stanfordcatchmentarea_fips = ["06085", "06081", "06087", "06001", "06013", 
                              "06053", "06069", "06077", "06099", "06047"]  
hdfccccatchmentarea_fips = ["06001", "06007", "06011", "06013", "06019", 
                            "06021", "06033", "06039", "06041", "06045", 
                            "06047", "06053", "06055", "06067", "06069", 
                            "06075", "06077", "06081", "06085", "06087", 
                            "06095", "06097", "06099", "06101", "06113"] 
sugarybeverage_fips = ["06001", "06075", "06087"]

# Generic data loader function
def load_and_clean_data(file_name, var_string, id_col, target_len):
    file_path = f"{obesogenicfactors_filepath}{file_name}"
    sourcedata = pd.read_excel(file_path, sheet_name=None)
    df = pd.concat(list(sourcedata.values()), ignore_index=True)
    
    if id_col in df.columns:
        df[id_col] = df[id_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(target_len)
        
    year_map = {"2015-2016": 2016, "2017-2018": 2018, "2019-2020": 2020, "2021-2022": 2022, "2023-2024": 2024, "2025-2026": 2026}
    df['year'] = df['yr'].apply(lambda x: year_map.get(x, np.nan))

    def categorize(val, thresholds, labels):
        if pd.isna(val) or val < 0: return "Data Missing"
        for t, l in zip(thresholds, labels):
            if val < t: return l
        return labels[-1]

    if var_string in ["adultobesity", "childoverweight", "teenoverweightobese"]:
        df[f"{var_string}_absolute"] = df["estimate"].apply(lambda x: categorize(x, [0.10, 0.20, 0.30, 0.40], ["0 to <10%", "10 to <20%", "20 to <30%", "30 to <40%", "40% or greater"]))
    elif var_string in ["adultfoodinsecurity", "adultsugarybev"]:
        df[f"{var_string}_absolute"] = df["estimate"].apply(lambda x: categorize(x, [0.05, 0.10, 0.15, 0.20], ["0 to <5%", "5 to <10%", "10 to <15%", "15 to <20%", "20% or greater"]))

    if target_len == 5:
        out_col = "county_fips"
        out_name = "county"
    elif target_len == 11:
        out_col = "censustract_fips"
        out_name = "censustract"

    return df.rename(columns={'estimate': var_string, 'geoid': out_col, 'geoName': out_name, "suppressed": f"{var_string}_suppressed", "yr": "year_string"}).drop(columns=["lb95", "ub95", "prevalence",
                                                                                                                                                                           "variable", "geoType", "population"])

# Read and process matrices
print("Loading workbook assets...", flush=True)
c_obesity = load_and_clean_data("adultobesity_counties.xlsx", "adultobesity", "geoid", 5)
c_child = load_and_clean_data("childoverweight_counties.xlsx", "childoverweight", "geoid", 5).drop(columns=["county", "year_string"])
c_teen = load_and_clean_data("teenoverweightobese_counties.xlsx", "teenoverweightobese", "geoid", 5).drop(columns=["county", "year_string"])
c_food = load_and_clean_data("adultfoodinsecurity_counties.xlsx", "adultfoodinsecurity", "geoid", 5).drop(columns=["county", "year_string"])
c_bev = load_and_clean_data("adultsugarbev_counties.xlsx", "adultsugarybev", "geoid", 5).drop(columns=["county", "year_string"])

obesogenicfactors_counties = c_obesity.merge(c_child, on=["county_fips", "year"], how="outer")\
                                      .merge(c_teen, on=["county_fips", "year"], how="outer")\
                                      .merge(c_food, on=["county_fips", "year"], how="outer")\
                                      .merge(c_bev, on=["county_fips", "year"], how="outer")

t_obesity = load_and_clean_data("adultobesity_censustracts.xlsx", "adultobesity", "geoid", 11)
t_child = load_and_clean_data("childoverweight_censustracts.xlsx", "childoverweight", "geoid", 11).drop(columns=["censustract", "year_string"])
t_teen = load_and_clean_data("teenoverweightobese_censustracts.xlsx", "teenoverweightobese", "geoid", 11).drop(columns=["censustract", "year_string"])
t_food = load_and_clean_data("adultfoodinsecurity_censustracts.xlsx", "adultfoodinsecurity", "geoid", 11).drop(columns=["censustract", "year_string"])
t_bev = load_and_clean_data("adultsugarbev_censustracts.xlsx", "adultsugarybev", "geoid", 11).drop(columns=["censustract", "year_string"])

obesogenicfactors_censustracts = t_obesity.merge(t_child, on=["censustract_fips", "year"], how="outer")\
                                          .merge(t_teen, on=["censustract_fips", "year"], how="outer")\
                                          .merge(t_food, on=["censustract_fips", "year"], how="outer")\
                                          .merge(t_bev, on=["censustract_fips", "year"], how="outer")

def compute_quintiles(df, id_col):
    out_df = df.copy()
    for col in ["adultobesity", "teenoverweightobese", "childoverweight", "adultfoodinsecurity", "adultsugarybev"]:
        if col in out_df.columns and not out_df[col].dropna().empty:
            out_df[f"{col}_quintile"] = pd.qcut(out_df[col], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates='drop')
        else:
            out_df[f"{col}_quintile"] = np.nan
    return out_df

# Group into clean dictionaries to eliminate conditional evaluations inside callback loops
data_store = {
    "county": {y: compute_quintiles(obesogenicfactors_counties[obesogenicfactors_counties['year'] == y], "county_fips") for y in [2016, 2018, 2020, 2022]},
    "censustract": {y: compute_quintiles(obesogenicfactors_censustracts[obesogenicfactors_censustracts['year'] == y], "censustract_fips") for y in [2016, 2018, 2020, 2022]}
}

#==============================================================================
# PRECOMPUTE SPATIAL LAYER GEOMETRIES (PRODUCTION VS DEBUG-OPTIMIZED)
#==============================================================================
print("Pre-building high vs debug spatial layers...", flush=True)

def generate_spatial_cache(gdf, filter_col, state_code, target_id_col, prod_tol, debug_tol):
    california_shapes = gdf[gdf[filter_col] == state_code].copy()
    
    # 1. High Fidelity Geometry Cache
    prod_shapes = california_shapes.copy()
    prod_shapes['geometry'] = prod_shapes.geometry.simplify(prod_tol, preserve_topology=True)
    if prod_shapes.crs != "EPSG:4326": prod_shapes = prod_shapes.to_crs(epsg=4326)
    prod_shapes[target_id_col] = prod_shapes[target_id_col].astype(str).str.strip()
    prod_json = json.loads(prod_shapes.to_json())

    # 2. Aggressive Debug Optimization Cache (Significantly drops coordinate arrays)
    debug_shapes = california_shapes.copy()
    debug_shapes['geometry'] = debug_shapes.geometry.simplify(debug_tol, preserve_topology=True)
    if debug_shapes.crs != "EPSG:4326": debug_shapes = debug_shapes.to_crs(epsg=4326)
    debug_shapes[target_id_col] = debug_shapes[target_id_col].astype(str).str.strip()
    debug_json = json.loads(debug_shapes.to_json())

    return {"prod": (prod_json, prod_shapes), "debug": (debug_json, debug_shapes)}

# Setup dual-layer spatial pipeline
spatial_pipeline = {
    "county": {
        2010: generate_spatial_cache(county_projected_2010, "STATEFP10", "06", "GEOID10", prod_tol=100, debug_tol=1200),
        2020: generate_spatial_cache(county_projected_2020, "STATEFP", "06", "GEOID", prod_tol=100, debug_tol=1200)
    },
    "censustract": {
        2010: generate_spatial_cache(censustract_projected_2010, "STATEFP10", "06", "GEOID10", prod_tol=150, debug_tol=2200),
        2020: generate_spatial_cache(censustract_projected_2020, "STATEFP", "06", "GEOID", prod_tol=150, debug_tol=2200)
    }
}

def get_catchment_boundary(gdf, fips_list, geo_join_col):
    """ Builds clean outer boundary traces while aggressively clearing out spatial gaps """
    catchment_gdf = gdf[gdf[geo_join_col].str.slice(0, 5).isin(fips_list)]
    if not catchment_gdf.empty:
        original_crs = catchment_gdf.crs
        # Move to metric projection to run clean consistent buffering buffers
        working_gdf = catchment_gdf.to_crs(epsg=3857)
        buffer_distance = 600  
        
        buffered_gdf = working_gdf.assign(geometry=working_gdf.geometry.buffer(buffer_distance))
        dissolved = buffered_gdf.dissolve()

        def remove_interior_holes(geometry):
            if geometry.geom_type == 'Polygon':
                return Polygon(geometry.exterior)
            elif geometry.geom_type == 'MultiPolygon':
                return MultiPolygon([Polygon(g.exterior) for g in geometry.geoms])
            return geometry

        dissolved['geometry'] = dissolved.geometry.apply(remove_interior_holes)
        dissolved['geometry'] = dissolved.geometry.buffer(-buffer_distance)
        return dissolved.to_crs(original_crs)
    return None

#==============================================================================
# COLOR CONFIGURATIONS
#==============================================================================
obesity_colormap = {"0 to <10%": "#FFFFE0", "10 to <20%": "#FAD390", "20 to <30%": "#E59866", "30 to <40%": "#BA4A00", "40% or greater": "#6E2C00", "Data Missing": "#D3D3D3"}
foodinsecurity_colormap = {"0 to <5%": "#66BB6A", "5 to <10%": "#A5D6A7", "10 to <15%": "#E8F5E9", "15 to <20%": "#FFF59D", "20% or greater": "#FDD835", "Data Missing": "#D3D3D3"}    
sugarybeverage_colormap = {"0 to <5%": "#F5EEF8", "5 to <10%": "#D7BDE2", "10 to <15%": "#AF7AC5", "15 to <20%": "#8E44AD", "20% or greater": "#4A235A", "Data Missing": "#D3D3D3"}

obesity_order = ["0 to <10%", "10 to <20%", "20 to <30%", "30 to <40%", "40% or greater"]
obesogenicfactor_order = ["0 to <5%", "5 to <10%", "10 to <15%", "15 to <20%", "20% or greater"]

def hex_to_rgba(hex_val, alpha=1.0):
    hex_clean = hex_val.lstrip('#')
    r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

#==============================================================================
# DASH LAYOUT
#==============================================================================
app = dash.Dash(__name__, title="Obesity & Obesogenic Factors Dashboard")

app.layout = html.Div(style={'fontFamily': 'Times New Roman, serif', 'padding': '30px', 'backgroundColor': '#fcfcfc', 'maxWidth': '1400px', 'margin': '0 auto'}, children=[
    html.Header(style={'borderBottom': '3px double #6E2C00', 'marginBottom': '25px', 'paddingBottom': '10px'}, children=[
        html.H1("Obesity & Obesogenic Factors Geospatial Demographics", style={'fontSize': '36px', 'color': '#052049', 'margin': '0', 'fontWeight': 'normal'}),
        html.P("DREAM Lab Demographic & Risk Assessment Spatial Interface", style={'fontStyle': 'italic', 'color': '#555'})
    ]),
    html.Div(style={'display': 'flex', 'gap': '30px', 'flexWrap': 'wrap'}, children=[
        html.Div(style={'flex': '1 1 350px', 'backgroundColor': '#f5f5f5', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}, children=[
            html.H3("Obesity Data Explorer", style={'borderBottom': '1px solid #ddd', 'paddingBottom': '5px', 'color': '#333', 'fontWeight': 'normal'}),
            
            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Obesity and Obesogenic Factors", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(id='factor-dropdown', options=[
                    {'label': 'Adult Obesity', 'value': 'adultobesity'},
                    {'label': 'Child Overweight', 'value': 'childoverweight'},
                    {'label': 'Teen Overweight/Obese', 'value': 'teenoverweightobese'},
                    {'label': 'Adult Food Insecurity', 'value': 'adultfoodinsecurity'},
                    {'label': 'Adult Sugary Beverage Consumption', 'value': 'adultsugarybev'}
                ], value='adultobesity', clearable=False)
            ]),

            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Time Frame:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(id='year-dropdown', options=[
                    {'label': '2015-2016', 'value': 2016},
                    {'label': '2017-2018', 'value': 2018},
                    {'label': '2019-2020', 'value': 2020},
                    {'label': '2021-2022', 'value': 2022}
                ], value=2016, clearable=False)
            ]),

            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Census Geography", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.RadioItems(id='geo-toggle', options=[
                    {'label': 'County', 'value': 'county'},
                    {'label': 'Census Tract', 'value': 'censustract'}
                ], value='county', labelStyle={'display': 'block', 'marginBottom': '8px'})
            ]),

            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Catchment Area / Sugary Beverage Tax Policy", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.RadioItems(id='catchment-toggle', options=[
                    {'label': 'California State', 'value': 'all'},
                    {'label': 'Stanford Cancer Institute Catchment Area', 'value': 'stanford_catchment'},
                    {'label': 'HDFCCC Catchment Area', 'value': 'HDFCCC_catchment'},
                    {'label': 'Sugary Beverage Policy Instated', 'value': 'sugarybeveragepolicy_cities'}
                ], value='all', labelStyle={'display': 'block', 'marginBottom': '8px'})
            ]),

            html.Div(style={'marginBottom': '10px', 'paddingTop': '10px', 'borderTop': '1px dashed #ccc'}, children=[
                html.Label("Performance Mode Toggle:", style={'fontSize': '13px', 'color': '#666', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Checklist(id='prod-toggle', options=[
                    {'label': 'Production High-Fidelity Rendering', 'value': 'prod'}
                ], value=[], style={'fontSize': '13px'})
            ])
        ]),
        html.Div(style={'flex': '3 1 600px'}, children=[
            dcc.Graph(id='spatial-choropleth-map', style={'height': '680px'}),
        ])
    ]),
    html.Footer(style={'marginTop': '30px', 'borderTop': '2px solid #ccc', 'paddingTop': '20px'}, children=[
        html.H4("Definitions", style={'color': '#444', 'fontWeight': 'normal'}),
        dcc.Markdown("""Per California Health Interview Survey documentation:
        * Adults are individuals 18 or older; adolescents/teens ages 12-17; and children ages 2-11.        
        * For adults, obesity is defined as a Body Mass Index of 30 or greater. 
        * For teens, overweight or obese is defined as a Body Mass Index in the 85th percentile or higher.
        * For children, overweight for age is defined as a weight at the 95th percentile or higher.
        * Food insecurity consists of low-income (200% Federal Poverty Level or below) who report being food insecure in the past xxxx _timeperiod_.
        * Sugar-sweetened beverage consumption consists of adults who consume 1+ sugar-sweetened beverages per day. 
        """),
        html.H4("Disclaimers", style={'color': '#444', 'fontWeight': 'normal'}),
        dcc.Markdown("""* California Health Interview Survey obscures estimates when populations are less than 1,000 individuals or when estimates are statistically unstable.
        * Adult sugary beverage consumption was not collected by CHIS for their 2017-2018 survey.
        * 2015-2016, 2017-2018, 2019-2020 data are plotted on 2010 Decennial Census geographies; 2021-2022 is plotted on 2020 Decennial Census geographies."""),
        html.H4("Additional Resources", style={'color': '#444', 'fontWeight': 'normal'}),
        dcc.Markdown("[Stanford Cancer Institute (SCI)](https://med.stanford.edu/cancer/about.html) | [National Cancer Institute (NCI)](https://www.cancer.gov) | Demographics data modeled by [CHIS](https://healthpolicy.ucla.edu/our-work/california-health-interview-survey-chis)")
    ])
])

#==============================================================================
# STREAMLINED CALLBACK ENGINE
#==============================================================================
@app.callback(
    Output('spatial-choropleth-map', 'figure'),
    [Input('factor-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('geo-toggle', 'value'),
     Input('catchment-toggle', 'value'),
     Input('prod-toggle', 'value')]
)
def update_interactive_map(selected_factor, selected_year, selected_geo, selected_catchment, prod_selection):
    # Determine mode: default (empty list) uses optimized debug shapes, checking uses high-fidelity
    render_mode = "prod" if "prod" in prod_selection else "debug"
    
    geo_year_key = 2020 if selected_year == 2022 else 2010
    geo_join_col = "GEOID" if geo_year_key == 2020 else "GEOID10"

    # Fetch geometry mapping cache instantaneously 
    geo_json_obj, base_shapes = spatial_pipeline[selected_geo][geo_year_key][render_mode]

    # Pull structural survey data array
    survey_df = data_store[selected_geo][selected_year]
    right_key = "county_fips" if selected_geo == "county" else "censustract_fips"

    # Lightweight join
    datasource = pd.merge(base_shapes[[geo_join_col]], survey_df, left_on=geo_join_col, right_on=right_key, how="left")

    col_base = f"{selected_factor}_absolute"
    if selected_factor == "adultobesity":
        base_colors, cat_order, metric_label = obesity_colormap, obesity_order, "Adult Obesity Distribution"
    elif selected_factor == "teenoverweightobese":
        base_colors, cat_order, metric_label = obesity_colormap, obesity_order, "Teen Overweight/Obese Distribution"
    elif selected_factor == "childoverweight":
        base_colors, cat_order, metric_label = obesity_colormap, obesity_order, "Child Overweight Distribution"
    elif selected_factor == "adultfoodinsecurity":
        base_colors, cat_order, metric_label = foodinsecurity_colormap, obesogenicfactor_order, "Adult Food Insecurity Distribution"
    elif selected_factor == "adultsugarybev":
        base_colors, cat_order, metric_label = sugarybeverage_colormap, obesogenicfactor_order, "Adult Sugary Beverage Consumption Distribution"

    year_display_strings = {2016: "2015-2016", 2018: "2017-2018", 2020: "2019-2020", 2022: "2021-2022"}
    geo_display_strings = {"county": "County", "censustract": "Census Tract"}
    
    selected_year_str = year_display_strings.get(selected_year, str(selected_year))
    selected_geo_str = geo_display_strings.get(selected_geo, "Geographic View")
    
    # Combine everything using a line break and a smaller, muted sub-font styling
    legend_combined_title = (
        f"<b>{metric_label}</b><br>"
        f"<span style='font-size: 11px; font-weight: normal; color: #555555; font-family: \"Times New Roman\", serif; font-style: normal;'>"
        f"{selected_geo_str}, {selected_year_str}</span>"
    )

    target_fips = {
        'stanford_catchment': stanfordcatchmentarea_fips,
        'HDFCCC_catchment': hdfccccatchmentarea_fips,
        'sugarybeveragepolicy_cities': sugarybeverage_fips
    }.get(selected_catchment, [])

    color_column_to_use = 'styled_color_group'
    
    # Fast vectorized calculation instead of slow iterative dataframe apply functions
    if selected_catchment == 'all':
        datasource[color_column_to_use] = datasource[col_base].fillna("Data Missing")
        final_categories = cat_order + ["Data Missing"]
        active_color_discrete_map = base_colors.copy()
    else:
        # Optimization: Map catchment membership vectorially
        fips_prefix = datasource[geo_join_col].str.slice(0, 5)
        in_catchment = fips_prefix.isin(target_fips)
        
        base_vals = datasource[col_base].fillna("Data Missing")
        datasource[color_column_to_use] = np.where(in_catchment, base_vals, base_vals + " - outside catchment area")
        
        active_color_discrete_map = base_colors.copy()
        final_categories = []
        for cat in cat_order:
            final_categories.extend([cat, f"{cat} - outside catchment area"])
            active_color_discrete_map[f"{cat} - outside catchment area"] = hex_to_rgba(base_colors[cat], alpha=0.15)
        
        final_categories.extend(["Data Missing", "Data Missing - outside catchment area"])
        active_color_discrete_map["Data Missing - outside catchment area"] = hex_to_rgba(base_colors["Data Missing"], alpha=0.15)

    datasource['display_pct'] = (datasource[selected_factor] * 100).round(1)

    # Inject legend tracking placeholders
    ghost_df = pd.DataFrame([{geo_join_col: f"ghost_{c}", color_column_to_use: c, "display_pct": np.nan} for c in final_categories])
    datasource = pd.concat([datasource, ghost_df], ignore_index=True)

    cat_type = pd.CategoricalDtype(categories=final_categories, ordered=True)
    datasource[color_column_to_use] = datasource[color_column_to_use].astype(cat_type)

    # Instant layout spatial framing estimation
    minx, miny, maxx, maxy = base_shapes.total_bounds
    
    fig = px.choropleth_mapbox(
        datasource, geojson=geo_json_obj, locations=datasource[geo_join_col],
        featureidkey="properties." + geo_join_col, color=color_column_to_use,
        color_discrete_map=active_color_discrete_map, category_orders={color_column_to_use: final_categories},
        mapbox_style="carto-positron", zoom=5.1, center={"lat": (miny + maxy) / 2, "lon": (minx + maxx) / 2},
        opacity=0.85, custom_data=["county" if selected_geo == "county" else "censustract", color_column_to_use, "display_pct"]
    )

    # Remove the extra legend entries for geographies outside of the catchment areas. 
    fig.for_each_trace(
        lambda trace: trace.update(showlegend=False) 
        if "outside catchment area" in trace.name else None
    )

    mapbox_layers_list = []
    if selected_catchment != 'all':
        boundary_gdf = get_catchment_boundary(base_shapes, target_fips, geo_join_col)
        if boundary_gdf is not None and not boundary_gdf.empty:
            mapbox_layers_list.append({
                "sourcetype": "geojson", "source": json.loads(boundary_gdf.geometry.to_json()),
                "type": "line", "color": "#111111", "line": {"width": 1.5}, "opacity": 0.9
            })

    fig.update_traces(
        marker_line_width=0.2 if selected_geo == "censustract" else 0.5,
        marker_line_color="#ffffff",
        hovertemplate="<b>%{customdata[0]}</b><br>Category: %{customdata[1]}<br>Value: %{customdata[2]:.1f}%<extra></extra>"
    )

    fig.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        font=dict(family="Times New Roman", size=14),
        legend=dict(title_text=legend_combined_title, y=0.04, x=0.02, bgcolor="rgba(255, 255, 255, 0.9)"),
        mapbox_layers=mapbox_layers_list
    )
    return fig

if __name__ == '__main__':
    if workstation == "local":
        app.run(debug=True)
    elif workstation == "remote":
        app.run(debug=True, host="0.0.0.0", port=8050)