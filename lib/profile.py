from lib.account import (
    _setNightmareTicketsLogic,
    _setTokensLogic,
    _setCreditsLogic,
    _removeAdsLogic,
    _unlockWeaponCollectionLogic,
    _unlockArmorCollectionLogic,
    _toggleCollectionRewardsLogic,
)
from lib.utilities import (
    loadSave,
    writeSave,
    loadConfig,
    getProfiles,
    loadItems
)
from random import randint
import numpy as np
from functools import partial
# ==========================================
# 1. LOGIC FUNCTIONS (Memory only, without I/O)
# ==========================================

def _setMoneyLogic(userData, profile, amount):
    userData['Inventory'][profile]['Money'] = amount
    return f'Set {amount:,}$ to {profile}'

def _setLevelLogic(userData, profile, level):
    XP_ARR = [
        0, 1071, 1288, 1655, 2176, 2855, 3696, 4704, 5883, 7237, 8770, 10486, 12390, 
        14486, 16778, 19270, 21966, 24871, 27989, 31324, 34880, 38661, 42672, 46917, 
        51400, 56125, 91145, 98978, 107193, 115797, 124795, 134195, 144002, 154222, 
        164863, 175930, 187430, 199368, 211752, 224587, 237880, 251637, 265865, 280569, 
        295756, 311433, 327605, 344279, 361461, 379158, 397375, 416120, 435398, 455215, 
        475579, 496495, 517970, 540009, 562620, 585808, 609580, 844923, 878201, 912282, 
        947176, 982890, 1019433, 1056813, 1095038, 1134118, 1174060, 1214873, 1256565, 
        1299144, 1342620, 1387000, 1432293, 1478507, 1525650, 1573732, 1622760, 1672743, 
        1723689, 1775606, 1828504, 1882390, 1937273, 1993161, 2050062, 2107986, 2166940, 
        3339899, 3431459, 3524603, 3619342, 3715690, 3813659, 3913262, 4014512, 4117420]
    total = sum(XP_ARR[:level])
    userData['Inventory'][profile]['Skills']['PlayerLevel'] = level
    userData['Inventory'][profile]['Skills']['PlayerTotalXp'] = total
    return f"Set profile level to {level}"

def _setBlackKeysLogic(userData, profile, amount):
    userData['Inventory'][profile]['Skills']['AvailableBlackKeys'] = amount
    return f'Set {amount:,} black keys to {profile}'

def _setAugCoresLogic(userData, profile, amount):
    userData['Inventory'][profile]['Skills']['AvailableEliteAugmentCores'] = amount
    return f'Set {amount:,} augment cores to {profile}'

def _setRandBlackStrongboxLogic(userData, profile, amount):
    amount = min(max(0, amount), 100000)
    userData['Inventory'][profile]['Skills']['AvailableBlackStrongboxes'] = np.random.randint(100000, 99999999999, size=amount, dtype=np.int64).tolist()
    return f'Set {amount:,} black strongboxes to {profile}'

def _activateSkillResetLogic(userData, profile, boolean):
    current = userData['Inventory'][profile].get('FreeSkillsReset', False)
    new_val = not current if boolean is None else boolean
    userData['Inventory'][profile]['FreeSkillsReset'] = new_val
    return f"{'Activated free skill reset' if new_val else 'Deactivated free skill reset'}"

def _changeUsernameLogic(userData, profile, name):
    userData['Inventory'][profile]['Name'] = name
    return f'Name set to: {name}'

def _setGrenadesLogic(userData, profile, grenade, amount):
    GRENADES = [('Cryo grenades', 'grenades_cryo'), ('Frag grenades', 'grenades_frag')]
    if grenade == 'ALL':
        for optionName, identifier in GRENADES:
            userData['Inventory'][profile]['Ammo'][identifier] = amount
        return f'All grenades amount successfully set to {amount:,}'
    
    optionName, identifier = next(((g[0], g[1]) for g in GRENADES if g[0] == grenade), (None, None))
    if identifier:
        userData['Inventory'][profile]['Ammo'][identifier] = amount
        return f'{optionName} set to {amount:,}'
    return "Grenade not found."

def _deleteProfileLogic(userData, profile):
    userData['Inventory'][profile] = {"Loaded": False}
    return f'Profile {profile} has been deleted'

def _setTurretsLogic(userData, profile, turretItems, turret, amount):
    turretType = 'normal' if userData['Inventory'][profile]['Skills']['PlayerLevel'] <= 30 else 'red'
    TURRETS = [(t['Name'], t['ID']) for t in turretItems[turretType]]
    
    if turret == 'ALL':
        for optionName, turretID in TURRETS:
            for i in userData['Inventory'][profile]['Turrets']:
                if i.get('TurretId') == turretID:
                    i['TurretCount'] = amount
                    break
            else:
                userData['Inventory'][profile]['Turrets'].append({'TurretId': turretID, 'TurretCount': amount})
        return f'All turrets amount successfully set to {amount:,}'
    
    optionName, turretID = next(((t[0], t[1]) for t in TURRETS if t[0] == turret), (None, None))
    if turretID:
        for i in userData['Inventory'][profile]['Turrets']:
            if i.get('TurretId') == turretID:
                i['TurretCount'] = amount
                break
        else:
            userData['Inventory'][profile]['Turrets'].append({'TurretId': turretID, 'TurretCount': amount})
        return f'{optionName} turret amount set to: {amount}'
    return "Turret not found."

def _setPremiumWeaponsLogic(userData, profile, premiumItems, weaponType, bonus, augments, grade):
    if weaponType == 'ALL':
        owned_weapons = userData['Inventory'][profile].get('Weapons', [])
        added = updated = 0
        for category in premiumItems.keys():
            for selectedWeapon in premiumItems[category]:
                result = _grantWeapon(userData, profile, selectedWeapon, bonus, augments, grade, owned_weapons)
                added += result == 'added'
                updated += result == 'updated'
        return f'[SUCCESS] Added {added} new items, updated {updated} owned items across all categories.'
    return ''

def _setMasteryLevelsLogic(userData, profile):
    for i in userData['MasteryProgress'][f'Mastery{profile}']:
        i['MasteryXp'] = 542400
        i['MasteryLvl'] = 5
    return 'Masteries set to max level'

