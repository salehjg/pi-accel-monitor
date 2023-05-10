## simple_bokeh_dashboard.py
import bokeh
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.io import curdoc
from bokeh.plotting import figure

import requests
import time
from datetime import datetime
import random

data_source = ColumnDataSource(data = {"Close": [], "DateTime": []}) ## Data Source

## Create Line Chart
fig = figure(x_axis_type="datetime",
#             plot_width=950, plot_height=450,
             tooltips=[("Close", "@Close")], title = "Bitcoin Close Price Live (Every Second)")

fig.line(x="DateTime", y="Close", line_color="tomato", line_width=3.0, source=data_source,)

fig.xaxis.axis_label="Date"
fig.yaxis.axis_label="Price ($)"
fig.xaxis.formatter=DatetimeTickFormatter( seconds = '%Y_%m_%D_%H_%M_%S')
fig.xaxis.major_label_orientation = 0.785 # pi/4

counter = 0
## Define Callbacks
def update_chart():
    global data_source
    resp = requests.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD")
    hist_data = resp.json()
    #new_row = {"Close": [hist_data["USD"]], "DateTime": [datetime.now(), ]}
    new_row = {"Close": [random.random()], "DateTime":[datetime.now()]}
    #counter = counter + 1
    data_source.stream(new_row)

curdoc().add_periodic_callback(update_chart, 1000)

curdoc().add_root(fig)

