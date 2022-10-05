# SmartGym SmartPhone Holder Service
This repository contains the source code for the SmartGym SmartPhone Holder service.  
Service returns machine data based on location.  
Service is hosted on gateway, port: 16000

## Paths of interest:
1. `GATEWAYIP:PORT` i.e. root.   
    Returns the data of the machines in the gateway location in JSON format  
    Example of data received:  
    `[{
        "name":"Shoulder Press",
        "type":"weightstack",
        "uuid":"5a1515ecce1c46c194044b30f860c826"
    }]`

2. `GATEWAYIP:PORT/location/`  
    Returns the machine data of other locations based on location specified  
    Example of endpoint: `192.168.5.9:16000/hbb/`

3. `GATEWAYIP:PORT/phs/location/`   
    Returns the machine:UUID data in JSON format  
    Example of endpoint: `192.168.5.9:16000/phs/hbb/`  
    Example of data received:  
    `[{
        "Shoulder Press":"5a1515ecce1c46c194044b30f860c826"
    }]`  
    Note: To get machine:UUID data of current gateway location, use: `GATEWAYIP:PORT/phs/here/`

## Current list of available locations: 
1. HBB
2. OTH
3. JE