def _setAllAmmoLogic(userData, profile, amount):
    AMMO_KEYS = [
        "ammo_NN_pistol_mep", "ammo_NN_pistol_thermal", "ammo_NN_pistol_energy", "ammo_NN_pistol_chemical",
        "ammo_NN_smg_mep", "ammo_NN_smg_thermal", "ammo_NN_smg_energy", "ammo_NN_smg_chemical",
        "ammo_NN_assault_mep", "ammo_NN_assault_thermal", "ammo_NN_assault_energy", "ammo_NN_assault_chemical",
        "ammo_NN_shotgun_mep", "ammo_NN_shotgun_thermal", "ammo_NN_shotgun_energy", "ammo_NN_shotgun_chemical",
        "ammo_NN_sniper_mep", "ammo_NN_sniper_thermal", "ammo_NN_sniper_energy", "ammo_NN_sniper_chemical",
        "ammo_NN_rocket_mep", "ammo_NN_rocket_thermal", "ammo_NN_rocket_energy", "ammo_NN_rocket_chemical",
        "ammo_NN_paw_mep", "ammo_NN_paw_thermal", "ammo_NN_paw_energy", "ammo_NN_paw_chemical",
        "ammo_NN_flame_mep", "ammo_NN_flame_thermal", "ammo_NN_flame_energy", "ammo_NN_flame_chemical",
        "ammo_NN_lmg_mep", "ammo_NN_lmg_thermal", "ammo_NN_lmg_energy", "ammo_NN_lmg_chemical",
        "ammo_NN_disk_mep", "ammo_NN_disk_thermal", "ammo_NN_disk_energy", "ammo_NN_disk_chemical",
        "ammo_NN_laser_mep", "ammo_NN_laser_thermal", "ammo_NN_laser_energy", "ammo_NN_laser_chemical",
        "ammo_NP_pistol_mep", "ammo_NP_pistol_thermal", "ammo_NP_pistol_energy", "ammo_NP_pistol_chemical",
        "ammo_NP_smg_mep", "ammo_NP_smg_thermal", "ammo_NP_smg_energy", "ammo_NP_smg_chemical",
        "ammo_NP_assault_mep", "ammo_NP_assault_thermal", "ammo_NP_assault_energy", "ammo_NP_assault_chemical",
        "ammo_NP_shotgun_mep", "ammo_NP_shotgun_thermal", "ammo_NP_shotgun_energy", "ammo_NP_shotgun_chemical",
        "ammo_NP_sniper_mep", "ammo_NP_sniper_thermal", "ammo_NP_sniper_energy", "ammo_NP_sniper_chemical",
        "ammo_NP_rocket_mep", "ammo_NP_rocket_thermal", "ammo_NP_rocket_energy", "ammo_NP_rocket_chemical",
        "ammo_NP_paw_mep", "ammo_NP_paw_thermal", "ammo_NP_paw_energy", "ammo_NP_paw_chemical",
        "ammo_NP_flame_mep", "ammo_NP_flame_thermal", "ammo_NP_flame_energy", "ammo_NP_flame_chemical",
        "ammo_NP_lmg_mep", "ammo_NP_lmg_thermal", "ammo_NP_lmg_energy", "ammo_NP_lmg_chemical",
        "ammo_NP_disk_mep", "ammo_NP_disk_thermal", "ammo_NP_disk_energy", "ammo_NP_disk_chemical",
        "ammo_NP_laser_mep", "ammo_NP_laser_thermal", "ammo_NP_laser_energy", "ammo_NP_laser_chemical",
        "ammo_RN_pistol_mep", "ammo_RN_pistol_thermal", "ammo_RN_pistol_energy", "ammo_RN_pistol_chemical",
        "ammo_RN_smg_mep", "ammo_RN_smg_thermal", "ammo_RN_smg_energy", "ammo_RN_smg_chemical",
        "ammo_RN_assault_mep", "ammo_RN_assault_thermal", "ammo_RN_assault_energy", "ammo_RN_assault_chemical",
        "ammo_RN_shotgun_mep", "ammo_RN_shotgun_thermal", "ammo_RN_shotgun_energy", "ammo_RN_shotgun_chemical",
        "ammo_RN_sniper_mep", "ammo_RN_sniper_thermal", "ammo_RN_sniper_energy", "ammo_RN_sniper_chemical",
        "ammo_RN_rocket_mep", "ammo_RN_rocket_thermal", "ammo_RN_rocket_energy", "ammo_RN_rocket_chemical",
        "ammo_RN_paw_mep", "ammo_RN_paw_thermal", "ammo_RN_paw_energy", "ammo_RN_paw_chemical",
        "ammo_RN_flame_mep", "ammo_RN_flame_thermal", "ammo_RN_flame_energy", "ammo_RN_flame_chemical",
        "ammo_RN_lmg_mep", "ammo_RN_lmg_thermal", "ammo_RN_lmg_energy", "ammo_RN_lmg_chemical",
        "ammo_RN_disk_mep", "ammo_RN_disk_thermal", "ammo_RN_disk_energy", "ammo_RN_disk_chemical",
        "ammo_RN_laser_mep", "ammo_RN_laser_thermal", "ammo_RN_laser_energy", "ammo_RN_laser_chemical",
        "ammo_RP_pistol_mep", "ammo_RP_pistol_thermal", "ammo_RP_pistol_energy", "ammo_RP_pistol_chemical",
        "ammo_RP_smg_mep", "ammo_RP_smg_thermal", "ammo_RP_smg_energy", "ammo_RP_smg_chemical",
        "ammo_RP_assault_mep", "ammo_RP_assault_thermal", "ammo_RP_assault_energy", "ammo_RP_assault_chemical",
        "ammo_RP_shotgun_mep", "ammo_RP_shotgun_thermal", "ammo_RP_shotgun_energy", "ammo_RP_shotgun_chemical",
        "ammo_RP_sniper_mep", "ammo_RP_sniper_thermal", "ammo_RP_sniper_energy", "ammo_RP_sniper_chemical",
        "ammo_RP_rocket_mep", "ammo_RP_rocket_thermal", "ammo_RP_rocket_energy", "ammo_RP_rocket_chemical",
        "ammo_RP_paw_mep", "ammo_RP_paw_thermal", "ammo_RP_paw_energy", "ammo_RP_paw_chemical",
        "ammo_RP_flame_mep", "ammo_RP_flame_thermal", "ammo_RP_flame_energy", "ammo_RP_flame_chemical",
        "ammo_RP_lmg_mep", "ammo_RP_lmg_thermal", "ammo_RP_lmg_energy", "ammo_RP_lmg_chemical",
        "ammo_RP_disk_mep", "ammo_RP_disk_thermal", "ammo_RP_disk_energy", "ammo_RP_disk_chemical",
        "ammo_RP_laser_mep", "ammo_RP_laser_thermal", "ammo_RP_laser_energy", "ammo_RP_laser_chemical",
        "ammo_BN_pistol_mep", "ammo_BN_pistol_thermal", "ammo_BN_pistol_energy", "ammo_BN_pistol_chemical",
        "ammo_BN_smg_mep", "ammo_BN_smg_thermal", "ammo_BN_smg_energy", "ammo_BN_smg_chemical",
        "ammo_BN_assault_mep", "ammo_BN_assault_thermal", "ammo_BN_assault_energy", "ammo_BN_assault_chemical",
        "ammo_BN_shotgun_mep", "ammo_BN_shotgun_thermal", "ammo_BN_shotgun_energy", "ammo_BN_shotgun_chemical",
        "ammo_BN_sniper_mep", "ammo_BN_sniper_thermal", "ammo_BN_sniper_energy", "ammo_BN_sniper_chemical",
        "ammo_BN_rocket_mep", "ammo_BN_rocket_thermal", "ammo_BN_rocket_energy", "ammo_BN_rocket_chemical",
        "ammo_BN_paw_mep", "ammo_BN_paw_thermal", "ammo_BN_paw_energy", "ammo_BN_paw_chemical",
        "ammo_BN_flame_mep", "ammo_BN_flame_thermal", "ammo_BN_flame_energy", "ammo_BN_flame_chemical",
        "ammo_BN_lmg_mep", "ammo_BN_lmg_thermal", "ammo_BN_lmg_energy", "ammo_BN_lmg_chemical",
        "ammo_BN_disk_mep", "ammo_BN_disk_thermal", "ammo_BN_disk_energy", "ammo_BN_disk_chemical",
        "ammo_BN_laser_mep", "ammo_BN_laser_thermal", "ammo_BN_laser_energy", "ammo_BN_laser_chemical",
        "ammo_BP_pistol_mep", "ammo_BP_pistol_thermal", "ammo_BP_pistol_energy", "ammo_BP_pistol_chemical",
        "ammo_BP_smg_mep", "ammo_BP_smg_thermal", "ammo_BP_smg_energy", "ammo_BP_smg_chemical",
        "ammo_BP_assault_mep", "ammo_BP_assault_thermal", "ammo_BP_assault_energy", "ammo_BP_assault_chemical",
        "ammo_BP_shotgun_mep", "ammo_BP_shotgun_thermal", "ammo_BP_shotgun_energy", "ammo_BP_shotgun_chemical",
        "ammo_BP_sniper_mep", "ammo_BP_sniper_thermal", "ammo_BP_sniper_energy", "ammo_BP_sniper_chemical",
        "ammo_BP_rocket_mep", "ammo_BP_rocket_thermal", "ammo_BP_rocket_energy", "ammo_BP_rocket_chemical",
        "ammo_BP_paw_mep", "ammo_BP_paw_thermal", "ammo_BP_paw_energy", "ammo_BP_paw_chemical",
        "ammo_BP_flame_mep", "ammo_BP_flame_thermal", "ammo_BP_flame_energy", "ammo_BP_flame_chemical",
        "ammo_BP_lmg_mep", "ammo_BP_lmg_thermal", "ammo_BP_lmg_energy", "ammo_BP_lmg_chemical",
        "ammo_BP_disk_mep", "ammo_BP_disk_thermal", "ammo_BP_disk_energy", "ammo_BP_disk_chemical",
        "ammo_BP_laser_mep", "ammo_BP_laser_thermal", "ammo_BP_laser_energy", "ammo_BP_laser_chemical",
    ]
    ammo_dict = userData['Inventory'][profile].setdefault('Ammo', {})
    ammo_dict.update(dict.fromkeys(AMMO_KEYS, amount))
    return f'[SUCCESS] All types of ammo successfully set to {amount:,}'

