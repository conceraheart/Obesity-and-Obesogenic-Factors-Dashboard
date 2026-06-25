# HDFCCC - Obesity Supplement - Obesogenic Factor Dashboard #
# Code by Nelson Wu #

# These codes pull in source data provided by California Health Interview Survey, 
# process them into a wide, year-by-year format for the included variables, 
# output this intermediate data to a checkpoint file, then use this data
# to render geospatial visualizations for obesity and obesogenic factors across California. 

# The dashboard includes additional features like a toggle for debug-optimized / production-quality 
# rendering, dropdown menus for variables / year / catchment areas. The catchment overlay 
# menu will place a boundary around catchment areas for Stanford Cancer Institute, HDFCCC, and
# cities who have instated a sugary beverage tax policy. Geographies outside the boundary are made
# more opaque. The dashboard also includes additional text descriptions for the data used, disclaimers, 
# and hyperlinks to additional resources. 

# To do:
# - "Apply changes" button to set options before rendering.
# - Loading bar / "processing" indicator for better user responsiveness.
# - Button-activated functionality for side-by-side visualizations.




# Activate virtual environment
# .\\.venv\scripts\activate.ps1


import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import openpyxl
import sys

import dash
from dash import dcc, html, State, Patch, no_update
from dash.dependencies import Input, Output
from shapely.geometry import Polygon, MultiPolygon

#==============================================================================
# READ IN SOURCE DATA & CATCHMENT CLASSIFICATIONS
#==============================================================================
workstation = "remote"

if workstation == "local":
    county_2010 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/CA_county_2010.shp")
    county_2020 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/CA_county_2020.shp")
    censustract_2010 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/CA_tract_2010.shp")
    censustract_2020 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/CA_tract_2020.shp")
    obesogenicfactors_filepath = "C:/Users/nelso/Downloads/Source Data/20260616/"
    checkpoint_outputdatapath_counties = "C:/users/nelso/Desktop/University of California San Francisco/DREAM Lab/Git Staging Area/HDFCCC-Obesity-and-Obesogenic-Factors-Dashboard/Output Data/WuNelson_HDFCCC_obesogenicfactors_counties_20260616.xlsx"
    checkpoint_outputdatapath_censustracts = "C:/users/nelso/Desktop/University of California San Francisco/DREAM Lab/Git Staging Area/HDFCCC-Obesity-and-Obesogenic-Factors-Dashboard/Output Data/WuNelson_HDFCCC_obesogenicfactors_censustracts_20260616.xlsx"
elif workstation == "remote":
    county_2010 = gpd.read_file("M:/DREAM Lab/Obesity Supplement/Source Data/CA_county_2010.shp")
    county_2020 = gpd.read_file("M:/DREAM Lab/Obesity Supplement/Source Data/CA_county_2020.shp")
    censustract_2010 = gpd.read_file("M:/DREAM Lab/Obesity Supplement/Source Data/CA_tract_2010.shp")
    censustract_2020 = gpd.read_file("M:/DREAM Lab/Obesity Supplement/Source Data/CA_tract_2020.shp")
    obesogenicfactors_filepath = "M:/DREAM Lab/Obesity Supplement/Output Data/"


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

#==============================================================================
# GLOBAL DASHBOARD CONFIGURATION
#==============================================================================
obesity_colormap = {"0 to <10%": "#FFFFE0", "10 to <20%": "#FAD390", "20 to <30%": "#E59866", "30 to <40%": "#BA4A00", "40% or greater": "#6E2C00", "Data Missing": "#D3D3D3"}
foodinsecurity_colormap = {"0 to <5%": "#66BB6A", "5 to <10%": "#A5D6A7", "10 to <15%": "#E8F5E9", "15 to <20%": "#FFF59D", "20% or greater": "#FDD835", "Data Missing": "#D3D3D3"}    
sugarybeverage_colormap = {"0 to <5%": "#F5EEF8", "5 to <10%": "#D7BDE2", "10 to <15%": "#AF7AC5", "15 to <20%": "#8E44AD", "20% or greater": "#4A235A", "Data Missing": "#D3D3D3"}

obesity_order = ["0 to <10%", "10 to <20%", "20 to <30%", "30 to <40%", "40% or greater"]
obesogenicfactor_order = ["0 to <5%", "5 to <10%", "10 to <15%", "15 to <20%", "20% or greater"]

