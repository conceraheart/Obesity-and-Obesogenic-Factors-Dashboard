# HDFCC - Obesity Supplement - Obesogenic Factor Dashboard #
# Code by Nelson Wu #
# These codes read in the requisite shape files and CHIS obesity #
# source data; clean and categorize the obesogenic factor data; #
# merge the shapefiles with specific, year-over-year obesogenic #
# data; plot this out in specific visualizations; and output this #
# in a user-friendly, toggle-able set of visualizations. #

# The 2021-2022 data is mapped to 2020 Census data; #
# the remaining data is mapped to 2010 Census data. #

# Initialize virtual environment. #
# This goes into the command line bash. #
# python3 -m venv .venv
# .venv/Scripts/activate

# Install packages #
# Also into the command line for the virtual environment. #
# pip install numpy pandas geopandas plotly openpxyl dash

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

#==============================================================================
# READ IN SOURCE DATA & CATCHMENT CLASSIFICATIONS
#==============================================================================
# Configure workstation. The DREAM Lab workstation has different file paths than the local
# machine, and also has access restrictions for running the Dash on the local server.
# Consequently the DREAM Lab workstation uses an html output instead of running on the local
# server. There is some functionality lost - there are no text links in the html.  
# The workstation variable toggles between the two environments. 
workstation = "remote"

# Read in shapefile data for counties and census tracts
# Note: Tigerline shapefiles will show water boundaries. NHGIS shapefiles do not.
if workstation == "local":
    county_2010 = gpd.read_file( "C:/Users/nelso/Downloads/Source Data/Census Area Units - county/US_county_2010.shp" )
    county_2020 = gpd.read_file( "C:/Users/nelso/Downloads/Source Data/Census Area Units - county/US_county_2020.shp" )
    county_projected_2010=county_2010.to_crs(epsg=3857)
    county_projected_2020=county_2020.to_crs(epsg=3857)
    censustract_2010 = gpd.read_file ( "C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/US_tract_2010.shp" )
    censustract_2020 = gpd.read_file ( "C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/US_tract_2020.shp" )
    censustract_projected_2010=censustract_2010.to_crs(epsg=3857)
    censustract_projected_2020=censustract_2020.to_crs(epsg=3857)
    obesogenicfactors_filepath = "C:/Users/nelso/Downloads/Source Data/"
    checkpoint_outputdatapath_counties = "C:/users/nelso/Desktop/University of California San Francisco/DREAM Lab/Git Staging Area/HDFCCC-Obesity-and-Obesogenic-Factors-Dashboard/Output Data/WuNelson_HDFCC_obesogenicfactors_counties_20260525.xlsx"
    checkpoint_outputdatapath_censustracts = "C:/users/nelso/Desktop/University of California San Francisco/DREAM Lab/Git Staging Area/HDFCCC-Obesity-and-Obesogenic-Factors-Dashboard/Output Data/WuNelson_HDFCC_obesogenicfactors_censustracts_20260525.xlsx"
elif workstation == "remote":
    county_2010 = gpd.read_file ( "Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/County_level/nhgis0035_shape/US_county_2010.shp" )
    county_2020 = gpd.read_file ( "Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/County_level/nhgis0039_shape/US_county_2020.shp" )
    county_projected_2010=county_2010.to_crs(epsg=3857)
    county_projected_2020=county_2020.to_crs(epsg=3857)
    censustract_2010 = gpd.read_file ( "Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/ALL_US_CT/US_tract_2010.shp" )
    censustract_2020=gpd.read_file("Y:/GIS workload/Libraries/GIS Library/Census_Area_Units/ALL_US_CT/US_tract_2020.shp")
    censustract_projected_2010 = censustract_2010.to_crs(epsg=3857)
    censustract_projected_2020=censustract_2020.to_crs(epsg=3857)
    obesogenicfactors_filepath = "M:/DREAM Lab/Obesity Supplement/Source Data/"
    checkpoint_outputdatapath_counties = "M:/DREAM Lab/Obesity Supplement/Output Data/WuNelson_HDFCC_obesogenicfactors_counties_20260526.xlsx"
    checkpoint_outputdatapath_censustracts = "M:/DREAM Lab/Obesity Supplement/Output Data/WuNelson_HDFCC_obesogenicfactors_censustracts_20260526.xlsx"

# Define HDFCC and Stanford Catchment Areas #
# Stanford Cancer Institute (SCI): 
    # Peninsula / South Bay 
        # Santa Clara - 06085
        # San Mateo - 06081
        # Santa Cruz - 06087
    # East Bay
        # Alameda - 06001
        # Contra Costa - 06013
    # Salinas Valley
        # Monterey - 06053
        # San Benito - 06069
    # San Joaquin Valley
        # San Joaquin - 06077
        # Stanislaus - 06099
        # Merced - 06047
