from lib.utilities import loadSave, writeSave, promptInt, directFunction, menuOptions, loadItems, nestedMenuOptions, dataclass
from typing import Union, List

@dataclass
class F:
    RESET: str = '\u001B[0m'
    RED: str = '\u001B[31m'
    GREEN: str = '\u001B[32m'
    YELLOW: str = '\u001B[33m'
    CYAN: str = '\u001B[36m'
    WHITE: str = '\u001B[37m'

# ==========================================
# 1. LOGIC FUNCTIONS (Memory only, without I/O)
# ==========================================

def _changeGuildLogic(userData, guild):
    GUILDS = ["GUARDIANS", "NOMADS", "OUTLAWS", "SPARTANS", "CENTURIONS", "CORSAIRS", "RANGERS", "VANGUARD"]
    if guild not in GUILDS:
        return f"Invalid guild: {guild}"
    userData['CurrentFactionWarFaction'] = guild
    return f"Changed guild to {guild}"

def _setCreditsLogic(userData, planet, amount):
    PLANETS = [('ZETA', 0), ('EPSILON', 1), ('SIGMA', 2), ('XI', 3), ('OMICRON', 4)]
    if planet == "FACTION WAR":
        userData['FactionWarCredits'] = amount
        return f"Set FactionWarCredits to {amount}"
    
    if planet == "ALL":
        userData['FactionWarCredits'] = amount
        for p in userData['FactionWarPlanetArray']:
            p['Currency'] = amount
        return f"Set credits for all planets to {amount}"
        
    planet_name, planet_index = next(((p[0], p[1]) for p in PLANETS if p[0] == planet), (None, None))
    if planet_index is not None:
        userData['FactionWarPlanetArray'][planet_index]['Currency'] = amount
        return f"Set credits for {planet_name} to {amount}"
    return f"Invalid planet: {planet}"

def _unlockProfilesLogic(userData, profile):
    PROFILES = [('IAP Character slot 1', 'SAS4_CharacterSlot1'), ('IAP Character slot 2', 'SAS4_CharacterSlot2')]
    optionName, identifier = next(((p[0], p[1]) for p in PROFILES if p[0] == profile), (None, None))
    if identifier:
        for i in userData['PurchasedIAP']['PurchasedIAPArray']:
            if i['Identifier'] == identifier:
                i['Value'] = not (i['Value'])
                return f"Profile: {optionName} was {'activated' if i['Value'] else 'deactivated'}"
    return "Profile not found."

def _unlockFairgroundLogic(userData):
    activated = False
    for i in userData['PurchasedIAP']['PurchasedIAPArray']:
        if i['Identifier'] == 'sas4_fairgroundpack':
            i['Value'] = not (i['Value'])
            activated = i['Value']
        if i['Identifier'] == 'sas4_fairgroundpacksale':
            i['Value'] = not (i['Value'])
    return f"{'Activated fairground pack' if activated else 'Deactivated fairground pack'}"

def _setTokensLogic(userData, amount):
    userData['Global']['ReviveTokens'] = amount
    return f"Set revive tokens to {amount}"

def _removeAdsLogic(userData, boolean):
    userData['Global']['ForceRemoveAds'] = not userData['Global']['ForceRemoveAds'] if boolean is None else boolean
    return f"{'Removed ads' if userData['Global']['ForceRemoveAds'] else 'Ads have been turned on'}"

def _setNightmareTicketsLogic(userData, amount):
    userData['Global']['AvailablePremiumTickets'] = amount
    return f"Set nightmare tickets to {amount}"

def _unlockWeaponCollectionLogic(userData, items, weaponType, version=None, weapon=None):
    if weaponType == 'ALL': 
        for category in items['weapons'].keys():
            for v in items['weapons'][category].keys():
                for w in items['weapons'][category][v]:
                    weaponID = w['ID']
                    for x in userData['CollectionArrayWeapon']:
                        if x['CollectionId'] == weaponID:
                            x['CollectionUnlocked'] = True
        return 'All weapons have been unlocked in the collection.'
        
    if weapon and version:
        WEAPONS = items['weapons'][weaponType.lower().replace(' ', '_')][version.lower()]
        selectedWeapon = next((w for w in WEAPONS if w['Name'] == weapon), None)
        if selectedWeapon:
            weaponID = selectedWeapon['ID']
            for x in userData['CollectionArrayWeapon']:
                if x['CollectionId'] == weaponID:
                    x['CollectionUnlocked'] = not x['CollectionUnlocked']
                    return f"{weapon} ({version}) has been {'unlocked' if x['CollectionUnlocked'] else 'locked'} in the collection."
        return f'Could not find {weapon} ({version}) in the collection.'

