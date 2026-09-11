import requests

def getClavisSecrets(fqdn,key,folderid=None, take=1000,skip=0):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secretsurl = site + '/api/v2/secrets'+ '?take=' + str(take) + '&skip=' + str(skip)
    if folderid:
        secretsurl += '&filter.folderId=' + str(folderid)
    secrets = requests.get(secretsurl,headers=header,verify=True)
    if secrets.status_code != 200:
        return None
    return secrets.json()

def getClavisSecret(fqdn,secretid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secreturl = site + '/api/v2/secrets/' + str(secretid)
    secret = requests.get(secreturl,headers=header,verify=True)
    if secret.status_code != 200:
        return None
    return secret.json()

def getClavisFolders(fqdn,key,id=None, take=1000, skip=0):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    if id == None:
        foldersurl = site + '/api/v1/folders' + '?take=' + str(take) + '&skip=' + str(skip)
    else:
        foldersurl = site + '/api/v1/folders/' + str(id) 
    folders = requests.get(foldersurl,headers=header,verify=True)
    if folders.status_code != 200:
        return None
    return folders.json()

def getClavisFolderTreeMembers(fqdn,folderid,key):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    foldersurl = site + '/api/v1/folders/' + str(folderid)
    folders = requests.get(foldersurl,headers=header,verify=True)
    folders = folders.json()
    for folder in folders['records']:
        if len(folder['childFolders']) > 0:
            getClavisFolderTreeMembers(fqdn,folder['id'],key)
        else:
            print(folder['folderPath'])

def getClavisFolderRootFolderId(fqdn,folderid,key):
    rootfolderid = folderid
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    foldersurl = site + '/api/v1/folders/' + str(folderid)
    folderresult = requests.get(foldersurl,headers=header,verify=True)
    if folderresult.status_code != 200:
        return None
    folder = folderresult.json()    
    if folder['parentFolderId'] == -1:
        return folder['id']
    else:
        rootfolderid = getClavisFolderRootFolderId(fqdn,folder['parentFolderId'],key)
    return rootfolderid
    