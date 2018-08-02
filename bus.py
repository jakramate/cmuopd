import numpy as np

# violet bus class 
# for storing potentially useful data


class vBus:
    route = 0          # bus route
    number = 0         # bus number
    numOfStops = 0     # number of times it stops
    stopped = False    # does it stop ?
    lat = 0            # current latitude
    lng = 0            # current longitude
    prev_lat = 0       # previous lat
    prev_lng = 0       # previous lng
    usage = 0          # total passengers today
    avgSpeed = 0       # storing average speed
    x = np.zeros(100)  # numpy array for storing timesteps
    y = np.zeros(100)  # numpy array for storing speed at each timesteps