stanfordcatchmentarea_fips = [
    "06085", "06081", "06087", "06001", "06013", "06053", 
    "06069", "06077", "06099", "06047"
]  

# HDFCC Catchment Area
    # Alameda - 06001
    # Butte - 06007
    # Colusa - 06011
    # Contra Costa - 06013
    # Fresno - 06019
    # Glenn - 06021
    # Lake - 06033
    # Madera - 06039
    # Marin - 06041
    # Mendocino - 06045
    # Merced - 06047
    # Monterey - 06053
    # Napa - 06055
    # Sacramento - 06067
    # San Benito - 06069
    # San Francisco - 06075
    # San Joaquin - 06077
    # San Mateo - 06081
    # Santa Clara - 06085
    # Santa Cruz - 06087
    # Solano - 06095
    # Sonoma - 06097
    # Stanislaus - 06099
    # Sutter - 06101
    # Yolo - 06113
hdfcccatchmentarea_fips = [
    "06001", "06007", "06011", "06013", "06019", "06021", 
    "06033", "06039", "06041", "06045", "06047", "06053", 
    "06055", "06067", "06069", "06075", "06077", "06081", 
    "06085", "06087", "06095", "06097", "06099", "06101", 
    "06113"
] 

# Sugary Beverage Tax Policy Instated (cities)
    # Oakland / Berkeley - 06001 (Alameda County)
    # Berkeley began a 1-cent-per-ounce tax on distributors in 2014.
    # Oakland passed a similar 1-cent-per-ounce tax in 2017.

    # San Francisco - 06075
    # San Francisco's sugary drink tax was implemented in 2018.

    # Santa Cruz - 06087
    # Santa Cruz implemented a sugary drink tax at a rate of 2-cents-per-fluid-ounce
    # and went into effect May, 2025. This tax went into effect despite a legal
    # moratorium on sugary beverage taxes in California.
sugarybeverage_fips = [
    "06001", "06075", "06087"
]

# Read in and define breakpoints
# Counties
def counties_readxlsx(file_path, var_string, id_col_to_fix=None, target_len=5):
    """
    Read sheets from .xlsx and append into single dataframe.
    """
    # Read sheets into dictionary. #
    sourcedata = pd.read_excel(file_path, sheet_name=None)

    # Extract dataframes by position #
    sourcedata_list = list(sourcedata.values())

    # Combine list into master dataframe. #
    sourcedata_df = pd.concat(sourcedata_list, ignore_index=True)

    # Apply leading zero fix. #
    if id_col_to_fix and id_col_to_fix in sourcedata_df.columns:
        sourcedata_df[id_col_to_fix] = (
            sourcedata_df[id_col_to_fix]
            .astype(str)
            .str.strip()
            .str.replace(r'/\.0$', '', regex=True)
            .str.zfill(target_len)
        )

    def year_nameconversion(var):
        if var == "2015-2016": return 2016
        elif var == "2017-2018": return 2018
        elif var == "2019-2020": return 2020
        elif var == "2021-2022": return 2022
        elif var == "2023-2024": return 2024
        elif var == "2025-2026": return 2026
        else: return np.nan
        
    sourcedata_df['year'] = sourcedata_df['yr'].apply(year_nameconversion)

    def categories_absolute_obesity(var):
        if var >= 0 and var < 0.10: return "0 to <10%"
        elif var >= 0.10 and var < 0.20: return "10 to <20%"
        elif var >= 0.20 and var < 0.30: return "20 to <30%"
        elif var >= 0.30 and var < 0.40: return "30 to <40%"
        elif var >= 0.40: return "40% or greater"
        else: return "Data Missing"

    def categories_absolute_obesogenic(var):
        if var >= 0 and var < 0.05: return "0 to <5%"
        elif var >= 0.05 and var < 0.10: return "5 to <10%"
        elif var >= 0.10 and var < 0.15: return "10 to <15%"
        elif var >= 0.15 and var < 0.20: return "15 to <20%"
        elif var >= 0.20: return "20% or greater"
        else: return "Data Missing"

    if var_string in ["adultobesity", "childoverweight", "teenoverweightobese"]:
        sourcedata_df[f"{var_string}_absolute"] = sourcedata_df["estimate"].apply(categories_absolute_obesity)
    elif var_string in ["adultfoodinsecurity", "adultsugarybev"]:
        sourcedata_df[f"{var_string}_absolute"] = sourcedata_df["estimate"].apply(categories_absolute_obesogenic)
        
    sourcedata_df = sourcedata_df.rename(columns={
        'estimate': var_string, 
        'geoid': 'county_fips', 
        'geoName': 'county', 
        "suppressed": f"{var_string}_suppressed", 
        "yr": "year_string"
    })
    
    outputdata_df = sourcedata_df[["county_fips", "county", "year", "year_string", var_string, f"{var_string}_suppressed", f"{var_string}_absolute"]]
    return outputdata_df 

