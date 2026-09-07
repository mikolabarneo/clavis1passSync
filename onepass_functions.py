import requests

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