# Consolidate factor configurations to remove if/elif logic from the renderer
# Standardized Option Banks
chis_years = [
    {'label': '2015-2016', 'value': 2016}, {'label': '2017-2018', 'value': 2018},
    {'label': '2019-2020', 'value': 2020}, {'label': '2021-2022', 'value': 2022}
]
index_years = [
    {'label': '2020', 'value': 2020 }
]
standard_geos = [
    {'label': 'County', 'value': 'county'}, {'label': 'Census Tract', 'value': 'censustract'}
]

# Consolidate factor configurations, including allowed contexts
FACTOR_CONFIG = {
    "adultobesity": {
        "colors": obesity_colormap, "order": obesity_order, "label": "Adult Obesity",
        "allowed_years": chis_years, "allowed_geos": standard_geos
    },
    "teenoverweightobese": {
        "colors": obesity_colormap, "order": obesity_order, "label": "Teen Overweight/Obese",
        "allowed_years": chis_years, "allowed_geos": standard_geos
    },
    "childoverweight": {
        "colors": obesity_colormap, "order": obesity_order, "label": "Child Overweight",
        "allowed_years": chis_years, "allowed_geos": standard_geos
    },
    "adultfoodinsecurity": {
        "colors": foodinsecurity_colormap, "order": obesogenicfactor_order, "label": "Adult Food Insecurity",
        "allowed_years": chis_years, "allowed_geos": standard_geos
    },
    "adultsugarybev": {
        "colors": sugarybeverage_colormap, "order": obesogenicfactor_order, "label": "Adult Sugary Beverage",
        "allowed_years": standard_years, "allowed_geos": standard_geos
    },
    

    # This factor only has 2010/2020 data, and is strictly locked to Census Tracts.
    "new_decade_factor": {
        "colors": obesity_colormap, "order": obesity_order, "label": "Historical Decadal Data",
        "allowed_years": [
            {'label': '2010 Decennial', 'value': 2010}, 
            {'label': '2020 Decennial', 'value': 2020}
        ],
        "allowed_geos": [
            {'label': 'County', 'value': 'county', 'disabled': True}, # This grays out the option!
            {'label': 'Census Tract', 'value': 'censustract'}
        ]
    }
}

def hex_to_rgba(hex_val, alpha=1.0):
    hex_clean = hex_val.lstrip('#')
    r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

