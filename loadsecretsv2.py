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
    clavisStartFolder = int(os.environ.get('CLAVISSTARTFOLDERID'))
    totalClavisFolders = getClavisFolders(clavisFQDN, clavisKey)
    if totalClavisFolders is None:
        print("Error retrieving Clavis folders. Please check your credentials and try again.")
        return
    for folder in totalClavisFolders['records']:
        f= classes.folder()
        f.id = folder['id']
        f.folderName = folder['folderName']
        f.parentFolderId = folder['parentFolderId']
        f.folderPath = folder['folderPath']
        rootFolderId = getClavisFolderRootFolderId(clavisFQDN, folder['id'], clavisKey)
        if rootFolderId is not None and rootFolderId == clavisStartFolder:
            f.rootFolderId = rootFolderId
            clavisFolders.append(f)
    for folder in clavisFolders:
        clavisSecretList = getClavisSecrets(clavisFQDN, clavisKey, folder.id)    
        for secret in clavisSecretList['records']:  
            secretdetails = getClavisSecret(clavisFQDN, secret['id'], clavisKey)
            if secretdetails is None:
                print(f"Error retrieving secret details for secret ID {secret['id']}. Skipping this secret.")
                continue
            clavisSecret = classes.secret()
            clavisSecret.folder = folder
            clavisSecret.clavisId = secretdetails['id']
            clavisSecret.title = secretdetails['name']
            clavisSecret.buildTags()
            for field in secretdetails['items']:
                if field['slug'] == 'resource':
                    href = field['itemValue']
                    label = field['fieldName']
                    url = {'href': href, 'label': label, 'primary': True}
                    clavisSecret.urls.append(url)
                if field['slug'] == 'hostname':
                    href = field['itemValue']
                    label = field['fieldName']
                    url = {'href': href, 'label': label, 'primary': True}
                    clavisSecret.urls.append(url)
                if field['slug'] == 'notes':
                    secretField = classes.secretField()
                    secretField.type = 'STRING'
                    secretField.id = 'notesPlain'
                    secretField.label = 'notesPlain'
                    secretField.value = field['itemValue']
                    secretField.purpose = 'NOTES'
                    clavisSecret.fields.append(secretField)
                if field['slug'] == 'username':
                    secretField = classes.secretField()
                    secretField.type = 'STRING'
                    secretField.id = 'username'
                    secretField.label = 'username'
                    secretField.value = field['itemValue']
                    secretField.purpose = 'USERNAME'
                    clavisSecret.fields.append(secretField)
                if field['slug'] == 'password':
                    secretField = classes.secretField()
                    secretField.type = 'CONCEALED'
                    secretField.id = 'password'
                    secretField.label = 'password'
                    secretField.value = field['itemValue']
                    secretField.purpose = 'PASSWORD'
                    clavisSecret.fields.append(secretField)
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