# Census Tracts
def censustracts_readxlsx(file_path, var_string, id_col_to_fix=None, target_len=11):
    """
    Read sheets from .xlsx and append into single dataframe.
    """
    # Read sheets into dictionary. #
    sourcedata = pd.read_excel(file_path, sheet_name=None)

    # Extract dataframes by position #
    sourcedata_list = list(sourcedata.values())

    # Combine list into master dataframe. #
    sourcedata_df = pd.concat(sourcedata_list, ignore_index=True)

    # Apply leading zero fix. #
    if id_col_to_fix and id_col_to_fix in sourcedata_df.columns:
        sourcedata_df[id_col_to_fix] = (
            sourcedata_df[id_col_to_fix]
            .astype(str)
            .str.strip()
            .str.replace(r'/\.0$', '', regex=True)
            .str.zfill(target_len)
        )

    def year_nameconversion(var):
        if var == "2015-2016": return 2016
        elif var == "2017-2018": return 2018
        elif var == "2019-2020": return 2020
        elif var == "2021-2022": return 2022
        elif var == "2023-2024": return 2024
        elif var == "2025-2026": return 2026
        else: return np.nan
        
    sourcedata_df['year'] = sourcedata_df['yr'].apply(year_nameconversion)

    def categories_absolute_obesity(var):
        if var >= 0 and var < 0.10: return "0 to <10%"
        elif var >= 0.10 and var < 0.20: return "10 to <20%"
        elif var >= 0.20 and var < 0.30: return "20 to <30%"
        elif var >= 0.30 and var < 0.40: return "30 to <40%"
        elif var >= 0.40: return "40% or greater"
        else: return "Data Missing"

    def categories_absolute_obesogenic(var):
        if var >= 0 and var < 0.05: return "0 to <5%"
        elif var >= 0.05 and var < 0.10: return "5 to <10%"
        elif var >= 0.10 and var < 0.15: return "10 to <15%"
        elif var >= 0.15 and var < 0.20: return "15 to <20%"
        elif var >= 0.20: return "20% or greater"
        else: return "Data Missing"

    if var_string in ["adultobesity", "childoverweight", "teenoverweightobese"]:
        sourcedata_df[f"{var_string}_absolute"] = sourcedata_df["estimate"].apply(categories_absolute_obesity)
    elif var_string in ["adultfoodinsecurity", "adultsugarybev"]:
        sourcedata_df[f"{var_string}_absolute"] = sourcedata_df["estimate"].apply(categories_absolute_obesogenic)
        
    sourcedata_df = sourcedata_df.rename(columns={
        'estimate': var_string, 
        'geoid': 'censustract_fips', 
        'geoName': 'censustract', 
        "suppressed": f"{var_string}_suppressed", 
        "yr": "year_string"
    })
    
    outputdata_df = sourcedata_df[["censustract_fips", "censustract", "year", "year_string", var_string, f"{var_string}_absolute", f"{var_string}_suppressed"]]
    return outputdata_df 

# Run data read functions
# Counties
adultobesity_counties = counties_readxlsx( f"{obesogenicfactors_filepath}adultobesity_counties.xlsx", 
                                          var_string="adultobesity", id_col_to_fix="geoid")
childoverweight_counties = counties_readxlsx( f"{obesogenicfactors_filepath}childoverweight_counties.xlsx", 
                                             var_string="childoverweight", id_col_to_fix="geoid").drop(columns=["county", "year_string"])
teenoverweightobese_counties = counties_readxlsx( f"{obesogenicfactors_filepath}teenoverweightobese_counties.xlsx", 
                                                 var_string="teenoverweightobese", id_col_to_fix="geoid").drop(columns=["county", "year_string"])
adultfoodinsecurity_counties = counties_readxlsx( f"{obesogenicfactors_filepath}adultfoodinsecurity_counties.xlsx",
                                                 var_string="adultfoodinsecurity", id_col_to_fix="geoid").drop(columns=["county", "year_string"])
adultsugarybeverage_counties = counties_readxlsx( f"{obesogenicfactors_filepath}adultsugarbev_counties.xlsx",
                                                 var_string="adultsugarybev", id_col_to_fix="geoid").drop(columns=["county", "year_string"])

obesogenicfactors_counties = adultobesity_counties.merge(childoverweight_counties, how="outer", on=["county_fips", "year"])\
    .merge(teenoverweightobese_counties, how="outer", on=["county_fips", "year"])\
    .merge(adultfoodinsecurity_counties, how="outer", on=["county_fips", "year"])\
    .merge(adultsugarybeverage_counties, how="outer", on=["county_fips", "year"])