#==============================================================================
# READ IN MASTER WIDE-DATA 
#==============================================================================
def load_master_data(filename, geotype, fips_len):
    """Loads a master wide-format dataset and standardizes the FIPS column."""
    path = os.path.join(obesogenicfactors_filepath, filename)
    df = pd.read_excel(path)
    
    fips_col = 'countyfips' if geotype == 'county' else 'censustractfips'
    
    # Ensure FIPS is parsed as a string, stripped of decimals, and zero-padded
    df[fips_col] = df[fips_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(fips_len)
    return df

print("Loading master datasets...", flush=True)

# Store the raw master datasets mapped to their respective geographic vintage
master_data_store = {
    "county": {
        2010: load_master_data("WuNelson_HDFCCC_obesitysupplementdata_county2010_20260624.xlsx", "county", 5),
        2020: load_master_data("WuNelson_HDFCCC_obesitysupplementdata_county2020_20260624.xlsx", "county", 5)
    },
    "censustract": {
        2010: load_master_data("WuNelson_HDFCCC_obesitysupplementdata_censustract2010_20260624.xlsx", "censustract", 11),
        2020: load_master_data("WuNelson_HDFCCC_obesitysupplementdata_censustract2020_20260624.xlsx", "censustract", 11)
    }
}

#==============================================================================
# PRECOMPUTE SPATIAL LAYER GEOMETRIES (PRODUCTION VS DEBUG-OPTIMIZED)
#==============================================================================
print("Pre-building high vs debug spatial layers...", flush=True)

def generate_spatial_cache(gdf, filter_col, state_code, target_id_col, prod_tol, debug_tol):
    california_shapes = gdf[gdf[filter_col] == state_code].copy()
    
    # High Fidelity Geometry Cache
    prod_shapes = california_shapes.copy()
    prod_shapes['geometry'] = prod_shapes.geometry.simplify(prod_tol, preserve_topology=True)
    if prod_shapes.crs != "EPSG:4326": prod_shapes = prod_shapes.to_crs(epsg=4326)
    prod_shapes[target_id_col] = prod_shapes[target_id_col].astype(str).str.strip()
    prod_json = json.loads(prod_shapes.to_json())

    # Aggressive Debug Optimization Cache (Significantly drops coordinate arrays)
    debug_shapes = california_shapes.copy()
    debug_shapes['geometry'] = debug_shapes.geometry.simplify(debug_tol, preserve_topology=True)
    if debug_shapes.crs != "EPSG:4326": debug_shapes = debug_shapes.to_crs(epsg=4326)
    debug_shapes[target_id_col] = debug_shapes[target_id_col].astype(str).str.strip()
    debug_json = json.loads(debug_shapes.to_json())

    return {"prod": (prod_json, prod_shapes), "debug": (debug_json, debug_shapes)}

# Setup dual-layer spatial pipeline
spatial_pipeline = {
    "county": {
        2010: generate_spatial_cache(county_projected_2010, "STATEFP10", "06", "GEOID10", prod_tol=20, debug_tol=1200),
        2020: generate_spatial_cache(county_projected_2020, "STATEFP", "06", "GEOID", prod_tol=20, debug_tol=1200)
    },
    "censustract": {
        2010: generate_spatial_cache(censustract_projected_2010, "STATEFP10", "06", "GEOID10", prod_tol=5, debug_tol=2200),
        2020: generate_spatial_cache(censustract_projected_2020, "STATEFP", "06", "GEOID", prod_tol=5, debug_tol=2200)
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
# UI CONTROL BUILDERS
#==============================================================================
# Options reused across both maps
factor_opts = [
    {'label': 'Adult Obesity', 'value': 'adultobesity'},
    {'label': 'Child Overweight', 'value': 'childoverweight'},
    {'label': 'Teen Overweight/Obese', 'value': 'teenoverweightobese'},
    {'label': 'Adult Food Insecurity', 'value': 'adultfoodinsecurity'},
    {'label': 'Adult Sugary Beverage Consumption', 'value': 'adultsugarybev'}
]
year_opts = [
    {'label': '2015-2016', 'value': 2016}, {'label': '2017-2018', 'value': 2018},
    {'label': '2019-2020', 'value': 2020}, {'label': '2021-2022', 'value': 2022}
]
geo_opts = [
    {'label': 'County', 'value': 'county'}, {'label': 'Census Tract', 'value': 'censustract'}
]
catchment_opts = [
    {'label': 'California State', 'value': 'all'},
    {'label': 'Stanford Cancer Institute Catchment Area', 'value': 'stanford_catchment'},
    {'label': 'UCSF/HDFCCC Catchment Area', 'value': 'HDFCCC_catchment'},
    {'label': 'Sugary Beverage Tax Policy Instated', 'value': 'sugarybeveragepolicy_cities'}
]

def create_control_panel(map_id_prefix, title, is_secondary=False):
    return html.Div(id=f'panel-{map_id_prefix}', style={'marginBottom': '20px', 'display': 'none' if is_secondary else 'block'}, children=[
        html.H4(title, style={'borderBottom': '1px solid #ddd', 'paddingBottom': '5px', 'color': '#333', 'marginTop': '15px'}),
        
        html.Label("Factor:", style={'fontWeight': 'bold', 'display': 'block', 'fontSize': '14px'}),
        dcc.Dropdown(id=f'factor-dropdown-{map_id_prefix}', options=factor_opts, value='adultobesity', clearable=False, style={'marginBottom': '15px'}),
        
        html.Label("Time Frame:", style={'fontWeight': 'bold', 'display': 'block', 'fontSize': '14px'}),
        dcc.Dropdown(id=f'year-dropdown-{map_id_prefix}', options=year_opts, value=2016, clearable=False, style={'marginBottom': '15px'}),
        
        html.Label("Geography:", style={'fontWeight': 'bold', 'display': 'block', 'fontSize': '14px'}),
        dcc.RadioItems(id=f'geo-toggle-{map_id_prefix}', options=geo_opts, value='county', labelStyle={'display': 'block', 'marginBottom': '4px'}),
        html.Br(),
        
        html.Label("Catchment Overlay:", style={'fontWeight': 'bold', 'display': 'block', 'fontSize': '14px'}),
        dcc.RadioItems(id=f'catchment-toggle-{map_id_prefix}', options=catchment_opts, value='all', labelStyle={'display': 'block', 'marginBottom': '4px'}),
    ])

def create_sync_button( is_secondary=False ):
    return html.Div( style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center' }, children=[
        html.Button('Synchronize Maps', id='sync-btn', n_clicks=0, style={
        'display': 'none' if is_secondary else 'block',
        'width': '60%', "height": '60%', 'padding': '12px', 'backgroundColor': '#052049', 
        'color': 'white', 'border': 'none', 'borderRadius': '3px', 'fontSize': '14px', 
        'cursor': 'pointer', 'fontWeight': 'bold', 'marginTop': '5px' }) ] )

#==============================================================================
# DASH LAYOUT
#==============================================================================
app = dash.Dash(__name__, title="Obesity & Obesogenic Factors Dashboard")

app.layout = html.Div(style={'fontFamily': 'Times New Roman, serif', 'padding': '30px', 'backgroundColor': '#fcfcfc', 'maxWidth': '1800px', 'margin': '0 auto'}, children=[
    html.Header(style={'borderBottom': '3px double #6E2C00', 'marginBottom': '25px', 'paddingBottom': '10px'}, children=[
        html.H1("Obesity & Obesogenic Factors Geospatial Demographics", style={'fontSize': '36px', 'color': '#052049', 'margin': '0', 'fontWeight': 'normal'}),
        html.P("DREAM Lab Demographic & Risk Assessment Spatial Interface", style={'fontStyle': 'italic', 'color': '#555'})
    ]),
    
    # REMOVED flexWrap: 'wrap' to lock the sidebar and maps to a single row
    html.Div(style={'display': 'flex', 'gap': '20px', 'flexDirection': 'row'}, children=[
        
        # --- LEFT SIDEBAR: CONTROLS ---
        # Added minWidth to ensure the sidebar doesn't get crushed by the maps
        html.Div(style={'flex': '0 0 350px', 'minWidth': '350px', 'backgroundColor': '#f5f5f5', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)', 'height': 'fit-content'}, children=[
            
            # Map 1 Controls
            create_control_panel('1', 'Map 1 Options', is_secondary=False),
            
            # Dual Map Toggle
            html.Div(style={'margin': '20px 0', 'padding': '15px 0', 'borderTop': '1px dashed #ccc', 'borderBottom': '1px dashed #ccc'}, children=[
                dcc.Checklist(
                    id='dual-map-toggle',
                    options=[{'label': ' Enable Side-by-Side Comparison', 'value': 'dual'}],
                    value=[],
                    style={'fontWeight': 'bold', 'color': '#052049'}
                )
            ]),
            # Apply Changes Button
            html.Button('Apply Changes', id='apply-btn', n_clicks=0, style={
                'width': '100%', 'padding': '12px', 'backgroundColor': '#052049', 'color': 'white', 
                'border': 'none', 'borderRadius': '5px', 'fontSize': '16px', 'cursor': 'pointer',
                'fontWeight': 'bold', 'marginTop': '10px', 'marginBottom': '5px'
            }),
            # Synchronize Maps Button
            # Only shown if side-by-side maps are enabled. When clicked, it will synchronize both maps to changes made to the primary
            # map boundaries.
            create_sync_button(is_secondary=True),            
            # Map 2 Controls (Hidden by default)
            create_control_panel('2', 'Map 2 Options', is_secondary=True),
            
            # Global rendering toggle
            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Performance Mode:", style={'fontSize': '13px', 'color': '#666', 'display': 'block', 'marginTop': '5px', 'marginBottom': '5px'}),
                dcc.Checklist(id='prod-toggle', options=[
                    {'label': ' Production High-Fidelity Rendering', 'value': 'prod'}
                ], value=[], style={'fontSize': '13px'})
            ]),

  
            # Interactive Status Alert (Hidden on boot)
            html.Div(id='status-alert-container', style={'display': 'none'}, children=[
                html.Span("✓ Maps updated successfully.", style={'fontWeight': 'bold', 'fontSize': '14px'}),
                html.Button("✖", id='close-status-btn', n_clicks=0, style={
                    'border': 'none', 'background': 'none', 'fontSize': '14px', 
                    'cursor': 'pointer', 'color': '#155724', 'padding': '0', 'marginLeft': '10px'
                })
            ])
        ]),
        # --- RIGHT MAIN AREA: MAPS ---
        # minWidth: 0 prevents the flex container from blowing out past the screen bounds
        html.Div(style={'flex': '1', 'minWidth': 0}, children=[
            dcc.Loading(
                id="loading-maps",
                type="circle",
                color="#052049",
                children=[
                    html.Div(id='maps-container', style={'display': 'flex', 'gap': '15px', 'width': '100%'}, children=[
                        
                        # Map 1
                        # flex: 1 ensures it shares space equally, minWidth: 0 stops horizontal overflow
                        html.Div(id='map1-wrapper', style={'flex': '1', 'minWidth': 0}, children=[
                            dcc.Graph(id='spatial-choropleth-map-1', style={'height': '650px'}) 
                        ]),
                        
                        # Map 2 (Hidden by default)
                        html.Div(id='map2-wrapper', style={'display': 'none'}, children=[
                            dcc.Graph(id='spatial-choropleth-map-2', style={'height': '650px'})
                        ])
                    ])
                ]
            )
        ])
    ]),
    
    # --- FOOTER ---
    html.Footer(style={'marginTop': '30px', 'borderTop': '2px solid #ccc', 'paddingTop': '20px'}, children=[
        html.H4("Definitions", style={'color': '#444', 'fontWeight': 'normal'}),
        dcc.Markdown("""Adult (18 or older) obesity is defined as a body mass index (BMI) of 30.0 or greater. BMI is calculated using respondent's self-reported weight and height.  
Teen respondents (12-17) are classified as overweight/obese if they rank higher than the 85th percentile in the CDC 2010 recommendations on assigning BMI.  
Proportion of children overweight for their age is constructed using sex, age (in months), and weight. It does not take into account height.  
Adult food insecurity is defined as proportion of adults who are low-income and food insecure.  
Adult sugar-sweetened beverage consumption is defined as proportion of adults who consume soda or sweet beverages at least once a day.      
        """),
        html.H4("Disclaimers", style={'color': '#444', 'fontWeight': 'normal'}),
        dcc.Markdown("""* California Health Interview Survey obscures estimates when populations are less than 1,000 individuals or when estimates are statistically unstable.
* 2015-2016, 2017-2018, 2019-2020 data are plotted on 2010 Decennial Census geographies; 2021-2022 is plotted on 2020 Decennial Census geographies."""),
        html.H4("Additional Resources", style={'color': '#444', 'fontWeight': 'normal'}),
        dcc.Markdown("[UCSF-Helen Diller Family Comprehensive Cancer Center (HDFCCC)] (https://cancer.ucsf.edu/) | [Stanford Cancer Institute (SCI)](https://med.stanford.edu/cancer/about.html) | Demographics data modeled by [CHIS](https://healthpolicy.ucla.edu/our-work/california-health-interview-survey-chis)")
    ])
])

