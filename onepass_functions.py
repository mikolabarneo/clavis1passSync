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

def createOPSecret(fqdn,vaultid,key,secret):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    body = secret.toJson()
    site = 'https://'+fqdn
    secreturl = site + '/v1/vaults/' + vaultid + '/items'
    print(json.dumps(body, indent=4))
    result = requests.post(secreturl,headers=header,json=body,verify=True)
    return result