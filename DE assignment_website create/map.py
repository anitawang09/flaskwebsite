import sqlite3
import pandas as pd
import geopandas as gpd
import plotly.express as px

# 1) Load your emissions data from the SQLite DB
conn = sqlite3.connect('cleaned_data.db')
df = pd.read_sql_query("""
    SELECT continent, emission_rate, quarter
      FROM emissions
""", conn)
conn.close()

# Ensure quarter is treated as a string (so the slider frames read nicely)
df['quarter'] = df['quarter'].astype(str)

# 2) Load the Natural Earth low-res world map and dissolve into continents
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
continents = world.dissolve(by='continent', as_index=False)[['continent','geometry']]

# 3) Merge your emissions onto the continent shapes
geo_df = continents.merge(df, on='continent')

# 4) Convert to GeoJSON for Plotly
#    We're going to use the entire GeoDataFrame as a FeatureCollection
geojson = geo_df.to_json()

# 5) Build the Plotly Express choropleth
fig = px.choropleth(
    df, 
    geojson=geojson,
    locations='continent',           # matches the featureidkey below
    color='emission_rate',
    animation_frame='quarter',       # this creates the time slider
    featureidkey='properties.continent',
    projection='natural earth',
    color_continuous_scale='OrRd',
    labels={'emission_rate': 'MtCO₂e'},
)

# 6) Clean up the map display
fig.update_geos(
    fitbounds="locations", 
    visible=False
)
fig.update_layout(
    title_text='Quarterly CO₂ Emissions by Continent',
    margin={"r":0,"t":50,"l":0,"b":0}
)

# 7) Show it (in Jupyter) or write out to HTML:
fig.show()
# Or, to save as a standalone HTML file:
# fig.write_html("continent_emissions_slider.html", include_plotlyjs='cdn')
# 8) Save the map to a file for later use
fig.write_image("continent_emissions_slider.png")