def _unlockArmorCollectionLogic(userData, items, armorType, version=None, armor=None):
    if armorType == 'ALL': 
        for category in items['armour'].keys():
            for v in items['armour'][category].keys():
                for a in items['armour'][category][v]:
                    armorID = a['ID']
                    for x in userData['CollectionArrayArmour']:
                        if x['CollectionId'] == armorID:
                            x['CollectionUnlocked'] = True
        return 'All armor has been unlocked in the collection.' 

    if armor and version:
        ARMORS = items['armour'][armorType.lower().replace(' ', '_')][version.lower()]
        selectedArmor = next((a for a in ARMORS if a['Name'] == armor), None)
        if selectedArmor:
            armorID = selectedArmor['ID']
            for x in userData['CollectionArrayArmour']:
                if x['CollectionId'] == armorID:
                    x['CollectionUnlocked'] = not x['CollectionUnlocked']
                    return f"{armor} ({version}) has been {'unlocked' if x['CollectionUnlocked'] else 'locked'} in the collection."
        return f'Could not find {armor} ({version}) in the collection.'

def _toggleCollectionRewardsLogic(userData, category, reward, setValue=None):
    rewards = userData['CollectionRewards']
    weaponRewards = [key for key in rewards.keys() if key.startswith('CollectionRewardWeapon') or 
                      any(w in key for w in ['Pistol', 'SMG', 'Assault', 'Shotgun', 'Sniper', 'Rocket', 'LMG'])]
    armourRewards = [key for key in rewards.keys() if key.startswith('CollectionRewardArmour') or 
                     any(a in key for a in ['Helmet', 'Torso', 'Gloves', 'Pants', 'Boots'])]
    
    target_rewards = weaponRewards if category == 'Weapons' else armourRewards

    if reward == 'Toggle All':
        if setValue is not None:
            new_value = setValue
        else:
            new_value = not all(rewards[key] for key in target_rewards)
        for key in target_rewards:
            rewards[key] = new_value
        return f"All {category} rewards set to {new_value}"
            
    rewards[reward] = not rewards[reward]
    return f"{reward} set to {rewards[reward]}"

# ==========================================
# 2. WRAPPER FUNCTIONS (Pending Disk I/O)
# ==========================================

@menuOptions
def changeGuild(guild: str = "__menu_options__") -> Union[str, List[str]]:
    GUILDS = ["GUARDIANS", "NOMADS", "OUTLAWS", "SPARTANS", "CENTURIONS", "CORSAIRS", "RANGERS", "VANGUARD"]
    
    if guild == "__menu_options__":
        return GUILDS
    
    userData = loadSave()
    log = _changeGuildLogic(userData, guild)
    writeSave(userData)
    return log

@menuOptions
def setCredits(planet: str = "__menu_options__", amount: int = None) -> Union[str, List[str]]:
    PLANETS = [('ZETA', 0), ('EPSILON', 1), ('SIGMA', 2), ('XI', 3), ('OMICRON', 4)]

    if planet == "__menu_options__":
        return [f"{p[0]}" for p in PLANETS] + ["ALL", "FACTION WAR"]
    
    if amount is None:
        if planet == "FACTION WAR":
            amount = promptInt("Enter the amount of FactionWarCredits: ")
        elif planet == "ALL":
            amount = promptInt("Enter the amount of credits for all planets and faction credit: ")
        else:
            amount = promptInt(f"Enter the amount of credits for {planet}: ")

    userData = loadSave()
    log = _setCreditsLogic(userData, planet, amount)
    writeSave(userData)
    return log

@menuOptions
def unlockProfiles(profile: str = '__menu_options__'):
    PROFILES = [('IAP Character slot 1', 'SAS4_CharacterSlot1'), ('IAP Character slot 2', 'SAS4_CharacterSlot2')]

    if profile == '__menu_options__':
        return [f"{p[0]}" for p in PROFILES]
    
    userData = loadSave()
    log = _unlockProfilesLogic(userData, profile)
    writeSave(userData)
    return log

@directFunction
def unlockFairground():
    userData = loadSave()
    log = _unlockFairgroundLogic(userData)
    writeSave(userData)
    return log

@directFunction
def setTokens(amount: int = None):
    if amount is None:
        amount = promptInt('Set revive token amount: ', minValue=0)
        
    userData = loadSave()
    log = _setTokensLogic(userData, amount)
    writeSave(userData)
    return log

@directFunction
def removeAds(boolean: bool = None):
    userData = loadSave()
    log = _removeAdsLogic(userData, boolean)
    writeSave(userData)
    return log

