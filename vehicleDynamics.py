import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

# return the distance travelled in metres
def distanceTravelled(v):
    return (v[-1]+v[-2])/2 

# calculating average speed
def updateAvgSpeed(avgSpeed, t, v):
    return (t/(t+1)) * (avgSpeed + v/t)
    # shorter form with one less multiplication
    # return avgSpeed + (v - avgSpeed)/(t+1)

# determine if the bus has stopped
# we use dynamic time warping to check the similarity of the bus
# speed's pattern with the pattern that corresponds to stopping pattern
def hasStopped(v):
    # reference speed pattern
    vref = [6.2,5.94,6.2,5.92,6.0499997,
            5.8199997,5.5499997,4.5899997,3.81,3.53,3.01,
            2.48,2.56, 3.4499998,3.25,2.27,1.04,0.17,
            0.,0.31,1.5,2.5,1.9,0.5,0.,0.0,0.0,0.0,
            0.,0.,0.,0.,0.]
    # calculating the dtw
    distance, path = fastdtw(v, vref, dist=euclidean)

    if distance < 25: # if the pattern is similar within some threshold
        return True 
    else:
        return False

# determine if the bus has started
# currently we just need to check if the bus is up to some speed
def hasStarted(v):
    if np.mean(v[-10:]) > 4:
        return True 
    else:
        return False


