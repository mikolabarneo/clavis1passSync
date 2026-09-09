import requests

def getClavisSecrets(fqdn,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secretsurl = site + '/api/v2/secrets'
    secrets = requests.get(secretsurl,headers=header,verify=True)
    return secrets.json()

def getClavisSecret(fqdn,secretid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secreturl = site + '/api/v2/secrets/' + str(secretid)
    secret = requests.get(secreturl,headers=header,verify=True)
    return secret.json()

def getClavisFolders(fqdn,id,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    foldersurl = site + '/api/v1/folders/' + str(id)
    folders = requests.get(foldersurl,headers=header,verify=True)
    return folders.json()