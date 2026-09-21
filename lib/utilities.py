from pathlib import Path
from typing import Iterator, Union, List, Dict, Any, Optional
from json import loads as jsloads, load as jsload, dump as jsdump, dumps as jsdumps, JSONDecodeError
from dataclasses import dataclass
from base64 import b64decode
from zlib import decompress as zdecompress
from lib.gameio import iterDecodeFromFile, encodeToFile

@dataclass
class const:
    CWD: Path = Path.cwd()
    CONFIG_PATH: Path = CWD / 'config.json'
    ITEMS_PATH: Path = CWD / 'items.json'
    DEFAULT_CONFIG = {
        'current_profile': None,
        'current_profile_name': None,
        'active_profiles': None,
        'active_profiles_names': None
    }
    VERSION: str = '5.0.1'
    ITEMS: str = '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'

# Variable staging global untuk Android
ACTIVE_SAVE_FILE = Path("temp_profile.save")

def loadSave(filepath: Optional[Union[str, Path]] = None) -> Any:
    target = Path(filepath) if filepath else ACTIVE_SAVE_FILE
    try:
        rawData = b''.join(iterDecodeFromFile(target))
        data = jsloads(rawData)
        if not isinstance(data, dict) or 'Inventory' not in data or not isinstance(data['Inventory'], dict):
            raise ValueError("Struktur file save tidak valid")
        return data
    except JSONDecodeError as e:
        print(f"Error decode JSON save: {e}")
        return None
    except Exception as e:
        print(f"Error memuat save: {e}")
        return None

def writeSave(data: dict, filepath: Optional[Union[str, Path]] = None) -> None:
    target = Path(filepath) if filepath else ACTIVE_SAVE_FILE
    with target.open("wb+") as fp:
        encodeToFile(jsdumps(data).encode("utf-8"), fp)

def getProfiles(userData: Optional[dict] = None) -> List[str]:
    data = userData if userData else loadSave()
    if data is None:
        return []
    try:
        return [i for i in data['Inventory'].keys() if isinstance(data['Inventory'][i], dict) and data['Inventory'][i].get('Loaded')]
    except Exception as e:
        print(f"Error parsing profiles: {e}")
        return []

def getNames(userData: Optional[dict] = None) -> List[str]:
    data = userData if userData else loadSave()
    if data is None:
        return []
    try:
        return [
            data['Inventory'][key]['Name']
            for key in data['Inventory'].keys()
            if isinstance(data['Inventory'][key], dict) and 'Name' in data['Inventory'][key]
        ]
    except Exception as e:
        print(f"Error parsing names: {e}")
        return []

def loadItems():
    if not const.ITEMS_PATH.exists():
        decoded = b64decode(const.ITEMS)
        decompressed = jsloads(zdecompress(decoded))
        with open(const.ITEMS_PATH, 'w') as f:
            jsdump(decompressed, f)
    with open(const.ITEMS_PATH) as f:
        return jsload(f)

def loadConfig() -> Dict[str, Any]:
    if not const.CONFIG_PATH.exists():
        with open(const.CONFIG_PATH, 'w') as f:
            jsdump(const.DEFAULT_CONFIG, f, indent=4)
        return const.DEFAULT_CONFIG
    try:
        with open(const.CONFIG_PATH) as f:
            return jsload(f)
    except Exception:
        return const.DEFAULT_CONFIG

def writeConfig(data: Dict[str, Any]) -> None:
    with open(const.CONFIG_PATH, 'w') as f:
        jsdump(data, f, indent=4)