# def _characterBuildLogic(userData, profile, BUILDS, buildName):
#     inventory = userData['Inventory'][profile]
#     current_class = inventory['Skills'].get('Class')

#     selected_preset = BUILDS.get(buildName)
#     if not selected_preset:
#         return f"[FAILED] Preset '{buildName}' not found."

#     for w in inventory.get('Weapons', []):
#         if w.get('EquippedSlot'):
#             w['EquippedSlot'] = -1

#     for w in inventory.get('Equipment', []):
#         if w.get('Equipped'):
#             w['Equipped'] = False

#     next_weapon_index = max([w.get('InventoryIndex', -1) for w in inventory.get('Weapons', [])] + [-1]) + 1
#     next_armor_index = max([e.get('InventoryIndex', -1) for e in inventory.get('Equipment', [])] + [-1]) + 1

#     preset_weapons = [dict(item) for item in selected_preset.get("Weapons", [])]
#     preset_equipment = [dict(item) for item in selected_preset.get("Equipment", [])]
    
#     for i, w in enumerate(preset_weapons):
#         w['InventoryIndex'] = next_weapon_index + i
#         w['Seen'] = True 

#     for i, e in enumerate(preset_equipment):
#         e['InventoryIndex'] = next_armor_index + i
#         e['Seen'] = True
#         e['Equipped'] = True
    
#     if 'Weapons' not in inventory: inventory['Weapons'] = []
#     if 'Equipment' not in inventory: inventory['Equipment'] = []
    
#     inventory['Weapons'].extend(preset_weapons)
#     inventory['Equipment'].extend(preset_equipment)

#     skills_section = inventory['Skills']
#     skills_section['PlayerLevel'] = 100
#     skills_section['PlayerTotalXp'] = 87977897
#     skills_section['AvailableSkillPoints'] = 0
    
#     class_names = {1: "Medic", 2: "Assault", 3: "Heavy"}
#     preset_skills_map = selected_preset.get("Skills", {})
    
#     if current_class in preset_skills_map:
#         skills_section['SkillsArray'] = preset_skills_map[current_class]
#         class_status = class_names.get(current_class, f"Class {current_class}")
#     else:
#         return f"[FAILED] Preset '{buildName}' does not support your current class."
        
#     return f"Applied '{buildName}' configuration for {class_status} successfully!"

def _grantStrongboxLogic(userData, profile, strongbox, itemType):
    box_type = 0 if itemType == 'weapon' else 1
    userData['Inventory'][profile]['Strongboxes']['Claimed'].extend([box_type, strongbox, 8, 2])

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def _resolveStats(bonus, augments, grade, maxAugments=4):
    grade = promptInt('Set item grade [0-12]: ', minValue=0, maxValue=12) if grade is None or not (0 <= grade <= 12) else grade
    augments = promptInt(f'Set item augments [0-{maxAugments}]: ', minValue=0, maxValue=maxAugments) if augments is None or not (0 <= augments <= maxAugments) else augments
    bonus = promptInt('Set item bonus stats [0-10]: ', minValue=0, maxValue=10) if bonus is None or not (0 <= bonus <= 10) else bonus
    return bonus, augments, grade

def _buildStrongbox(ID, grade, augments, bonus, equipVersion=0, equippedSlot=-1, inventoryIndex=0, equipped=None):
    strongbox = {
        "ID": ID,
        "EquipVersion": equipVersion,
        "Grade": grade,
        "EquippedSlot": equippedSlot,
        "AugmentSlots": augments,
        "InventoryIndex": inventoryIndex,
        "Seen": False,
        "BonusStatsLevel": bonus,
        "ContainsKey": False,
        "ContainsAugmentCore": False,
        "BlackStrongboxSeed": 0,
        "UseDefaultOpenLogic": True
    }
    if equipped is not None:
        strongbox["Equipped"] = equipped
    return strongbox

def _grantWeapon(userData, profile, selectedWeapon, bonus, augments, grade, owned_weapons):
    weaponID = selectedWeapon['ID']
    for w in owned_weapons:
        if isinstance(w, dict) and w.get('ID') == weaponID:
            w['Grade'] = grade
            w['AugmentSlots'] = augments
            w['BonusStatsLevel'] = bonus
            return 'updated'

    strongbox = _buildStrongbox(weaponID, grade, augments, bonus)
    _grantStrongboxLogic(userData, profile, strongbox, 'weapon')
    return 'added'

# ==========================================
# 3. WRAPPER FUNCTIONS (Pending Disk I/O)
# ==========================================

@directFunction
def setMoney(amount: int = None):
    if amount is None:
        amount = promptInt('Set money amount: ', minValue=0)
    
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setMoneyLogic(userData, profile, amount)
    writeSave(userData)
    return log

@directFunction
def setLevel(level: int = None):
    if level is None:
        level = promptInt('Set level (0-100): ', minValue=0, maxValue=100)
    
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setLevelLogic(userData, profile, level)
    writeSave(userData)
    return log

@directFunction
def setBlackKeys(amount: int = None):
    if amount is None:
        amount = promptInt('Set black keys amount: ', minValue=0)
        
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setBlackKeysLogic(userData, profile, amount)
    writeSave(userData)
    return log

@directFunction
def setAugCores(amount: int = None):
    if amount is None:
        amount = promptInt('Set augment cores amount: ', minValue=0)
        
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setAugCoresLogic(userData, profile, amount)
    writeSave(userData)
    return log

@directFunction
def setRandBlackStrongbox(amount: int = None):
    if amount is None:
        amount = promptInt('Set black strongboxes amount: ', minValue=0, maxValue=100000)
        
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setRandBlackStrongboxLogic(userData, profile, amount)
    writeSave(userData)
    return log

@directFunction
def activateSkillReset(boolean: bool = None):
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _activateSkillResetLogic(userData, profile, boolean)
    writeSave(userData)
    return log

@directFunction
def changeUsername():
    name = promptStr('Set new name: ')
    
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _changeUsernameLogic(userData, profile, name)
    writeSave(userData)
    return log

@menuOptions
def setGrenades(grenade: str = '__menu_options__', amount: int = None):
    GRENADES = [('Cryo grenades', 'grenades_cryo'), ('Frag grenades', 'grenades_frag')]

    if grenade == '__menu_options__':
        options = [f"{g[0]}" for g in GRENADES]
        options.extend(['ALL'])
        return options

    if amount is None:
        prompt_msg = 'Enter amount for all grenades: ' if grenade == 'ALL' else 'Enter amount: '
        amount = promptInt(prompt_msg, minValue=0)
        
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setGrenadesLogic(userData, profile, grenade, amount)
    writeSave(userData)
    return log

@menuOptions
def deleteProfile(profile: str = '__menu_options__'):
    if profile == '__menu_options__':
        return getProfiles()

    userData = loadSave()
    log = _deleteProfileLogic(userData, profile)
    writeSave(userData)
    return log

@menuOptions
def setTurrets(turret: str = '__menu_options__', amount: int = None):
    turretItems = loadItems()['turret']
    
    if turret == '__menu_options__':
        userData = loadSave()
        profile = loadConfig()['current_profile']
        turretType = 'normal' if userData['Inventory'][profile]['Skills']['PlayerLevel'] <= 30 else 'red'
        options = [t['Name'] for t in turretItems[turretType]]
        options.extend(['ALL'])
        return options

    if amount is None:
        prompt_msg = 'Enter amount for all turrets: ' if turret == 'ALL' else f'Set {turret} turrets amount: '
        amount = promptInt(prompt_msg, minValue=0)
        
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setTurretsLogic(userData, profile, turretItems, turret, amount)
    writeSave(userData)
    return log

