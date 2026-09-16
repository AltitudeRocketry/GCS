import json
import requests
from pathlib import Path
import sys
import os

def CheckForUpdate():

    ToUpdate = {"GCS": {"updateAvailable": False, "ExeName": "GroundStation.exe"},
                "TestStand": {"updateAvailable": False, "ExeName": "TestStand.bin"},
                "FlightComputer": {"updateAvailable": False, "ExeName": "FlightComputer.bin"} }

    configFilePath = get_config_path()


    with open(configFilePath, 'r') as configFile:
        config = json.load(configFile)

    for system, data in config.items():

        if system in ToUpdate:
            try:
                if "downloadFile" in data:
                    ToUpdate[system]["ExeName"] = data["downloadFile"]

                if "repos" in data:
                    response = requests.get(data["repos"], timeout=2)
                    if response.status_code == 200:
                        remoteVersion = response.text.strip()
                        localVersion = data["localVersion"]
                        if remoteVersion != localVersion:
                            ToUpdate[system]["updateAvailable"] = True
                        else:
                            ToUpdate[system]["updateAvailable"] = False
            except Exception as e:
                print(f"Error checking updates for {system}: {e}")


    return ToUpdate


        # if system == "GCS":
        #     try:
        #         response = requests.get(data["repos"], timeout=2)
        #         if response.status_code == 200:
        #             remoteVersion = response.text.strip()
        #             localVersion = data["localVersion"]
        #             if remoteVersion != localVersion:
        #                 ToUpdate["GCS"][0] = True
        #             else:
        #                 ToUpdate["GCS"][0] = False
        #         response = requests.get(data["downloadFile"], timeout=2)
        #         if response.status_code == 200:
        #             exeName = response.text.strip()
        #             ToUpdate["GCS"][1] = exeName
        #     except:
        #         print("error")

        # elif system == "TestStand":
        #     try:
        #         response = requests.get(data["repos"], timeout=2)
        #         if response.status_code == 200:
        #             remoteVersion = response.text.strip()
        #             localVersion = data["localVersion"]

        #             if remoteVersion != localVersion:
        #                 ToUpdate["Test Stand"] = True
        #             else:
        #                 print("All good")
        #     except:
        #         print("error")
                
        # # elif system == "FlightComputer":
        # #     response = requests.get(data["repos"], timeout=2)
        # #     if response.status_code == 200:
        # #         remoteVersion = response.text.strip()
        # #         localVersion = data["localVersion"]

        # #         if remoteVersion != localVersion:
                    
        # #             ToUpdate[2] = True
        # #         else:
        # #             print("All good")
                    

    
        
def get_config_path():
    if getattr(sys, 'frozen', False):
        # App is compiled: config lives inside PyInstaller's temp folder
        base_dir = sys._MEIPASS
    else:
        # App is running as raw script: config lives in project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_dir, 'config', 'config.json')

# Usage for your update checker:


    

    