@directFunction
def setNightmareTickets(amount: int = None):
    if amount is None:
        amount = promptInt('Set nightmare tickets amount: ', minValue=0)
        
    userData = loadSave()
    log = _setNightmareTicketsLogic(userData, amount)
    writeSave(userData)
    return log

@nestedMenuOptions
def unlockWeaponCollection(weaponType: str = '__menu_options__'):
    items = loadItems()
    
    if weaponType == '__menu_options__':
        options = {w.capitalize().replace('_', ' '): unlockWeaponCollection for w in items['weapons'].keys()}
        options['ALL'] = unlockWeaponCollection
        return options
    
    if weaponType == 'ALL': 
        userData = loadSave()
        log = _unlockWeaponCollectionLogic(userData, items, 'ALL')
        writeSave(userData)
        return log
    
    def setWeaponVersion(version: str = '__menu_options__'):
        if version == '__menu_options__':
            return {v.capitalize(): setWeaponVersion for v in items['weapons'][weaponType.lower().replace(' ', '_')].keys()}
        
        WEAPONS = items['weapons'][weaponType.lower().replace(' ', '_')][version.lower()]
        
        def unlockWeapon(weapon: str = '__menu_options__'):
            if weapon == '__menu_options__':
                return {w['Name']: unlockWeapon for w in WEAPONS}
            
            userData = loadSave()
            log = _unlockWeaponCollectionLogic(userData, items, weaponType, version, weapon)
            writeSave(userData)
            return log
            
        return unlockWeapon()
    
    return setWeaponVersion()


@nestedMenuOptions
def unlockArmorCollection(armorType: str = '__menu_options__'):
    items = loadItems()
    
    if armorType == '__menu_options__':
        options = {a.capitalize().replace('_', ' '): unlockArmorCollection for a in items['armour'].keys()}
        options['ALL'] = unlockArmorCollection
        return options
    
    if armorType == 'ALL': 
        userData = loadSave()
        log = _unlockArmorCollectionLogic(userData, items, 'ALL')
        writeSave(userData)
        return log

    def setArmorVersion(version: str = '__menu_options__'):
        if version == '__menu_options__':
            return {v.capitalize(): setArmorVersion for v in items['armour'][armorType.lower().replace(' ', '_')].keys()}
        
        ARMORS = items['armour'][armorType.lower().replace(' ', '_')][version.lower()]
        
        def unlockArmor(armor: str = '__menu_options__'):
            if armor == '__menu_options__':
                return {a['Name']: unlockArmor for a in ARMORS}
            
            userData = loadSave()
            log = _unlockArmorCollectionLogic(userData, items, armorType, version, armor)
            writeSave(userData)
            return log
            
        return unlockArmor()
    
    return setArmorVersion()

@nestedMenuOptions
def toggleCollectionRewards(category: str = '__menu_options__'):
    if category == '__menu_options__':
        return {
            'Weapons': toggleCollectionRewards,
            'Armor': toggleCollectionRewards
        }

    def toggleReward(reward: str = '__menu_options__', setValue: bool = None):
        if reward == '__menu_options__':
            userData = loadSave()
            rewards = userData['CollectionRewards']
            weaponRewards = [key for key in rewards.keys() if key.startswith('CollectionRewardWeapon') or 
                              any(weapon in key for weapon in ['Pistol', 'SMG', 'Assault', 'Shotgun', 'Sniper', 'Rocket', 'LMG'])]
            armourRewards = [key for key in rewards.keys() if key.startswith('CollectionRewardArmour') or 
                             any(armor in key for armor in ['Helmet', 'Torso', 'Gloves', 'Pants', 'Boots'])]
            return {key: toggleReward for key in rewards.keys() if key in (weaponRewards if category == 'Weapons' else armourRewards)}
        
        userData = loadSave()
        log = _toggleCollectionRewardsLogic(userData, category, reward, setValue)
        writeSave(userData)
        return log

    options = toggleReward()
    options['Toggle All'] = toggleReward
    return options


ACCOUNT = {
    'Factions': {
        'Set credits': setCredits,
        'Change guild': changeGuild
    },
    'IAP Settings': {
        'Unlock profiles': unlockProfiles,
        'Unlock fairground pack': unlockFairground
    },
    'Remove ads (Mobile only)': removeAds,
    'Revive tokens': setTokens,
    'Nightmare tickets': setNightmareTickets,
    'Unlock collections': {
        'Weapon collection': unlockWeaponCollection,
        'Armour collection': unlockArmorCollection
    },
    'Toggle rewards': toggleCollectionRewards
}