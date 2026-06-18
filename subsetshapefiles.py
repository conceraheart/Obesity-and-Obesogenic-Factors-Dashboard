import geopandas as gpd

print("Loading national counties (this will take a moment)...")
# Read only the rows matching California's State FIPS code ('06') using a lambda filter
# available in newer versions of geopandas/pyogrio, or read it once to filter it:
gdf_county_2010 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/US_county_2010.shp")
print ( gdf_county_2010.columns.tolist())
gdf_county_2020 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/US_county_2020.shp")
print ( gdf_county_2020.columns.tolist())
print ( "Loading national census tracts" )
gdf_ct_2010 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/US_tract_2010.shp")
gdf_ct_2020 = gpd.read_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/US_tract_2020.shp")
print("Filtering for California...")
# Filter for California (adjust column name 'STATEFP10' if your 2010/2020 files use different conventions)
ca_gdf_county_2010 = gdf_county_2010[gdf_county_2010['STATEFP10'] == '06']
ca_gdf_county_2020 = gdf_county_2020[gdf_county_2020['STATEFP'] == '06']

ca_gdf_ct_2010 = gdf_ct_2010[gdf_ct_2010['STATEFP10'] == '06']
ca_gdf_ct_2020 = gdf_ct_2020[gdf_ct_2020['STATEFP'] == '06']

print("Saving localized state-level file...")
ca_gdf_county_2010.to_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/CA_county_2010.shp")
ca_gdf_county_2020.to_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - county/CA_county_2020.shp")
ca_gdf_ct_2010.to_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/CA_tract_2010.shp")
ca_gdf_ct_2020.to_file("C:/Users/nelso/Downloads/Source Data/Census Area Units - census tract/CA_tract_2020.shp")
print("Done!")

