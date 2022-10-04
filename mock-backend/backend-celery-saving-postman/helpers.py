from config import *

def processRedisBoolean(dicto):
    for k,v in dicto.items():
        if isinstance(v, str):
            if v.lower() == 'true':
                dicto[k] = True  
            if v.lower() == 'false':
                dicto[k] = False  
    return dicto

def j(*args):
    return ':'.join([str(ele) for ele in args])

def reformRedisStream(machineId):
    # Retrieve all data from data_stream
    raw = r.xrange(j(machineId, 'data_stream'))

    # Restructure the data into list of dictionary
    out = []
    for ts, val in raw:
        val = {
            k.decode(): v.decode() for k, v in val.items()
        }
        # ts: in milliseconds
        timeStr = ts.decode().split('-')[0]
        timeFloat = float(timeStr)/1000  
        val['timestamp'] = datetime.datetime.fromtimestamp(timeFloat, tz=tz_utc)
        val = processRedisBoolean(val)
        out.append(val)

    return out

def getRedisChannelDict(machineId):
    #Returns a dictionary of the current values stored in a particular key
    
    dicto = {}
    keyPattern = machineId + ":*"
    for key in r.scan_iter(keyPattern):
        ky = key.decode().split(":")[1]
        if ky != "data_stream":
            dicto[ky] = r.get(key).decode()
        else:
            dicto[ky] = reformRedisStream(machineId)
    if "timestamp" in dicto:
        timeFloat = float(dicto['timestamp'])
        dicto['timestamp'] = datetime.datetime.fromtimestamp(timeFloat, tz=tz_utc)

    return processRedisBoolean(dicto)