# Census Tracts
# I have standardized the source .xlsx sheets to "geoid" and "yr"
# Some of the source sheets had no provided "yr" label, but the sheets were labeled by year. 
# Other sheets had different capitalization for "geoid" and "yr".
adultobesity_censustracts = censustracts_readxlsx( f"{obesogenicfactors_filepath}adultobesity_censustracts.xlsx",
                                              var_string="adultobesity", id_col_to_fix="geoid")
childoverweight_censustracts = censustracts_readxlsx( f"{obesogenicfactors_filepath}childoverweight_censustracts.xlsx", 
                                                 var_string="childoverweight", id_col_to_fix="geoid").drop(columns=["censustract", "year_string"])
teenoverweightobese_censustracts = censustracts_readxlsx( f"{obesogenicfactors_filepath}teenoverweightobese_censustracts.xlsx", 
                                                     var_string="teenoverweightobese", id_col_to_fix="geoid").drop(columns=["censustract", "year_string"])
adultfoodinsecurity_censustracts = censustracts_readxlsx( f"{obesogenicfactors_filepath}adultfoodinsecurity_censustracts.xlsx",
                                                     var_string="adultfoodinsecurity", id_col_to_fix="geoid").drop(columns=["censustract", "year_string"])
adultsugarybeverage_censustracts = censustracts_readxlsx( f"{obesogenicfactors_filepath}adultsugarbev_censustracts.xlsx",
                                                     var_string="adultsugarybev", id_col_to_fix="geoid").drop(columns=["censustract", "year_string"])

obesogenicfactors_censustracts = adultobesity_censustracts.merge(childoverweight_censustracts, how="outer", on=["censustract_fips", "year"])\
    .merge(teenoverweightobese_censustracts, how="outer", on=["censustract_fips", "year"])\
    .merge(adultfoodinsecurity_censustracts, how="outer", on=["censustract_fips", "year"])\
    .merge(adultsugarybeverage_censustracts, how="outer", on=["censustract_fips", "year"])

# Split obesogenic factor data into year over year data; calculate quintiles for these data by year. #
def yearoveryear_counties(year_var):
    obesogenicfactors_counties_year = obesogenicfactors_counties[obesogenicfactors_counties['year'] == year_var].copy()
    
    # Calculate quintiles safely
    for col in ["adultobesity", "teenoverweightobese", "childoverweight", "adultfoodinsecurity", "adultsugarybev"]:
        if col in obesogenicfactors_counties_year.columns and not obesogenicfactors_counties_year[col].dropna().empty:
            obesogenicfactors_counties_year[f"{col}_quintile"] = pd.qcut(obesogenicfactors_counties_year[col], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates='drop')
        else:
            obesogenicfactors_counties_year[f"{col}_quintile"] = np.nan
            
    return obesogenicfactors_counties_year

