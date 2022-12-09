#!/usr/bin/env python
# coding: utf-8

# In[1]:


from IPython.display import HTML
HTML('''<script>
  function code_toggle() {
    if (code_shown){
      $('div.input').hide('500');
      $('#toggleButton').val('Show Code')
    } else {
      $('div.input').show('500');
      $('#toggleButton').val('Hide Code')
    }
    code_shown = !code_shown
  }
  $( document ).ready(function(){
    code_shown=false;
    $('div.input').hide()
  });
</script>
<form action="javascript:code_toggle()"><input type="submit" id="toggleButton" value="Show Code"></form>''')


# # Imports and Data Loading

# In[2]:


import math

import pandas as pd
import numpy as np
import geopandas as gpd

from bokeh.io import output_notebook, show
from bokeh.plotting import figure, ColumnDataSource
from bokeh.palettes import RdYlGn, Blues8
from bokeh.transform import linear_cmap
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter, LinearInterpolator

import xyzservices.providers as xyz

df = pd.read_csv('traffic.zip', parse_dates={'timestamp':[0,1]})
df.columns = map(str.lower, df.columns)
for col in ['borough', 'on street name', 'cross street name', 'off street name']:
    df[col] = df[col].str.lower()
df.columns = df.columns.str.replace(' ','_')
df = df[['timestamp', 'borough', 'zip_code', 'latitude', 'longitude', 'on_street_name', 'number_of_persons_injured', 'number_of_persons_killed', 'contributing_factor_vehicle_1']]
df = df.dropna(subset=['borough', 'zip_code', 'latitude'])
df.zip_code = df.zip_code.apply(lambda x: str(int(x)))
df['timestamp']=df['timestamp'].astype(str)
df = df[df.latitude != 0]
df = df.reset_index(drop=True)


# # Data work for points for accidents with injuries

# ## Convert latitude and longitude to Web Mercator projection

# In[3]:


# Define function to switch from lat/long to mercator coordinates

# derived from the Java version explained here: http://wiki.openstreetmap.org/wiki/Mercator
RADIUS = 6378137.0 # in meters on the equator

def latitude_to_mercator_y(lat):
  return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * RADIUS

def longitude_to_mercator_x(long):
  return math.radians(long) * RADIUS

df['mercator_x'] = df.longitude.apply(longitude_to_mercator_x)
df['mercator_y'] = df.latitude.apply(latitude_to_mercator_y)


# ## Create bins to sort accidents by number of persons injured

# In[4]:


# drop all accidents with 0 injuries
df = df[df['number_of_persons_injured'] > 0]
df = df.sort_values('number_of_persons_injured')

# The number of persons injured is essentially 1-8.
# Create a bin for each, but include the five accidents
# with more than 8 in the bin with 8 injuries
df['injury_bins'] = df['number_of_persons_injured']
df.loc[df['injury_bins'] > 7, 'injury_bins'] = 8


# ## Define points size and color

# In[5]:


# Define color mapper for points - which will define the color of the data points
pcolor_mapper = linear_cmap(
    field_name = 'injury_bins', 
    palette = RdYlGn[8], 
    low = df['injury_bins'].min(), 
    high = df['injury_bins'].max()
)

# Define size mapper for points - which will define the size of the data points
psize_mapper = LinearInterpolator(
    x=[1,8],
    y=[2,20]
)


# # Create map

# ## Create map features

# In[6]:


# Set tooltips - these appear when we hover over a data point in our map
tooltips = [
    ('Date and Time of Accident', '@timestamp'), 
    ("Number of Persons Injured","@number_of_persons_injured"), 
    ("Zip Code","@zip_code"), 
    ('Cause of Accident','@contributing_factor_vehicle_1')
]


# ## Create map and add points and grids

# In[7]:


get_ipython().run_cell_magic('capture', '', '\n# Create the figure\np = figure(\n    title = \'Traffic Accidents, NYC, 2020\', \n    x_axis_type="mercator", \n    y_axis_type="mercator", \n    x_axis_label="Longitude",\n    y_axis_label = \'Latitude\', \n    tooltips = tooltips\n)\n\n# Add the underlying tile\np.add_tile(xyz.CartoDB.Positron)\n\n# Add the points for each accident with injuries\np.circle(\n    x = \'mercator_x\', \n    y = \'mercator_y\', \n    color = pcolor_mapper, \n    source = ColumnDataSource(data=df),\n    size = {\'field\': \'injury_bins\', \'transform\': psize_mapper},\n    alpha = 0.7\n)\n')


# # Display map

# In[8]:


output_notebook()
show(p)

