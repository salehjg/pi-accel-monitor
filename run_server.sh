echo "$1"
BOKEH_RESOURCES=inline bokeh serve $1 --allow-websocket-origin=192.168.100.100:5006
