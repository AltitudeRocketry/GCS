import json
import requests
from pathlib import Path

def CheckForUpdate():
    script_dir = Path(__file__).parent.parent
    versionFilePath = script_dir / "config" / "config.json"

    with open(versionFilePath, 'r') as versionFile:
        version = json.load(versionFile)

        

    
        
    

    

    
