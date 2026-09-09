import os
from onepass_functions import getOPSecret, getOPSecrets, getOPVaults
from clavis_functions import getClavisFolders, getClavisSecrets, getClavisSecret
import classes

def main():
    onePassSecrets = []
    clavisSecrets = []
    onePassFQDN = os.environ.get('OPFQDN')
    onePassKey = os.environ.get('OPKEY')
    clavisFQDN = os.environ.get('CLAVISFQDN')
    clavisKey = os.environ.get('CLAVISKEY')
    clavisSecretList = getClavisSecrets(clavisFQDN, clavisKey)    
    for secret in clavisSecretList['records']:        
        secretdetails = getClavisSecret(clavisFQDN, secret['id'], clavisKey)                
        secretfolder = getClavisFolders(clavisFQDN, secret['folderId'], clavisKey)
        clavisSecret = classes.secret()
        clavisFolder = classes.folder()
        clavisFolder.id = secretfolder['id']
        clavisFolder.folderName = secretfolder['folderName']
        clavisFolder.parentFolderId = secretfolder['parentFolderId']
        clavisFolder.folderPath = secretfolder['folderPath']
        clavisSecret.folder = clavisFolder
        clavisSecret.clavisId = secretdetails['id']
        clavisSecret.title = secretdetails['name']
        clavisSecret.buildTags()
        clavisSecrets.append(clavisSecret)
    vaults = getOPVaults(onePassFQDN, onePassKey)
    for vault in vaults:
        vaultsecrets = getOPSecrets(onePassFQDN, vault['id'], onePassKey)
        for secret in vaultsecrets:
            fullsecret = getOPSecret(onePassFQDN, vault['id'], secret['id'], onePassKey)
            onePassSecrets.append(fullsecret)
    print(onePassSecrets)


if __name__== '__main__':
    main()