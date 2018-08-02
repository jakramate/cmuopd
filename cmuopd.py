import numpy as np
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import time, threading
import vehicleDynamics as vd
import bus as bus
from scipy.spatial.distance import euclidean

# summarise all buses on the database
def summary():
    global fleet

    for busnum in fleet:
        curBus = fleet[busnum]
        print('Bus {}/{} stops {} times, serves {} person, avg.speed {:.2f}'.format(
            curBus.number, curBus.route, curBus.numOfStops, curBus.usage, curBus.avgSpeed)) 

    threading.Timer(60, summary).start()


def parsePayload(msg):
    payload = dict()
    utfmsg = msg.decode("utf-8") # converting bytes to string
    res = [i for i in utfmsg[1:-1].split(",")]
    for feature in res:
        colpos = feature.find(":")
        payload[feature[0:colpos].strip('"')] = feature[colpos+1:]
    
    return payload


# The callback for when the client receives a CONNACK response from the server.
def handle_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("cmutransit/busonservice")

# The callback for when a PUBLISH message is received from the server.
def handle_message(client, userdata, msg):
    global fleet

    inBus = parsePayload(msg.payload)

    if inBus["bus"] not in fleet: # if current bus number is not in fleet
        fleet[inBus["bus"]] = bus.vBus() # create new bus        
        print("Bus number ", inBus["bus"], " added")

    
    curBus = fleet[inBus["bus"]] # curBus is a bus object
    curBus.number = inBus["bus"]
    curBus.route  = inBus["route"]


    # for translating the time window
    if curBus.x[-1] > 100:
        curBus.x = curBus.x[1:]
        curBus.y = curBus.y[1:]
    
    curBus.x = np.append(curBus.x, curBus.x[-1]+1)
 
    # moving average with window length of three
    #if len(curBus.y) > 3:
    #    curBus.y = np.append(curBus.y, (curBus.y[-2] + curBus.y[-1] 
    #        + np.array(float(inBus["speed"])))/3)
    #else:
    curBus.y = np.append(curBus.y, np.array(float(inBus["speed"])))
   
    if not curBus.stopped:
        curBus.lat = float(inBus["lat"])
        curBus.lng = float(inBus["lng"])
        
    # start/stop detection based on DTW
    location_diff = euclidean([curBus.prev_lat, curBus.prev_lng],[curBus.lat, curBus.lng])
        
    if vd.hasStopped(curBus.y[-20:]) and location_diff < 4e-5 and not curBus.stopped:
        print('Car number ', curBus.number,'/', curBus.route,
                ' has stopped at (', curBus.lat, curBus.lng,')')
        curBus.stopped = True
        curBus.numOfStops += 1

    if vd.hasStarted(curBus.y[-20:]) and curBus.stopped:
        print('Car number ', curBus.number, '/', curBus.route, 
                ' is departing from (', curBus.lat, curBus.lng,')')
        curBus.stopped = False
       
    curBus.prev_lat = curBus.lat
    curBus.prev_lng = curBus.lng
        
    # recoding passenger
    curBus.usage += int(inBus["geton"])

    # recording average speed
    if curBus.y[-1] > 4:
        curBus.avgSpeed = vd.updateAvgSpeed(curBus.avgSpeed, curBus.x[-1], curBus.y[-1])
    
    
    # for plotting
    #    line.set_ydata(y)
    #    line.set_xdata(x)
    #    plt.xlim(x[0],x[-1]) # adjusting x-axis markers
    #    plt.draw()
    #    plt.pause(0.1)

        
#=============== global =========================    
client = mqtt.Client()
client.on_connect = handle_connect
client.on_message = handle_message
client.username_pw_set("cmu_opd","morchor@4.0now")
client.connect("202.28.244.147")

# setting up empty dictionary for storing buses
fleet = {} 

# first call to summary function which
summary()

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
