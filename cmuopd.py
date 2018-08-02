import numpy as np
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import time, threading
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

def summary():
    global fleet

    for busnum in fleet:
        curBus = fleet[busnum]
        print('Bus number', curBus.number, 'has stopped', curBus.numOfStops , 
                'times total passengers served ', curBus.usage)


    threading.Timer(60, summary).start()




# determine if the bus has stopped
def hasStopped(v):

    vref = [6.2,5.94,6.2,5.92,6.0499997,
            5.8199997,5.5499997,4.5899997,3.81,3.53,3.01,
            2.48,2.56, 3.4499998,3.25,2.27,1.04,0.17,
            0.,0.31,1.5,2.5,1.9,0.5,0.,0.0,0.0,0.0,
            0.,0.,0.,0.,0.]

    distance, path = fastdtw(v, vref, dist=euclidean)
    #print('stop dtw ',distance)

    if distance < 25:
        return True 
    else:
        return False

# determine if the bus has started
def hasStarted(v):
    #vref = [6.0,5.84,5.62,5.4799997,
    #        5.2199997,4.9499997,4.5899997,3.81,3.53,3.01,
    #        2.48,2.56, 3.4499998,3.25,2.27,1.04,0.17,
    #        0.,0.31,1.5,2.5,1.9,0.5,0.,0.,0.]
    
    #distance, path = fastdtw(v, vref[::-1], dist=euclidean)
    #print('start dtw ',distance)
    
    #if distance < 20:
    if np.mean(v[-10:]) > 4:
        return True 
    else:
        return False


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
        fleet[inBus["bus"]] = vBus() # create new bus        
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
        
    if hasStopped(curBus.y[-20:]) and location_diff < 4e-5 and not curBus.stopped:
        print('Car number ', curBus.number,'/', curBus.route,
                ' has stopped at (', curBus.lat, curBus.lng,')')
        curBus.stopped = True
        curBus.numOfStops += 1

    if hasStarted(curBus.y[-20:]) and curBus.stopped:
        print('Car number ', curBus.number, '/', curBus.route, 
                ' is departing from (', curBus.lat, curBus.lng,')')
        curBus.stopped = False
       
    curBus.prev_lat = curBus.lat
    curBus.prev_lng = curBus.lng
        
    # recoding passenger
    curBus.usage += float(inBus["geton"])
    
    
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

# the plotting
#plt.ion()
#plt.ylim(-1,10)
#plt.xlim(-1,101)
#ax = plt.gca()
#line, = ax.plot(0,0,'bo-')

# bus object
class vBus:
    stopped = False # for indicating if the bus has stopped
    number = 0
    route = 0
    numOfStops = 0
    prev_lat = 0
    prev_lng = 0
    lat = 0
    lng = 0
    usage = 0
    x = np.zeros(100) # representing time
    y = np.zeros(100) # representing speed at time t
    

fleet = {} # empty dictionary

summary()

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
