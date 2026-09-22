import json

import requests
from classes import secret

def getOPVaults(fqdn,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    vaultsurl = site + '/v1/vaults'
    vaults = requests.get(vaultsurl,headers=header,verify=True)
    return vaults.json()
    
def getOPSecrets(fqdn,vaultid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secretsurl = site + '/v1/vaults/' + vaultid + '/items'
    secrets = requests.get(secretsurl,headers=header,verify=True)
    return secrets.json()

def getOPSecret(fqdn,vaultid,secretid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secreturl = site + '/v1/vaults/' + vaultid + '/items/' + secretid
    secret = requests.get(secreturl,headers=header,verify=True)
    return secret.json()

def createUpdateOPSecret(fqdn,vaultid,key,secret):
    secretMap = mapExistingSecrets(fqdn,vaultid,key)
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    body = secret.toJson()
    site = 'https://'+fqdn
    if str(secret.clavisId) in secretMap:
        secretid = secretMap[str(secret.clavisId)]
        secreturl = site + '/v1/vaults/' + vaultid + '/items/' + secretid
        result = requests.put(secreturl,headers=header,json=body,verify=True)
        return result
    else:   
        secreturl = site + '/v1/vaults/' + vaultid + '/items'
        result = requests.post(secreturl,headers=header,json=body,verify=True)
    return result

def mapExistingSecrets(fqdn,vaultid,key):
    existingSecrets = getOPSecrets(fqdn,vaultid,key)
    secretMap = {}
    for secret in existingSecrets:
        secretDetail = getOPSecret(fqdn,vaultid,secret['id'],key)
        if 'sections' in secretDetail:
            for section in secretDetail['sections']:
                if section['id'] == 'clavisId':
                    clavisId = section['label']
                    secretMap[clavisId] = secretDetail['id'] 
    return secretMap