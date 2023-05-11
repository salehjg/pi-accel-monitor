echo "$1"
myip="$(hostname -I)"
myip_nospace=$(echo $myip | tr -d ' ')
echo "IP: ${myip_nospace}"
BOKEH_RESOURCES=inline bokeh serve $1 --allow-websocket-origin=${myip_nospace}:5006