def yearoveryear_censustracts(year_var):
    obesogenicfactors_censustracts_year = obesogenicfactors_censustracts[obesogenicfactors_censustracts['year'] == year_var].copy()
    
    # Calculate quintiles safely
    for col in ["adultobesity", "teenoverweightobese", "childoverweight", "adultfoodinsecurity", "adultsugarybev"]:
        if col in obesogenicfactors_censustracts_year.columns and not obesogenicfactors_censustracts_year[col].dropna().empty:
            obesogenicfactors_censustracts_year[f"{col}_quintile"] = pd.qcut(obesogenicfactors_censustracts_year[col], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"], duplicates='drop')
        else:
            obesogenicfactors_censustracts_year[f"{col}_quintile"] = np.nan
            
    return obesogenicfactors_censustracts_year

# Run functions
# Counties
obesogenicfactors_counties_2016 = yearoveryear_counties(year_var=2016)
obesogenicfactors_counties_2018 = yearoveryear_counties(year_var=2018)
obesogenicfactors_counties_2020 = yearoveryear_counties(year_var=2020)
obesogenicfactors_counties_2022 = yearoveryear_counties(year_var=2022)

# Census tracts
obesogenicfactors_censustracts_2016 = yearoveryear_censustracts(year_var=2016)
obesogenicfactors_censustracts_2018 = yearoveryear_censustracts(year_var=2018)
obesogenicfactors_censustracts_2020 = yearoveryear_censustracts(year_var=2020)
obesogenicfactors_censustracts_2022 = yearoveryear_censustracts(year_var=2022)

# Save intermediate processing checkpoints locally
# Counties
with pd.ExcelWriter(checkpoint_outputdatapath_counties, engine="openpyxl") as writer:
    obesogenicfactors_counties_2016.to_excel(writer, sheet_name="2016", index=False)
    obesogenicfactors_counties_2018.to_excel(writer, sheet_name="2018", index=False)
    obesogenicfactors_counties_2020.to_excel(writer, sheet_name="2020", index=False)
    obesogenicfactors_counties_2022.to_excel(writer, sheet_name="2022", index=False)

# Census Tracts
with pd.ExcelWriter(checkpoint_outputdatapath_censustracts, engine="openpyxl") as writer:
    obesogenicfactors_censustracts_2016.to_excel(writer, sheet_name="2016", index=False)
    obesogenicfactors_censustracts_2018.to_excel(writer, sheet_name="2018", index=False)
    obesogenicfactors_censustracts_2020.to_excel(writer, sheet_name="2020", index=False)
    obesogenicfactors_censustracts_2022.to_excel(writer, sheet_name="2022", index=False)

#==============================================================================
# COLOR GRADIENTS AND SCALES CONFIGURATIONS
#==============================================================================
obesity_colormap = {
    "0 to <10%": "#FFFFE0",
    "10 to <20%": "#FAD390",
    "20 to <30%": "#E59866",
    "30 to <40%": "#BA4A00",
    "40% or greater": "#6E2C00",
    "Data Missing": "#D3D3D3"
}
foodinsecurity_colormap = {
    "0 to <5%": "#66BB6A",
    "5 to <10%": "#A5D6A7",
    "10 to <15%": "#E8F5E9",
    "15 to <20%": "#FFF59D",
    "20% or greater": "#FDD835",
    "Data Missing": "#D3D3D3"
}    
sugarybeverage_colormap = {
    "0 to <5%": "#F5EEF8",
    "5 to <10%": "#D7BDE2",
    "10 to <15%": "#AF7AC5",
    "15 to <20%": "#8E44AD",
    "20% or greater": "#4A235A",
    "Data Missing": "#D3D3D3"
}

obesity_order = ["0 to <10%", "10 to <20%", "20 to <30%", "30 to <40%", "40% or greater"]
obesogenicfactor_order = ["0 to <5%", "5 to <10%", "10 to <15%", "15 to <20%", "20% or greater"]

# Helper function to convert HEX to RGBA (for clean transparent overlays without schema errors)
def hex_to_rgba(hex_val, alpha=1.0):
    hex_clean = hex_val.lstrip('#')
    if len(hex_clean) == 3:
        hex_clean = "".join([char*2 for char in hex_clean])
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

#==============================================================================
# SPATIAL SIMPLIFICATION & CATCHMENT BOUNDARIES
#==============================================================================
def get_catchment_boundary(gdf, fips_list):
    """
    Filters spatial data by FIPS list and dissolves interior county borders to output a single outline.
    """
    catchment_gdf = gdf[gdf['county_fips'].isin(fips_list)]
    if not catchment_gdf.empty:
        dissolved = catchment_gdf.dissolve()
        return dissolved
    return None

print("Pre-processing spatial layers for instantaneous callback performance...", flush=True)

def precompute_geojson(gdf, filter_col, simplify_val):
    # Isolate California (FIPS "06")
    temp = gdf[gdf[filter_col] == "06"].copy()
    
    # Apply geometry simplification early while still in the projected CRS (EPSG:3857)
    temp['geometry'] = temp.geometry.simplify(simplify_val, preserve_topology=True)
    
    # Project to WGS84 (EPSG:4326) which Plotly requires for coordinate reading
    if temp.crs != "EPSG:4326":
        temp = temp.to_crs(epsg=4326)
        
    # Return a lightweight parsed Python dictionary map structure
    return json.loads(temp.geometry.to_json()), temp

# Set baseline simplification tolerance (Higher number = smaller payload = faster render)
sim_tol = 400 if workstation == "remote" else 100

# Execute once at startup: Stores the shape structures permanently in global memory
geojson_county_2010, county_shapes_2010 = precompute_geojson(county_projected_2010 if workstation == "remote" else county_2010, "STATEFP10", sim_tol)
geojson_county_2020, county_shapes_2020 = precompute_geojson(county_projected_2020 if workstation == "remote" else county_2020, "STATEFP", sim_tol)
geojson_censustract_2010, tract_shapes_2010 = precompute_geojson(censustract_projected_2010, "STATEFP10", sim_tol)
geojson_censustract_2020, tract_shapes_2020 = precompute_geojson(censustract_projected_2020, "STATEFP", sim_tol)



#==============================================================================
# DASH INTERACTIVE APPLICATION LAYOUT
#==============================================================================
app = dash.Dash(__name__, title="Obesity & Obesogenic Factors Dashboard")

app.layout = html.Div(style={
    'fontFamily': 'Times New Roman, serif', 
    'padding': '30px', 
    'backgroundColor': '#fcfcfc',
    'maxWidth': '1400px',
    'margin': '0 auto'
}, children=[
    
    html.Header(style={'borderBottom': '3px double #6E2C00', 'marginBottom': '25px', 'paddingBottom': '10px'}, children=[
        html.H1("Obesity & Obesogenic Factors Geospatial Demographics", style={'fontSize': '36px', 'color': '#052049', 'margin': '0', 'fontWeight': 'normal'}),
        html.P("DREAM Lab Demographic & Risk Assessment Spatial Interface", style={'fontStyle': 'italic', 'color': '#555'})
    ]),
    
    html.Div(style={'display': 'flex', 'gap': '30px', 'flexWrap': 'wrap'}, children=[
        
        # Left Control Sidebar
        html.Div(style={'flex': '1 1 350px', 'backgroundColor': '#f5f5f5', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}, children=[
            html.H3("Obesity Data Explorer", style={'borderBottom': '1px solid #ddd', 'paddingBottom': '5px', 'color': '#333', 'fontWeight': 'normal'}),
            
            # Select Factor (Dropdown)
            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Obesity and Obesogenic Factor Metric", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='factor-dropdown',
                    options=[
                        {'label': 'Adult Obesity', 'value': 'adultobesity'},
                        {'label': 'Child Overweight', 'value': 'childoverweight'},
                        {'label': 'Teen Overweight/Obese', 'value': 'teenoverweightobese'},
                        {'label': 'Adult Food Insecurity', 'value': 'adultfoodinsecurity'},
                        {'label': 'Adult Sugary Beverage Consumption', 'value': 'adultsugarybev'}
                    ],
                    value='adultobesity',
                    clearable=False
                )
            ]),

            # Select Year (Dropdown)
            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Time Frame:", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[
                        {'label': '2015-2016', 'value': 2016},
                        {'label': '2017-2018', 'value': 2018},
                        {'label': '2019-2020', 'value': 2020},
                        {'label': '2021-2022', 'value': 2022}
                    ],
                    value=2016,
                    clearable=False
                )
            ]),

            # Select Census Geography (Dynamic switch)
            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Census Geography", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.RadioItems(
                    id='geo-toggle',
                    options=[
                        {'label': 'County-Level', 'value': 'county'},
                        {'label': 'Census Tract-Level', 'value': 'censustract'}
                    ],
                    value='county',
                    labelStyle={'display': 'block', 'marginBottom': '8px'}
                )
            ]),

            # Select Catchment Area Toggle
            html.Div(style={'marginBottom': '20px'}, children=[
                html.Label("Catchment Area / Sugary Beverage Tax Policy", style={'fontWeight': 'bold', 'display': 'block', 'marginBottom': '5px'}),
                dcc.RadioItems(
                    id='catchment-toggle',
                    options=[
                        {'label': 'California State', 'value': 'all'},
                        {'label': 'Stanford Cancer Institute Catchment Area', 'value': 'stanford_catchment'},
                        {'label': 'HDFCC Catchment Area', 'value': 'HDFCC_catchment'},
                        {'label': 'Sugary Beverage Policy Instated', 'value': 'sugarybeveragepolicy_cities'}
                    ],
                    value='all',
                    labelStyle={'display': 'block', 'marginBottom': '8px'}
                )
            ]),

            # Debug/Performance Fidelity Toggle
            html.Div(style={'marginBottom': '10px', 'paddingTop': '10px', 'borderTop': '1px dashed #ccc'}, children=[
                html.Label("Debug Render Speed (Shape Simplification):", style={'fontSize': '13px', 'color': '#666', 'display': 'block', 'marginBottom': '5px'}),
                dcc.Checklist(
                    id='prod-toggle',
                    options=[{'label': 'Production High-Fidelity Rendering', 'value': 'prod'}],
                    value=[],
                    style={'fontSize': '13px'}
                )
            ])
        ]),
        
        # Interactive Map Output Window
        html.Div(style={'flex': '3 1 600px'}, children=[
            dcc.Graph(id='spatial-choropleth-map', style={'height': '680px'}),
        ])
    ]),
    
    # Bottom Footer Citations & Portals
    html.Footer(style={'marginTop': '30px', 'borderTop': '2px solid #ccc', 'paddingTop': '20px'}, children=[
        html.H4("Definitions", style={'color': '#444', 'fontWeight': 'normal'}),
        html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'fontSize': '14px'}, children=[
            dcc.Markdown("""
            - Adults are individuals 18 or older; adolescents/teens ages 12-17; and children ages 0-11.
            - Obesity is defined as a Body Mass Index of 30 or higher.
            - Overweight is defined as a Body Mass Index of 25 to <30.
            """, style={'flex': '1'})
        ]),
        html.H4("Additional Resources", style={'color': '#444', 'fontWeight': 'normal'}),
        html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'fontSize': '14px'}, children=[
            dcc.Markdown("""
            * **Cancer and Obesity Research Resources:**
              * [Stanford Cancer Institute (SCI)](https://med.stanford.edu/cancer/about.html)
              * [National Cancer Institute (NCI) - Obesity and Cancer Risk Policy Framework](https://www.cancer.gov/about-cancer/causes-prevention/risk/obesity/obesity-fact-sheet)
              * [CDC Division of Nutrition, Physical Activity, and Obesity (DNPAO)](https://www.cdc.gov/nccdphp/dnpao/index.html)
            """, style={'flex': '1'}),
            dcc.Markdown("""
            * **Underlying Demographics Sources:**
              * Demographics modeled by [California Health Interview Survey (CHIS).](https://healthpolicy.ucla.edu/our-work/california-health-interview-survey-chis)
            """, style={'flex': '1', 'marginLeft': '20px'})
        ])
    ])
])