#==============================================================================
# CORE MAP GENERATION ENGINE
#==============================================================================
#==============================================================================
# CORE MAP GENERATION ENGINE
#==============================================================================
def generate_choropleth(selected_factor, selected_year, selected_geo, selected_catchment, prod_selection):
    """Abstracted core logic for rendering maps using wide-format master data."""
    render_mode = "prod" if "prod" in prod_selection else "debug"
    
    # 1. Determine Geography Vintage & Identifiers
    geo_year_key = 2020 if selected_year == 2022 else 2010
    geo_join_col = "GEOID" if geo_year_key == 2020 else "GEOID10"
    data_fips_col = 'countyfips' if selected_geo == 'county' else 'censustractfips'
    location_name_col = 'countyname' if selected_geo == 'county' else 'censustractname'

    # 2. Fetch Base Assets
    geo_json_obj, base_shapes = spatial_pipeline[selected_geo][geo_year_key][render_mode]
    master_df = master_data_store[selected_geo][geo_year_key]

    # 3. Join Spatial Shapes to Master Data
    datasource = pd.merge(base_shapes[[geo_join_col]], master_df, left_on=geo_join_col, right_on=data_fips_col, how="left")

    # 4. Target Dynamic Columns based on UI selections
    val_col = f"{selected_factor}_{selected_year}"
    cat_col = f"{selected_factor}_category_{selected_year}"

    # NOTE: If your master Excel data stores percentages as decimals (0.32), keep the * 100.
    # If your master Excel data is already formatted as whole numbers (32.4), remove the * 100.
    datasource['display_pct'] = (datasource[val_col] * 100).round(1) 

    # 5. Fetch Factor Configuration
    config = FACTOR_CONFIG[selected_factor]
    base_colors = config["colors"]
    cat_order = config["order"]
    metric_label = config["label"]
    
    color_column_to_use = 'styled_color_group'
    
    # 6. Apply Catchment Area Transparency Logic
    target_fips = {
        'stanford_catchment': stanfordcatchmentarea_fips,
        'HDFCCC_catchment': hdfccccatchmentarea_fips,
        'sugarybeveragepolicy_cities': sugarybeverage_fips
    }.get(selected_catchment, [])
    
    if selected_catchment == 'all':
        datasource[color_column_to_use] = datasource[cat_col].fillna("Data Missing")
        final_categories = cat_order + ["Data Missing"]
        active_color_discrete_map = base_colors.copy()
    else:
        fips_prefix = datasource[geo_join_col].str.slice(0, 5)
        in_catchment = fips_prefix.isin(target_fips)
        
        base_vals = datasource[cat_col].fillna("Data Missing")
        datasource[color_column_to_use] = np.where(in_catchment, base_vals, base_vals + " - outside catchment area")
        
        active_color_discrete_map = base_colors.copy()
        final_categories = []
        for cat in cat_order:
            final_categories.extend([cat, f"{cat} - outside catchment area"])
            active_color_discrete_map[f"{cat} - outside catchment area"] = hex_to_rgba(base_colors[cat], alpha=0.15)
        
        final_categories.extend(["Data Missing", "Data Missing - outside catchment area"])
        active_color_discrete_map["Data Missing - outside catchment area"] = hex_to_rgba(base_colors["Data Missing"], alpha=0.15)

    # 7. Inject "Ghost" rows to force Plotly to render all legend items even if they don't exist in the current map view
    ghost_df = pd.DataFrame([{geo_join_col: f"ghost_{c}", color_column_to_use: c, "display_pct": np.nan} for c in final_categories])
    datasource = pd.concat([datasource, ghost_df], ignore_index=True)

    cat_type = pd.CategoricalDtype(categories=final_categories, ordered=True)
    datasource[color_column_to_use] = datasource[color_column_to_use].astype(cat_type)

    # 8. Render the Map
    minx, miny, maxx, maxy = base_shapes.total_bounds
    
    year_display_strings = {2016: "2015-2016", 2018: "2017-2018", 2020: "2019-2020", 2022: "2021-2022"}
    geo_display_strings = {"county": "County", "censustract": "Census Tract"}
    legend_combined_title = (
        f"<b>{metric_label}</b><br>"
        f"<span style='font-size: 11px; font-weight: normal; color: #555555;'>"
        f"{geo_display_strings.get(selected_geo, '')}, {year_display_strings.get(selected_year, '')}</span>"
    )

    fig = px.choropleth_mapbox(
        datasource, geojson=geo_json_obj, locations=datasource[geo_join_col],
        featureidkey="properties." + geo_join_col, color=color_column_to_use,
        color_discrete_map=active_color_discrete_map, category_orders={color_column_to_use: final_categories},
        mapbox_style="carto-positron", zoom=5.1, center={"lat": (miny + maxy) / 2, "lon": (minx + maxx) / 2},
        opacity=0.85, custom_data=[location_name_col, color_column_to_use, "display_pct"]
    )

    fig.for_each_trace(
        lambda trace: trace.update(showlegend=False) if "outside catchment area" in trace.name else None
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
        mapbox_layers=mapbox_layers_list,
        uirevision='constant'
    )
    return fig