@nestedMenuOptions
def setStdWeapons(weaponType: str = '__menu_options__', bonus: int = None, augments: int = None, grade: int = None):
    items = loadItems()

    if weaponType == '__menu_options__':
        return {w.capitalize().replace('_', ' '): partial(setStdWeapons, bonus=bonus, augments=augments, grade=grade) for w in items['weapons'].keys()}

    def setWeaponVersion(version: str = '__menu_options__', bonus=bonus, augments=augments, grade=grade):
        if version == '__menu_options__':
            return {
                v.capitalize(): partial(setWeaponVersion, bonus=bonus, augments=augments, grade=grade)
                for v in items['weapons'][weaponType.lower().replace(' ', '_')].keys()
            }
        
        WEAPONS = items['weapons'][weaponType.lower().replace(' ', '_')][version.lower()]
        
        def setWeapon(weapon: str = '__menu_options__', bonus=bonus, augments=augments, grade=grade):
            if weapon == '__menu_options__':
                return {w['Name']: partial(setWeapon, bonus=bonus, augments=augments, grade=grade) for w in WEAPONS}

            selectedWeapon = next((w for w in WEAPONS if w['Name'] == weapon), None)

            resolvedBonus, resolvedAugments, resolvedGrade = _resolveStats(bonus, augments, grade)
            
            equipVersion = {'normal': 0, 'red': 1, 'black': 2, 'factions': 3}.get(version.lower(), 0)
            strongbox = _buildStrongbox(selectedWeapon['ID'], resolvedGrade, resolvedAugments, resolvedBonus, equipVersion)
            
            userData = loadSave()
            profile = loadConfig()['current_profile']
            _grantStrongboxLogic(userData, profile, strongbox, 'weapon')
            writeSave(userData)
            
            return f'{weapon} ({version}) added to strongboxes with bonus: {resolvedBonus}, augments: {resolvedAugments}, grade: {resolvedGrade}'

        return setWeapon()

    return setWeaponVersion()

@nestedMenuOptions
def setArmour(armourType = '__menu_options__', bonus: int = None, augments: int = None, grade: int = None):
    items = loadItems()

    if armourType == '__menu_options__':
        return {a.capitalize().replace('_', ' '): partial(setArmour, bonus=bonus, augments=augments, grade=grade) for a in items['armour'].keys()}

    def setArmourVersion(version: str = '__menu_options__', bonus=bonus, augments=augments, grade=grade):
        if version == '__menu_options__':
            return {v.capitalize(): partial(setArmourVersion, bonus=bonus, augments=augments, grade=grade) for v in items['armour'][armourType.lower().replace(' ', '_')].keys()}
        
        ARMOUR = items['armour'][armourType.lower().replace(' ', '_')][version.lower()]
        
        def setArmourItem(armour: str = '__menu_options__', bonus=bonus, augments=augments, grade=grade):
            if armour == '__menu_options__':
                return {a['Name']: partial(setArmourItem, bonus=bonus, augments=augments, grade=grade) for a in ARMOUR}

            selectedWeapon = next((a for a in ARMOUR if a['Name'] == armour), None)
            if selectedWeapon:
                resolvedBonus, resolvedAugments, resolvedGrade = _resolveStats(bonus, augments, grade, maxAugments=3)

                equipVersion = {'normal': 0, 'red': 1, 'black': 2, 'factions': 3}.get(version.lower(), 0)
                equippedSlot = {'helmet': 1, 'vest': 2, 'gloves': 3, 'boots': 4, 'pants': 5}.get(armourType.lower(), 0)
                strongbox = _buildStrongbox(selectedWeapon['ID'], resolvedGrade, resolvedAugments, resolvedBonus, equipVersion, equippedSlot, inventoryIndex=-1, equipped=False)
                                
                userData = loadSave()
                profile = loadConfig()['current_profile']
                _grantStrongboxLogic(userData, profile, strongbox, 'armour')
                writeSave(userData)
                
                return f'{armour} ({version}) added to strongboxes with bonus: {resolvedBonus}, augments: {resolvedAugments}, grade: {resolvedGrade}'
            
        return setArmourItem()

    return setArmourVersion()

@nestedMenuOptions
def setPremiumWeapons(weaponType: str = '__menu_options__', bonus: int = None, augments: int = None, grade: int = None):
    items = loadItems()

    if weaponType == '__menu_options__':
        options = {w.capitalize().replace('_', ' '): partial(setPremiumWeapons, bonus=bonus, augments=augments, grade=grade) for w in items['premium'].keys()}
        options['ALL'] = setPremiumWeapons
        return options 

    if weaponType == 'ALL':
        bonus, augments, grade = _resolveStats(bonus, augments, grade)
        
        userData = loadSave()
        profile = loadConfig()['current_profile']
        log = _setPremiumWeaponsLogic(userData, profile, items['premium'], 'ALL', bonus, augments, grade)
        writeSave(userData)
        return log

    WEAPONS = items['premium'][weaponType.lower().replace(' ', '_')]

    def setPremWeapon(weapon: str = '__menu_options__', bonus=bonus, augments=augments, grade=grade):
        if weapon == '__menu_options__':
            return {w['Name']: partial(setPremWeapon, bonus=bonus, augments=augments, grade=grade) for w in WEAPONS}

        selectedWeapon = next((w for w in WEAPONS if w['Name'] == weapon), None)
        
        resolvedBonus, resolvedAugments, resolvedGrade = _resolveStats(bonus, augments, grade)
        
        userData = loadSave()
        profile = loadConfig()['current_profile']
        owned_weapons = userData['Inventory'][profile].get('Weapons', [])
        result = _grantWeapon(userData, profile, selectedWeapon, resolvedBonus, resolvedAugments, resolvedGrade, owned_weapons)

        writeSave(userData)
        if result == 'updated':
            return f'{weapon} already owned, stats updated to bonus: {resolvedBonus}, augments: {resolvedAugments}, grade: {resolvedGrade}'
        return f'{weapon} added to strongboxes with bonus: {resolvedBonus}, augments: {resolvedAugments}, grade: {resolvedGrade}'

    return setPremWeapon()

@directFunction
def setMasteryLevels():
    userData = loadSave()
    profile = loadConfig()['current_profile']
    log = _setMasteryLevelsLogic(userData, profile)
    writeSave(userData)
    return log

@directFunction
def setAllAmmo(amount: int = None):
    if amount is None:
        amount = promptInt('Enter amount for ALL types of ammo: ', minValue=0)
        
    userData = loadSave()
    if userData is None:
        return "[FAILED] Failed to load save file."
    profile = loadConfig()['current_profile']
    
    log = _setAllAmmoLogic(userData, profile, amount)
    writeSave(userData)
    return log

PREMIUM_WEAPON_IDS = { 184, 185, 186, 187, 188, 189, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 211, 212, 213, 214, 216, 217, 218, 219, 233 }