#==============================================================================
# DYNAMIC INTERACTIVE MAP RENDERER
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
    is_production = 'prod' in prod_selection
    
    # ADJUST TOLERANCE FOR METERS (EPSG:3857)
    simplification_tolerance = 10 if is_production else 500

    if selected_year == 2022:
        base_shapes = county_shapes_2020.copy() if selected_geo == "county" else tract_shapes_2020.copy()
        geo_json_obj = geojson_county_2020 if selected_geo == "county" else geojson_censustract_2020
        geo_join_col = "GEOID"
        year_suffix = "2020"
    else:
        base_shapes = county_shapes_2010.copy() if selected_geo == "county" else tract_shapes_2010.copy()
        geo_json_obj = geojson_county_2010 if selected_geo == "county" else geojson_censustract_2010
        geo_join_col = "GEOID10"
        year_suffix = "2010"

    # Isolate targeting survey demographics datasets
    if selected_year == 2016:
        survey_df = obesogenicfactors_counties_2016 if selected_geo == "county" else obesogenicfactors_censustracts_2016
    elif selected_year == 2018:
        survey_df = obesogenicfactors_counties_2018 if selected_geo == "county" else obesogenicfactors_censustracts_2018
    elif selected_year == 2020:
        survey_df = obesogenicfactors_counties_2020 if selected_geo == "county" else obesogenicfactors_censustracts_2020
    else:
        survey_df = obesogenicfactors_counties_2022 if selected_geo == "county" else obesogenicfactors_censustracts_2022

    # High performance index merge
    right_key = "county_fips" if selected_geo == "county" else "censustract_fips"
    datasource = base_shapes.merge(survey_df, left_on=geo_join_col, right_on=right_key, how="left")


    # Project coordinates cleanly into WGS84 EPSG:4326 map coordinate system AFTER calculations are complete
    if datasource.crs != "EPSG:4326":
        datasource = datasource.to_crs(epsg=4326)

    col_base = f"{selected_factor}_absolute"

    # Select palettes matching clinical standards
    if selected_factor == "adultobesity":
        base_colors = obesity_colormap
        cat_order = obesity_order
        metric_label = "Adult Obesity"
    elif selected_factor == "teenoverweightobese":
        base_colors = obesity_colormap
        cat_order = obesity_order
        metric_label = "Teen Overweight or Obese"
    elif selected_factor == "childoverweight":
        base_colors = obesity_colormap
        cat_order = obesity_order
        metric_label = "Child Overweight"
    elif selected_factor == "adultfoodinsecurity":
        base_colors = foodinsecurity_colormap
        cat_order = obesogenicfactor_order
        metric_label = "Adults Experiencing Food Insecurity"
    else: # adultsugarybev
        base_colors = sugarybeverage_colormap
        cat_order = obesogenicfactor_order
        metric_label = "Sugary Beverage Consumption Distribution"

    # Copy of active categorical map palette
    active_color_discrete_map = base_colors.copy()
    
    # Calculate target active catchment FIPS array
    if selected_catchment == 'stanford_catchment':
        target_fips = stanfordcatchmentarea_fips
    elif selected_catchment == 'HDFCC_catchment':
        target_fips = hdfcccatchmentarea_fips
    elif selected_catchment == 'sugarybeveragepolicy_cities':
        target_fips = sugarybeverage_fips
    else:
        target_fips = []

    color_column_to_use = 'styled_color_group'
    
