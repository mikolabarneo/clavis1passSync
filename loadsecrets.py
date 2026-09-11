import os
from onepass_functions import getOPSecret, getOPSecrets, getOPVaults
from clavis_functions import getClavisFolders, getClavisSecrets, getClavisSecret, getClavisFolderTreeMembers, getClavisFolderRootFolderId
import classes

def main():
    onePassSecrets = []
    clavisSecrets = []
    clavisFolders = []
    onePassFQDN = os.environ.get('OPFQDN')
    onePassKey = os.environ.get('OPKEY')
    clavisFQDN = os.environ.get('CLAVISFQDN')
    clavisKey = os.environ.get('CLAVISKEY')
    clavisStartFolder = os.environ.get('CLAVISSTARTFOLDERID')
    #print(getClavisFolderRootFolderId(clavisFQDN, clavisStartFolder, clavisKey))
    #getClavisFolderTreeMembers(clavisFQDN, clavisStartFolder, clavisKey)
    clavisSecretList = getClavisSecrets(clavisFQDN, clavisKey)    
    for secret in clavisSecretList['records']:  
        secretdetails = getClavisSecret(clavisFQDN, secret['id'], clavisKey)                
        secretfolder = getClavisFolders(clavisFQDN, secret['folderId'], clavisKey)
        newfolder = True
        clavisSecret = classes.secret()
        for clavisFolder in clavisFolders:
            if clavisFolder.id == secretfolder['id']:
                clavisSecret.folder = clavisFolder
                newfolder = False
        if newfolder:
            clavisFolder = classes.folder()
            clavisFolder.id = secretfolder['id']
            clavisFolder.folderName = secretfolder['folderName']
            clavisFolder.parentFolderId = secretfolder['parentFolderId']
            clavisFolder.folderPath = secretfolder['folderPath']
            clavisFolders.append(clavisFolder)
            print('New folder added: ' + clavisFolder.folderPath)
        clavisSecret.folder = clavisFolder
        clavisSecret.clavisId = secretdetails['id']
        clavisSecret.title = secretdetails['name']
        clavisSecret.buildTags()
        clavisSecrets.append(clavisSecret)
    print(clavisFolders)
    vaults = getOPVaults(onePassFQDN, onePassKey)
    for vault in vaults:
        vaultsecrets = getOPSecrets(onePassFQDN, vault['id'], onePassKey)
        for secret in vaultsecrets:
            fullsecret = getOPSecret(onePassFQDN, vault['id'], secret['id'], onePassKey)
            onePassSecrets.append(fullsecret)
    print(onePassSecrets)


if __name__== '__main__':
    main()