#==============================================================================
# STREAMLINED CALLBACK ENGINE
#==============================================================================
# UI Toggle Callback (Shows/Hides Map 2)
@app.callback(
    [Output('panel-2', 'style'), Output('map2-wrapper', 'style'), Output('sync-btn', 'style')],
    [Input('dual-map-toggle', 'value')]
)
def toggle_dual_mode(toggle_val):
    if 'dual' in toggle_val:
        # Inject flex and minWidth constraints when making Map 2 visible
        return ( {'display': 'block', 'marginBottom': '20px'},
                 {'flex': '1', 'minWidth': 0, 'display': 'block'}, 
                 {'display': 'block', 'width': '60%', 'height': '60%', 'padding': '12px', 
                  'backgroundColor': '#052049', 'color': 'white', 'border': 'none', 
                  'borderRadius': '5px', 'fontSize': '14px', 'cursor': 'pointer', 
                  'fontWeight': 'bold', 'marginTop': '5px'} )
    return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

# Main Generation Callback (Triggers on boot and "Apply Changes" click)
@app.callback(
    [Output('spatial-choropleth-map-1', 'figure'),
     Output('spatial-choropleth-map-2', 'figure'),
     Output('status-alert-container', 'style')],
    [Input('apply-btn', 'n_clicks')],
    [State('factor-dropdown-1', 'value'), State('year-dropdown-1', 'value'), 
     State('geo-toggle-1', 'value'), State('catchment-toggle-1', 'value'),
     State('factor-dropdown-2', 'value'), State('year-dropdown-2', 'value'), 
     State('geo-toggle-2', 'value'), State('catchment-toggle-2', 'value'),
     State('prod-toggle', 'value'), State('dual-map-toggle', 'value')]
)
def update_maps(n_clicks, f1, y1, g1, c1, f2, y2, g2, c2, prod_mode, dual_mode):
    # Initialize Map 1
    fig1 = generate_choropleth(f1, y1, g1, c1, prod_mode)
    
    # Initialize Map 2 (if dual mode is active)
    if 'dual' in dual_mode:
        fig2 = generate_choropleth(f2, y2, g2, c2, prod_mode)
    else:
        fig2 = no_update
        
    # Manage Status Indicator Visibility
    if n_clicks == 0:
        alert_style = {'display': 'none'}
    else:
        alert_style = {
            'display': 'flex', 'marginTop': '15px', 'padding': '10px 15px', 
            'backgroundColor': '#d4edda', 'color': '#155724', 'borderRadius': '5px', 
            'justifyContent': 'space-between', 'alignItems': 'center', 
            'border': '1px solid #c3e6cb', 'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
        }
        
    return fig1, fig2, alert_style

