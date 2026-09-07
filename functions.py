import requests

def getVaults(fqdn,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    vaultsurl = site + '/v1/vaults'
    vaults = requests.get(vaultsurl,headers=header,verify=False)
    return vaults.json()
    
def getSecrets(fqdn,vaultid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secretsurl = site + '/v1/vaults/' + vaultid + '/items'
    volumes = requests.get(secretsurl,headers=header,verify=False)
    return volumes.json()

def getSecret(fqdn,vaultid,secretid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secreturl = site + '/v1/vaults/' + vaultid + '/items/' + secretid
    secret = requests.get(secreturl,headers=header,verify=False)
    return secret.json()