import os
from onepass_functions import getOPSecret, getOPSecrets, getOPVaults, createOPSecret
from clavis_functions import getClavisFolders, getClavisSecrets, getClavisSecret, getClavisFolderTreeMembers, getClavisFolderRootFolderId
import classes

def main():
    clavisSecrets = []
    onePassFQDN = os.environ.get('OPFQDN')
    onePassKey = os.environ.get('OPKEY')
    onePassVaultId = os.environ.get('OPVAULTID')
    clavisFQDN = os.environ.get('CLAVISFQDN')
    clavisKey = os.environ.get('CLAVISKEY')
    clavisStartFolder = int(os.environ.get('CLAVISSTARTFOLDERID'))
    clavisSecretList = getClavisSecrets(clavisFQDN, clavisKey, clavisStartFolder)
    if clavisSecretList is None:
        print("Error retrieving Clavis secrets. Please check your credentials and try again.")
        return
    for secret in clavisSecretList['records']:
        secretdetails = getClavisSecret(clavisFQDN, secret['id'], clavisKey)
        clavisSecret = classes.secret()
        clavisSecret.clavisId = secretdetails['id']
        clavisSecret.title = secretdetails['name']
        secretfolder = getClavisFolders(clavisFQDN, clavisKey, secret['folderId'], )
        clavisFolder = classes.folder()
        clavisFolder.id = secretfolder['id']
        clavisFolder.folderName = secretfolder['folderName']
        clavisFolder.parentFolderId = secretfolder['parentFolderId']
        clavisFolder.folderPath = secretfolder['folderPath']
        clavisSecret.folder = clavisFolder
        clavisSecret.buildTags()
        clavisSecret.sections[0].label = str(clavisSecret.clavisId)
        clavisSecret.vault.id = onePassVaultId  #hardcoded for now, but can be changed to a variable if needed
        clavisSecret.vault.name = 'CSST' #hardcoded for now, but can be changed to a variable if needed
        for field in secretdetails['items']:
            if field['slug'] == 'resource':
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
    for secret in clavisSecrets:
        createOPSecret(onePassFQDN, onePassVaultId, onePassKey, secret)
    


if __name__== '__main__':
    main()