def assign_color_group(row):
        if selected_catchment == 'all':
            return row[col_base] if pd.notna(row[col_base]) else "Data Missing"
        else:
            # Dynamically look up 'county_fips' or 'censustract_fips' depending on right_key
            fips_val = str(row[right_key]) if pd.notna(row[right_key]) else ""
            # Slice the first 5 digits so a tract identifier matches a county target FIPS
            county_prefix = fips_val[:5] 
            
            if county_prefix in target_fips:
                return row[col_base] if pd.notna(row[col_base]) else "Data Missing"
            else:
                base_val = row[col_base] if pd.notna(row[col_base]) else "Data Missing"
                return f"{base_val} - outside catchment area"

        datasource[color_column_to_use] = datasource.apply(assign_color_group, axis=1)
        
        # Populate dynamic category maps with faded/transparent RGBA values
        # Legacy option to include different legend for catchment area / outside catchment area
        # labels.
        for key, hex_color in base_colors.items():
            faded_rgba = hex_to_rgba(hex_color, alpha=0.13)
            active_color_discrete_map[f"{key} - outside catchment area"] = faded_rgba
            
        final_categories = cat_order + ["Data Missing"]
    else:
        datasource[color_column_to_use] = datasource[col_base].fillna("Data Missing")
        final_categories = cat_order + ["Data Missing"]

    # Enforce strict pandas categorical datatype formatting to guarantee sorting
    cat_type = pd.CategoricalDtype(categories=final_categories, ordered=True)
    datasource[color_column_to_use] = datasource[color_column_to_use].astype(cat_type)

    # Multiply raw decimal matrices by 100 and round to 1 decimal place
    datasource['display_pct'] = datasource[selected_factor].apply(
        lambda x: round(x * 100, 1) if pd.notna(x) else np.nan
    )

    # Compile the GeoJSON boundary geometry using ONLY rows with valid geometry shapes
    valid_spatial_gdf = datasource[datasource['geometry'].notna()]
    geojson_data = json.loads(valid_spatial_gdf.geometry.to_json())

    # Append visual "ghost rows" to force empty categorical elements to display in the legend