BUILDS = {
    "Meta Balanced": {
        "Skills": {
            1: [
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "toughness", "SkillLevel": 2},
                {"SkillName": "bodyarmour", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "medkit", "SkillLevel": 25},
                {"SkillName": "revive", "SkillLevel": 1},
                {"SkillName": "finalfarewell", "SkillLevel": 1}
            ],
            2: [
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 21},
                {"SkillName": "criticalshot", "SkillLevel": 7},
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "killingspree", "SkillLevel": 25}
            ],
            3: [
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 21},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "heavygear", "SkillLevel": 1},
                {"SkillName": "toughbody", "SkillLevel": 6},
                {"SkillName": "dieanotherday", "SkillLevel": 1}
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 8, "Augment2LVL": 12,
                "Augment3ID": 6, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12
            }
        ],
        "Equipment": [
            {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 23, "Augment1LVL": 12, "Augment2ID": 24, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Critbrecher Heavy": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "heavygear", "SkillLevel": 23},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 22},
                {"SkillName": "fastreload", "SkillLevel": 12},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10201, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "HS2 - Five Balls Zerfallen": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "heavygear", "SkillLevel": 21},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 21},
                {"SkillName": "fastreload", "SkillLevel": 15},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Concussion Heavy": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "concussion", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
                {"SkillName": "heavygear", "SkillLevel": 1},
                {"SkillName": "toughbody", "SkillLevel": 2},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "CHS2 - Concussion HS2": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "concussion", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 16},
                {"SkillName": "fastreload", "SkillLevel": 15},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
                {"SkillName": "heavygear", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "LMS Hypertank Heavy": {
        "Skills": {
            3: [
                {"SkillName": "toughbody", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 24},
                {"SkillName": "toughness", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 24},
                {"SkillName": "fastreload", "SkillLevel": 2},
                {"SkillName": "holdtheline", "SkillLevel": 1},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
                {"SkillName": "heavygear", "SkillLevel": 1},
                {"SkillName": "concussion", "SkillLevel": 5},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 220, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 219, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 221, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "HS1 – Classic Heavy": {
        "Skills": {
            3: [
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 19},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "toughbody", "SkillLevel": 1},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Crit Tank Heavy": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "toughbody", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 13},
                {"SkillName": "fastmovement", "SkillLevel": 14},
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
                {"SkillName": "concussion", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 15, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Max Damage Critbrecher": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 18},
                {"SkillName": "heavygear", "SkillLevel": 14},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Omega Concussion Heavy": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "concussion", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 18},
                {"SkillName": "fastmovement", "SkillLevel": 13},
                {"SkillName": "heavygear", "SkillLevel": 1},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Critfallen": {
        "Skills": {
            3: [
                {"SkillName": "holdtheline", "SkillLevel": 25},
                {"SkillName": "heavygear", "SkillLevel": 21},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 20},
                {"SkillName": "bodyarmour", "SkillLevel": 12},
                {"SkillName": "fastreload", "SkillLevel": 3},
                {"SkillName": "toughbody", "SkillLevel": 1},
                {"SkillName": "dieanotherday", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Race Modded Crit Assault": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 25},
                {"SkillName": "deadlyforce", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 7},
                {"SkillName": "stimshot", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Saultbrecher": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 25},
                {"SkillName": "deadlyforce", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 12},
                {"SkillName": "criticalshot", "SkillLevel": 10},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "fastmovement", "SkillLevel": 10},
            ]
        },
        "Weapons": [
            {
                "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10201, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Max Damage Assault": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "deadlyforce", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 8},
            ]
        },
        "Weapons": [
            {
                "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Max Speed Assault": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 7},
                {"SkillName": "assaultteam", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10207, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Virus Samples Assault": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 12},
                {"SkillName": "bodyarmour", "SkillLevel": 20},
                {"SkillName": "stimshot", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10177, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10207, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "AS1 – Classic Assault": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 19},
                {"SkillName": "fastreload", "SkillLevel": 4},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 20, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Weapon Enjoyer Assault (Zerfallen 4 Clip, Damage Focused)": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 24},
                {"SkillName": "deadlyforce", "SkillLevel": 9},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 10},
                {"SkillName": "fastmovement", "SkillLevel": 6},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Weapon Enjoyer Assault (Zerfallen 4 Clip, Critical Focused)": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 24},
                {"SkillName": "deadlyforce", "SkillLevel": 9},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 10},
                {"SkillName": "fastmovement", "SkillLevel": 6},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Weapon Enjoyer Assault (Damage Focused)": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 24},
                {"SkillName": "deadlyforce", "SkillLevel": 9},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 10},
                {"SkillName": "fastmovement", "SkillLevel": 6},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Weapon Enjoyer Assault (Critical Focused)": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 24},
                {"SkillName": "deadlyforce", "SkillLevel": 9},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 10},
                {"SkillName": "fastmovement", "SkillLevel": 6},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Weapon Enjoyer Assault (Movement Speed and DPS Focused)": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 24},
                {"SkillName": "deadlyforce", "SkillLevel": 9},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 10},
                {"SkillName": "fastmovement", "SkillLevel": 6},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10207, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Weapon Enjoyer Assault (Zerfallen 5 Clipsize)": {
        "Skills": {
            2: [
                {"SkillName": "adrenaline", "SkillLevel": 25},
                {"SkillName": "killingspree", "SkillLevel": 24},
                {"SkillName": "deadlyforce", "SkillLevel": 9},
                {"SkillName": "stimshot", "SkillLevel": 1},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 10},
                {"SkillName": "fastmovement", "SkillLevel": 6},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Hospital Medic": {
        "Skills": {
            1: [
                {"SkillName": "revive", "SkillLevel": 25},
                {"SkillName": "finalfarewell", "SkillLevel": 25},
                {"SkillName": "recoverytime", "SkillLevel": 25},
                {"SkillName": "medkit", "SkillLevel": 22},
                {"SkillName": "fastreload", "SkillLevel": 3},
            ]
        },
        "Weapons": [
            {
                "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
            },
            {
                "ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 4, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
            {"ID": 137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 20, "Augment1LVL": 12, "Augment2ID": 16, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Terminals Medic": {
        "Skills": {
            1: [
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "medkit", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 20},
                {"SkillName": "energyregen", "SkillLevel": 12},
                {"SkillName": "finalfarewell", "SkillLevel": 1},
            ]
        },
        "Weapons": [
            {
                "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 9, "Augment4LVL": 12,
            },
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 9, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
            {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Tank Medic for LMS": {
        "Skills": {
            1: [
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "toughness", "SkillLevel": 25},
                {"SkillName": "medkit", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 21},
                {"SkillName": "energyregen", "SkillLevel": 12},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
            },
            {
                "ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 2, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 217, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
            {"ID": 218, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 220, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Hypertank Medic for LMS": {
        "Skills": {
            1: [
                {"SkillName": "medkit", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "toughness", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 24},
                {"SkillName": "fastreload", "SkillLevel": 2},
                {"SkillName": "energyregen", "SkillLevel": 7},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 220, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 219, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 221, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "MS2 – Blue Assault": {
        "Skills": {
            1: [
                {"SkillName": "medkit", "SkillLevel": 4},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 21},
                {"SkillName": "bodyarmour", "SkillLevel": 25},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "MS2+ – Race Modded MS2": {
        "Skills": {
            1: [
                {"SkillName": "medkit", "SkillLevel": 25},
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "bodyarmour", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
            ]
        },
        "Weapons": [
            {
                "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 9, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 14, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
            {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
            {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
        ],
    },
    "Hexafecta Medic": {
        "Skills": {
            1: [
                {"SkillName": "fastmovement", "SkillLevel": 25},
                {"SkillName": "criticalshot", "SkillLevel": 25},
                {"SkillName": "zombieantidote", "SkillLevel": 25},
                {"SkillName": "fastreload", "SkillLevel": 12},
                {"SkillName": "medkit", "SkillLevel": 13},
            ]
        },
        "Weapons": [
            {
                "ID": 149, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3,
                "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 0, "Augment4LVL": 0,
            },
            {
                "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
                "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
                "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
                "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
            },
        ],
        "Equipment": [
            {"ID": 130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 2, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
            {"ID": 137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 2, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 18, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
            {"ID": 135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 2, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
            {"ID": 171, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 2, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
            {"ID": 167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 2, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
        ],
    },
    "Antiboost Medic": {
        "Skills": {
            1: [
                {"SkillName": "medkit", "SkillLevel": 1},
                {"SkillName": "revive", "SkillLevel": 21},
                {"SkillName": "finalfarewell", "SkillLevel": 1},
            ]
        },
        "Weapons": [],
        "Equipment": [],
    },
}

@nestedMenuOptions  
def characterBuild(buildName: str = '__menu_options__'):
    userData = loadSave()
    if userData is None:
        return {} if buildName == '__menu_options__' else "[FAILED] Failed to load save file."
    
    profile = loadConfig()['current_profile']
    
    if buildName == '__menu_options__':
        current_class = userData['Inventory'][profile].get('Skills', {}).get('Class')
        return {
            name: characterBuild
            for name, data in BUILDS.items()
            if "Skills" in data and current_class in data["Skills"]
        }

    log = _characterBuildLogic(userData, profile, BUILDS, buildName)
    writeSave(userData)
    return log

def _update_or_add_weapon(inventory: dict, preset_weapon: dict, next_index: int) -> int:
    """
    Jika ID termasuk senjata premium dan sudah ada di inventori:
        -> Update slot augment, bonus stats, grade, dan equipped slot tanpa duplikasi.
    Jika bukan premium atau belum dimiliki:
        -> Tambahkan item baru ke inventori dan increment next_index.
    """
    weapon_id = preset_weapon.get('ID')
    owned_weapons = inventory['Weapons']
    is_premium = weapon_id in PREMIUM_WEAPON_IDS

    target_weapon = None
    if is_premium:
        target_weapon = next((w for w in owned_weapons if w.get('ID') == weapon_id), None)

    if target_weapon is not None:
        # Update atribut augment dan level senjata yang sudah ada
        target_weapon['EquippedSlot'] = preset_weapon.get('EquippedSlot', -1)
        target_weapon['Grade'] = preset_weapon.get('Grade', target_weapon.get('Grade', 12))
        target_weapon['BonusStatsLevel'] = preset_weapon.get('BonusStatsLevel', target_weapon.get('BonusStatsLevel', 10))
        target_weapon['AugmentSlots'] = preset_weapon.get('AugmentSlots', 4)
        target_weapon['Seen'] = True

        for aug_idx in range(1, 5):
            id_key = f'Augment{aug_idx}ID'
            lvl_key = f'Augment{aug_idx}LVL'
            target_weapon[id_key] = preset_weapon.get(id_key, 0)
            target_weapon[lvl_key] = preset_weapon.get(lvl_key, 0)
        return next_index

    # Jika item baru: clone dict dan beri index berikutnya
    new_weapon = dict(preset_weapon)
    new_weapon['InventoryIndex'] = next_index
    new_weapon['Seen'] = True
    owned_weapons.append(new_weapon)
    return next_index + 1

def _characterBuildLogic(userData, profile, builds, buildName):
    inventory = userData['Inventory'][profile]
    current_class = inventory.get('Skills', {}).get('Class')

    selected_preset = builds.get(buildName)
    if not selected_preset:
        return f"[FAILED] Preset '{buildName}' not found."

    preset_skills_map = selected_preset.get("Skills", {})
    if current_class not in preset_skills_map:
        return f"[FAILED] Preset '{buildName}' does not support your current class."

    # Pastikan list inventori ada
    owned_weapons = inventory.setdefault('Weapons', [])
    owned_equipment = inventory.setdefault('Equipment', [])

    # Lepaskan semua item yang sedang terpasang
    for w in owned_weapons:
        if w.get('EquippedSlot', -1) != -1:
            w['EquippedSlot'] = -1

    for e in owned_equipment:
        if e.get('Equipped', False):
            e['Equipped'] = False

    # Hitung index awal inventori
    next_weapon_index = max([w.get('InventoryIndex', -1) for w in owned_weapons] + [-1]) + 1
    next_armor_index = max([e.get('InventoryIndex', -1) for e in owned_equipment] + [-1]) + 1

    # Proses Senjata (Update augment jika premium sudah ada, tambahkan jika belum)
    for preset_w in selected_preset.get("Weapons", []):
        next_weapon_index = _update_or_add_weapon(inventory, preset_w, next_weapon_index)

    # Proses Armor/Equipment (Selalu extend item baru)
    for i, e in enumerate(selected_preset.get("Equipment", [])):
        new_equip = dict(e)
        new_equip['InventoryIndex'] = next_armor_index + i
        new_equip['Seen'] = True
        new_equip['Equipped'] = True
        owned_equipment.append(new_equip)

    # Konfigurasi Skill & Level Karakter
    skills_section = inventory['Skills']
    skills_section['PlayerLevel'] = 100
    skills_section['PlayerTotalXp'] = 87977897
    skills_section['AvailableSkillPoints'] = 0
    skills_section['SkillsArray'] = preset_skills_map[current_class]

    class_names = {1: "Medic", 2: "Assault", 3: "Heavy"}
    class_status = class_names.get(current_class, f"Class {current_class}")
    return f"Applied '{buildName}' configuration for {class_status} successfully!"

# @nestedMenuOptions  
# def characterBuild(buildName: str = '__menu_options__'):
#     BUILDS = {
#         "Meta Balanced": {
#             "Skills": {
#                 1: [  # --- MEDIC ---
#                     {"SkillName": "fastreload", "SkillLevel": 4},
#                     {"SkillName": "fastmovement", "SkillLevel": 25},
#                     {"SkillName": "toughness", "SkillLevel": 2},
#                     {"SkillName": "bodyarmour", "SkillLevel": 25},
#                     {"SkillName": "criticalshot", "SkillLevel": 25},
#                     {"SkillName": "medkit", "SkillLevel": 25},
#                     {"SkillName": "revive", "SkillLevel": 1},
#                     {"SkillName": "finalfarewell", "SkillLevel": 1}
#                 ],
#                 2: [  # --- ASSAULT ---
#                     {"SkillName": "fastreload", "SkillLevel": 4},
#                     {"SkillName": "fastmovement", "SkillLevel": 25},
#                     {"SkillName": "bodyarmour", "SkillLevel": 21},
#                     {"SkillName": "criticalshot", "SkillLevel": 7},
#                     {"SkillName": "adrenaline", "SkillLevel": 25},
#                     {"SkillName": "stimshot", "SkillLevel": 1},
#                     {"SkillName": "killingspree", "SkillLevel": 25}
#                 ],
#                 3: [  # --- HEAVY ---
#                     {"SkillName": "fastreload", "SkillLevel": 4},
#                     {"SkillName": "fastmovement", "SkillLevel": 25},
#                     {"SkillName": "bodyarmour", "SkillLevel": 21},
#                     {"SkillName": "criticalshot", "SkillLevel": 25},
#                     {"SkillName": "holdtheline", "SkillLevel": 25},
#                     {"SkillName": "heavygear", "SkillLevel": 1},
#                     {"SkillName": "toughbody", "SkillLevel": 6},
#                     {"SkillName": "dieanotherday", "SkillLevel": 1}
#                 ]
#             },
#             "Weapons": [
#                 {
#                     "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                     "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                     "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 8, "Augment2LVL": 12,
#                     "Augment3ID": 6, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12
#                 },
#                 {
#                     "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                     "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                     "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                     "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12
#                 }
#             ],
#             "Equipment": [
#                 {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 23, "Augment1LVL": 12, "Augment2ID": 24, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#                 {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#                 {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#                 {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#                 {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             ],
#         },
#         # ----------------------------------------------------
#         # HEAVY BUILDS
#         # ----------------------------------------------------
#         "Critbrecher Heavy": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "heavygear", "SkillLevel": 23},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 22},
#                 {"SkillName": "fastreload", "SkillLevel": 12},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10201, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "HS2 - Five Balls Zerfallen": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "heavygear", "SkillLevel": 21},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 21},
#                 {"SkillName": "fastreload", "SkillLevel": 15},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Concussion Heavy": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "concussion", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 4},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#                 {"SkillName": "heavygear", "SkillLevel": 1},
#                 {"SkillName": "toughbody", "SkillLevel": 2},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "CHS2 - Concussion HS2": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "concussion", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 16},
#                 {"SkillName": "fastreload", "SkillLevel": 15},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#                 {"SkillName": "heavygear", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "LMS Hypertank Heavy": {
#         "Skills": {
#             3: [
#                 {"SkillName": "toughbody", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 24},
#                 {"SkillName": "toughness", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 24},
#                 {"SkillName": "fastreload", "SkillLevel": 2},
#                 {"SkillName": "holdtheline", "SkillLevel": 1},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#                 {"SkillName": "heavygear", "SkillLevel": 1},
#                 {"SkillName": "concussion", "SkillLevel": 5},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 220, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 219, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 221, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "HS1 – Classic Heavy": {
#         "Skills": {
#             3: [
#                 {"SkillName": "fastreload", "SkillLevel": 4},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 19},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "toughbody", "SkillLevel": 1},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Crit Tank Heavy": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "toughbody", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 13},
#                 {"SkillName": "fastmovement", "SkillLevel": 14},
#                 {"SkillName": "fastreload", "SkillLevel": 4},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#                 {"SkillName": "concussion", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 15, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Max Damage Critbrecher": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 18},
#                 {"SkillName": "heavygear", "SkillLevel": 14},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Omega Concussion Heavy": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "concussion", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 18},
#                 {"SkillName": "fastmovement", "SkillLevel": 13},
#                 {"SkillName": "heavygear", "SkillLevel": 1},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Critfallen": {
#         "Skills": {
#             3: [
#                 {"SkillName": "holdtheline", "SkillLevel": 25},
#                 {"SkillName": "heavygear", "SkillLevel": 21},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 20},
#                 {"SkillName": "bodyarmour", "SkillLevel": 12},
#                 {"SkillName": "fastreload", "SkillLevel": 3},
#                 {"SkillName": "toughbody", "SkillLevel": 1},
#                 {"SkillName": "dieanotherday", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },

#     # ----------------------------------------------------
#     # ASSAULT BUILDS
#     # ----------------------------------------------------
#     "Race Modded Crit Assault": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 25},
#                 {"SkillName": "deadlyforce", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 7},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Saultbrecher": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 25},
#                 {"SkillName": "deadlyforce", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 12},
#                 {"SkillName": "criticalshot", "SkillLevel": 10},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "fastmovement", "SkillLevel": 10},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10201, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Max Damage Assault": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "deadlyforce", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 8},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Max Speed Assault": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 7},
#                 {"SkillName": "assaultteam", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10207, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Virus Samples Assault": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 12},
#                 {"SkillName": "bodyarmour", "SkillLevel": 20},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10177, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10207, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "AS1 – Classic Assault": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 19},
#                 {"SkillName": "fastreload", "SkillLevel": 4},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 20, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Weapon Enjoyer Assault (Zerfallen 4 Clip, Damage Focused)": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 24},
#                 {"SkillName": "deadlyforce", "SkillLevel": 9},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 10},
#                 {"SkillName": "fastmovement", "SkillLevel": 6},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Weapon Enjoyer Assault (Zerfallen 4 Clip, Critical Focused)": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 24},
#                 {"SkillName": "deadlyforce", "SkillLevel": 9},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 10},
#                 {"SkillName": "fastmovement", "SkillLevel": 6},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Weapon Enjoyer Assault (Damage Focused)": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 24},
#                 {"SkillName": "deadlyforce", "SkillLevel": 9},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 10},
#                 {"SkillName": "fastmovement", "SkillLevel": 6},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Weapon Enjoyer Assault (Critical Focused)": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 24},
#                 {"SkillName": "deadlyforce", "SkillLevel": 9},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 10},
#                 {"SkillName": "fastmovement", "SkillLevel": 6},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Weapon Enjoyer Assault (Movement Speed and DPS Focused)": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 24},
#                 {"SkillName": "deadlyforce", "SkillLevel": 9},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 10},
#                 {"SkillName": "fastmovement", "SkillLevel": 6},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10207, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 225, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Weapon Enjoyer Assault (Zerfallen 5 Clipsize)": {
#         "Skills": {
#             2: [
#                 {"SkillName": "adrenaline", "SkillLevel": 25},
#                 {"SkillName": "killingspree", "SkillLevel": 24},
#                 {"SkillName": "deadlyforce", "SkillLevel": 9},
#                 {"SkillName": "stimshot", "SkillLevel": 1},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 10},
#                 {"SkillName": "fastmovement", "SkillLevel": 6},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 238, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 240, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 239, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },

#     # ----------------------------------------------------
#     # MEDIC BUILDS
#     # ----------------------------------------------------
#     "Hospital Medic": {
#         "Skills": {
#             1: [
#                 {"SkillName": "revive", "SkillLevel": 25},
#                 {"SkillName": "finalfarewell", "SkillLevel": 25},
#                 {"SkillName": "recoverytime", "SkillLevel": 25},
#                 {"SkillName": "medkit", "SkillLevel": 22},
#                 {"SkillName": "fastreload", "SkillLevel": 3},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 5, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 4, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 20, "Augment1LVL": 12, "Augment2ID": 16, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 211, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 241, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Terminals Medic": {
#         "Skills": {
#             1: [
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "medkit", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 20},
#                 {"SkillName": "energyregen", "SkillLevel": 12},
#                 {"SkillName": "finalfarewell", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10068, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 9, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 10, "Augment3LVL": 12, "Augment4ID": 9, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 20, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Tank Medic for LMS": {
#         "Skills": {
#             1: [
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "toughness", "SkillLevel": 25},
#                 {"SkillName": "medkit", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 21},
#                 {"SkillName": "energyregen", "SkillLevel": 12},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 10, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 2, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 11, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 217, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 13, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 218, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 14, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 220, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Hypertank Medic for LMS": {
#         "Skills": {
#             1: [
#                 {"SkillName": "medkit", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "toughness", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 24},
#                 {"SkillName": "fastreload", "SkillLevel": 2},
#                 {"SkillName": "energyregen", "SkillLevel": 7},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 222, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 11, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 10195, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 228, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 220, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 219, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 221, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "MS2 – Blue Assault": {
#         "Skills": {
#             1: [
#                 {"SkillName": "medkit", "SkillLevel": 4},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 21},
#                 {"SkillName": "bodyarmour", "SkillLevel": 25},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 17, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 20, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10199, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 14, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "MS2+ – Race Modded MS2": {
#         "Skills": {
#             1: [
#                 {"SkillName": "medkit", "SkillLevel": 25},
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "bodyarmour", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 10066, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 4,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 9, "Augment3LVL": 12, "Augment4ID": 8, "Augment4LVL": 12,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 9, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 227, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 19, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 3, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 230, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 3, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 14, "Augment1LVL": 12, "Augment2ID": 25, "Augment2LVL": 12, "Augment3ID": 13, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 229, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 3, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 22, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#             {"ID": 10167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 3, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 13, "Augment2LVL": 12, "Augment3ID": 15, "Augment3LVL": 12, "Equipped": True},
#         ],
#     },
#     "Hexafecta Medic": {
#         "Skills": {
#             1: [
#                 {"SkillName": "fastmovement", "SkillLevel": 25},
#                 {"SkillName": "criticalshot", "SkillLevel": 25},
#                 {"SkillName": "zombieantidote", "SkillLevel": 25},
#                 {"SkillName": "fastreload", "SkillLevel": 12},
#                 {"SkillName": "medkit", "SkillLevel": 13},
#             ]
#         },
#         "Weapons": [
#             {
#                 "ID": 149, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 3,
#                 "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 3, "Augment3LVL": 12, "Augment4ID": 0, "Augment4LVL": 0,
#             },
#             {
#                 "ID": 10081, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 4,
#                 "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10,
#                 "Augment1ID": 1, "Augment1LVL": 12, "Augment2ID": 6, "Augment2LVL": 12,
#                 "Augment3ID": 5, "Augment3LVL": 12, "Augment4ID": 3, "Augment4LVL": 12,
#             },
#         ],
#         "Equipment": [
#             {"ID": 130, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 1, "AugmentSlots": 2, "InventoryIndex": 0, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 24, "Augment1LVL": 12, "Augment2ID": 23, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
#             {"ID": 137, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 2, "AugmentSlots": 2, "InventoryIndex": 1, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 17, "Augment1LVL": 12, "Augment2ID": 18, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
#             {"ID": 135, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 3, "AugmentSlots": 2, "InventoryIndex": 2, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 25, "Augment1LVL": 12, "Augment2ID": 15, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
#             {"ID": 171, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 4, "AugmentSlots": 2, "InventoryIndex": 3, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 17, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
#             {"ID": 167, "EquipVersion": 0, "Grade": 12, "EquippedSlot": 5, "AugmentSlots": 2, "InventoryIndex": 4, "Seen": True, "BonusStatsLevel": 10, "Augment1ID": 22, "Augment1LVL": 12, "Augment2ID": 19, "Augment2LVL": 12, "Augment3ID": 0, "Augment3LVL": 0, "Equipped": True},
#         ],
#     },
#     "Antiboost Medic": {
#         "Skills": {
#             1: [
#                 {"SkillName": "medkit", "SkillLevel": 1},
#                 {"SkillName": "revive", "SkillLevel": 21},
#                 {"SkillName": "finalfarewell", "SkillLevel": 1},
#             ]
#         },
#         "Weapons": [],
#         "Equipment": [],
#     },
#     }

#     userData = loadSave()
#     if userData is None:
#         return {} if buildName == '__menu_options__' else "[FAILED] Failed to load save file."
#     profile = loadConfig()['current_profile']
    
#     if buildName == '__menu_options__':
#         inventory = userData['Inventory'][profile]
#         current_class = inventory['Skills'].get('Class')
#         valid_options = {}
#         for name, data in BUILDS.items():
#             if "Skills" in data and current_class in data["Skills"]:
#                 valid_options[name] = characterBuild
#         return valid_options

#     log = _characterBuildLogic(userData, profile, BUILDS, buildName)
#     writeSave(userData)
#     return log

CLASS_MAP = {
    'Medic': 1,
    'Assault': 2,
    'Heavy': 3,
}

@menuOptions
def setCurrentProfileClass(className: str = '__menu_options__'):
    if className == '__menu_options__':
        return list(CLASS_MAP.keys())
    
    userData = loadSave()
    if userData is None:
        return "[FAILED] Failed to load save file."
    profile = loadConfig()['current_profile']
    
    log = _setCurrentProfileClassLogic(userData, profile, className)
    writeSave(userData)
    return log

def _setCurrentProfileClassLogic(userData, profile, className):
    class_id = CLASS_MAP.get(className)
    if class_id is not None:
        skills = userData['Inventory'][profile]['Skills']
        skills['Class'] = class_id
        skills['SkillsArray'] = []
        return f'Class set to {className}'
    return "Class not found."

# ==========================================
# 4. CUSTOM STATS (MAIN OPTIMIZATION)
# ==========================================

@directFunction
def setCurrentProfileStats():
    amount = 2 ** 31 - 2 ** 20
    logs = []
    userData = loadSave()
    if userData is None:
        return "[FAILED] Failed to load save file."
    profile = loadConfig()['current_profile']

    logs.append(_setNightmareTicketsLogic(userData, amount))
    logs.append(_setTokensLogic(userData, amount))
    logs.append(_setCreditsLogic(userData, 'ALL', amount))
    logs.append(_removeAdsLogic(userData, True))
    logs.append(_unlockWeaponCollectionLogic(userData, items, 'ALL'))
    logs.append(_unlockArmorCollectionLogic(userData, items, 'ALL'))
    logs.append(_toggleCollectionRewardsLogic(userData, 'Weapons', 'Toggle All', False))
    logs.append(_toggleCollectionRewardsLogic(userData, 'Armor', 'Toggle All', False))


    logs.append(_setLevelLogic(userData, profile, 100))
    logs.append(_setMoneyLogic(userData, profile, amount))
    logs.append(_setBlackKeysLogic(userData, profile, amount))
    logs.append(_setAugCoresLogic(userData, profile, amount))
    logs.append(_setRandBlackStrongboxLogic(userData, profile, amount))
    logs.append(_activateSkillResetLogic(userData, profile, False))
    logs.append(_setMasteryLevelsLogic(userData, profile))
    logs.append(_setGrenadesLogic(userData, profile, 'ALL', amount))
    
    turretItems = loadItems()['turret']
    logs.append(_setTurretsLogic(userData, profile, turretItems, 'ALL', amount))
    
    logs.append(_setAllAmmoLogic(userData, profile, amount))
    
    items = loadItems()
    logs.append(_setPremiumWeaponsLogic(userData, profile, items['premium'], 'ALL', 10, 4, 12))

    writeSave(userData)

    report_body = "\n".join(logs)
    return f"\n{report_body}"

@directFunction
def setAllProfileStats():
    amount = 2 ** 31 - 2 ** 20
    logs = []

    # 2. BACA FILE 1 KALI SAJA
    userData = loadSave()
    if userData is None:
        return "[FAILED] Failed to load save file."
    # Ambil semua profil yang aktif/Loaded langsung dari memori
    profiles = [
        key for key, val in userData['Inventory'].items() 
        if isinstance(val, dict) and val.get('Loaded')
    ]

    if not profiles:
        return "[FAILED] No active profiles found in save data."

    # 1. JALANKAN FUNGSI EKSTERNAL (Berlaku untuk level Global/Akun, bukan spesifik profil)
    logs.append(_setNightmareTicketsLogic(userData, amount))
    logs.append(_setTokensLogic(userData, amount))
    logs.append(_setCreditsLogic(userData, 'ALL', amount))
    logs.append(_removeAdsLogic(userData, True))
    logs.append(_unlockWeaponCollectionLogic(userData, items, 'ALL'))
    logs.append(_unlockArmorCollectionLogic(userData, items, 'ALL'))
    logs.append(_toggleCollectionRewardsLogic(userData, 'Weapons', 'Toggle All', False))
    logs.append(_toggleCollectionRewardsLogic(userData, 'Armor', 'Toggle All', False))
    
    # Load file eksternal (items) 1 kali saja di luar loop untuk menghemat memori
    turretItems = loadItems()['turret']
    items = loadItems()

    # 3. LOOP KE SEMUA PROFILE DI MEMORI (Sangat ringan karena murni manipulasi dictionary)
    for profile in profiles:
        logs.append(f"\n--- [ Applying Custom Stats to Profile: {profile} ] ---")
        logs.append(_setLevelLogic(userData, profile, 100))
        logs.append(_setMoneyLogic(userData, profile, amount))
        logs.append(_setBlackKeysLogic(userData, profile, amount))
        logs.append(_setAugCoresLogic(userData, profile, amount))
        logs.append(_setRandBlackStrongboxLogic(userData, profile, amount))
        logs.append(_activateSkillResetLogic(userData, profile, False))
        logs.append(_setMasteryLevelsLogic(userData, profile))
        logs.append(_setGrenadesLogic(userData, profile, 'ALL', amount))
        logs.append(_setTurretsLogic(userData, profile, turretItems, 'ALL', amount))
        logs.append(_setAllAmmoLogic(userData, profile, amount))
        logs.append(_setPremiumWeaponsLogic(userData, profile, items['premium'], 'ALL', 10, 4, 12))

    # 4. TULIS FILE 1 KALI SAJA DI AKHIR UNTUK SELURUH PROFIL
    writeSave(userData)

    report_body = "\n".join(logs)
    return f"\n{report_body}"

# ==========================================
# 5. MENU CONFIGURATION
# ==========================================

PROFILE = {
    'Set items': {
        'Set weapons': {
            'Set standard weapons': setStdWeapons,
            'Set premium weapons': setPremiumWeapons
        },
        'Set armour': setArmour,
        'Set turrets': setTurrets,
        'Set grenades': setGrenades,
        'Set ammo' : setAllAmmo,
    },
    'Set money': setMoney,
    'Set level': setLevel,
    'Set black keys': setBlackKeys,
    'Set augment cores': setAugCores,
    'Set black strongbox': setRandBlackStrongbox,
    'Activate free skill reset': activateSkillReset,
    'Set mastery to max level': setMasteryLevels,
    'Change name': changeUsername,
    'Delete a profile': deleteProfile,
    'Character Presets': characterBuild,
    'Set Custom Stats': {
        'Current Profile': setCurrentProfileStats,
        'All Profiles' : setAllProfileStats,
    },
    'Set Class': setCurrentProfileClass,
}