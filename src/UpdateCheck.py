import json
import requests
from pathlib import Path

def CheckForUpdate():

    ToUpdate = [False, False, False]
    script_dir = Path(__file__).parent.parent
    configFilePath = script_dir / "config" / "config.json"

    with open(configFilePath, 'r') as configFile:
        config = json.load(configFile)

    for system, data in config.items():
        if system == "MainApp":
            try:
                response = requests.get(data["repos"], timeout=2)
                if response.status_code == 200:
                    remoteVersion = response.text.strip()
                    localVersion = data["localVersion"]

                    if remoteVersion != localVersion:
                        ToUpdate[0] = True
                    else:
                        print("All good")
            except:
                print("error")

        elif system == "TestStand":
            try:
                response = requests.get(data["repos"], timeout=2)
                if response.status_code == 200:
                    remoteVersion = response.text.strip()
                    localVersion = data["localVersion"]

                    if remoteVersion != localVersion:
                        ToUpdate[1] = True
                    else:
                        print("All good")
            except:
                print("error")
                
        # elif system == "FlightComputer":
        #     response = requests.get(data["repos"], timeout=2)
        #     if response.status_code == 200:
        #         remoteVersion = response.text.strip()
        #         localVersion = data["localVersion"]

        #         if remoteVersion != localVersion:
                    
        #             ToUpdate[2] = True
        #         else:
        #             print("All good")
                    

    return ToUpdate
    
        
    

    

    