ghost_records = [
        {
            right_key: f"ghost_{cat}", # Dynamically matches active FIPS column name
            "county" if selected_geo == "county" else "censustract": "Ghost",
            col_base: cat,
            "geometry": None
        }
        for cat in final_categories
    ]
    ghost_df = pd.DataFrame(ghost_records)
    ghost_gdf = gpd.GeoDataFrame(ghost_df, geometry='geometry', crs=datasource.crs)

    # Safely concat real and visual ghost datasets
    datasource = gpd.GeoDataFrame(pd.concat([datasource, ghost_gdf], ignore_index=True), crs=datasource.crs)
    datasource[color_column_to_use] = datasource[color_column_to_use].astype(cat_type)

    minx, miny, maxx, maxy = datasource.total_bounds
    map_center = {"lat": (miny + maxy) / 2, "lon": (minx + maxx) / 2}

    fig = px.choropleth_mapbox(
        datasource,
        geojson=geo_json_obj,
        locations=datasource[geo_join_col].combine_first(datasource['county_fips']),
        color=color_column_to_use,
        color_discrete_map=active_color_discrete_map,
        category_orders={color_column_to_use: final_categories},
        mapbox_style="carto-positron",
        zoom=5.3,
        center=map_center,
        opacity=0.85,
        custom_data=["county" if selected_geo == "county" else "censustract", color_column_to_use, "display_pct"]
    )

    # Create dissolved boundary outline layer for our map layout layers list
    mapbox_layers_list = []
    if selected_catchment != 'all':
        boundary_gdf = get_catchment_boundary(datasource, target_fips)
        if boundary_gdf is not None and not boundary_gdf.empty:
            if boundary_gdf.crs != "EPSG:4326":
                boundary_gdf = boundary_gdf.to_crs(epsg=4326)
            
            # Map dissolved multi-polygon geometry output
            geojson_boundary = json.loads(boundary_gdf.geometry.to_json())
            mapbox_layers_list.append({
                "sourcetype": "geojson",
                "source": geojson_boundary,
                "type": "line",
                "color": "#111111",  # High-contrast bold black border outline
                "line": {"width": 3.5},  # Nested correctly to bypass Plotly layout schemas
                "opacity": 0.95
            })

    fig.update_traces(
        marker_line_width=0.4,
        marker_line_color="#ffffff",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "Category: %{customdata[1]}<br>" +
            "Proportion of Population: %{customdata[2]:.1f}%<br>" +
            "<extra></extra>"
        ),
        hoverlabel=dict(
            font_family="Times New Roman",
            font_size=16
        )
    )

    # Enforce strict layout visual styling
    fig.update_layout(
        margin={"r": 0, "t": 10, "l": 0, "b": 0},
        font=dict(
            family="Times New Roman",
            size=14,
            color="#2c1a04"
        ),
        legend=dict(
            title_text=metric_label,
            title_font_family="Times New Roman",
            font_family="Times New Roman",
            traceorder="normal",
            yanchor="bottom",
            y=0.04,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#ddd",
            borderwidth=1
        ),
        mapbox_layers=mapbox_layers_list
    )
    
    return fig

if __name__ == '__main__':
    if workstation == "local":
        # Local server deployment bootup
            app.run(debug=True)
    elif workstation == "remote":
        try:
            app.run(debug=True, host="0.0.0.0", port=8050)
            print("--> app.run() block finished executing successfully.", flush=True)
        except Exception as e:
            print(f"--> SERVER CRASHED WITH ERROR: {e}", file=sys.stderr, flush=True)

#fig.write_html ( "M:/DREAM Lab/Obesity Supplement/Output Data/WuNelson_HDFCC_obesogenicfactors_adultobesity_20260512.html" )