# Synchronize bounds from Map 1 to Map 2
@app.callback(
    Output('spatial-choropleth-map-2', 'figure', allow_duplicate=True),
    [Input('spatial-choropleth-map-1', 'relayoutData'),
     Input('sync-btn', 'n_clicks')],
    [State('dual-map-toggle', 'value')],
    prevent_initial_call=True
)
def sync_maps(relayout_data, n_clicks, dual_mode):
    # Only synchronize if dual mode is active and pan/zoom events occurred
    if 'dual' not in dual_mode:
        return no_update
    # If user has not panned or zoomed Map 1, relayout_data is None.
    if not relayout_data:
        return no_update
#if 'mapbox.zoom' in relayout_data or 'mapbox.center' in relayout_data or n_clicks > 0:
    
    if n_clicks > 0:
        patched_fig = Patch()
        if 'mapbox.zoom' in relayout_data:
            patched_fig['layout']['mapbox']['zoom'] = relayout_data['mapbox.zoom']
        if 'mapbox.center' in relayout_data:
            patched_fig['layout']['mapbox']['center'] = relayout_data['mapbox.center']
        return patched_fig
        
    return no_update

# Dismiss Status Indicator
@app.callback(
    Output('status-alert-container', 'style', allow_duplicate=True),
    [Input('close-status-btn', 'n_clicks')],
    prevent_initial_call=True
)
def dismiss_status(n_clicks):
    # When the close button is clicked, hide the container again
    if n_clicks > 0:
        return {'display': 'none'}
    return no_update

if __name__ == '__main__':
    if workstation == "local":
        app.run(debug=False)
    elif workstation == "remote":
        app.run(debug=False, host="0.0.0.0", port=8050)