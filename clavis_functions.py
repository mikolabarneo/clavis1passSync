import base64

import requests

from classes import folder as clavisFolderClass, secret as clavisSecretClass, secretField as clavisSecretFieldClass

CERTIFICATE_TEMPLATE_NAME = 'Certificate'

def getClavisSecrets(fqdn,key,folderid=None, take=1000,skip=0):
    header = {}
    header['Content-Type'] = 'application/json;'
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    secretsurl = site + '/api/v2/secrets'+ '?take=' + str(take) + '&skip=' + str(skip)
    if folderid:
        secretsurl += '&filter.folderId=' + str(folderid)+ '&filter.includeSubfolders=true'
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

def getClavisSecretField(fqdn,secretid,slug,key):
    header = {}
    header['Accept'] = '*/*'
    header['Authorization'] = 'Bearer '+key
    site = 'https://'+fqdn
    fieldurl = site + '/api/v1/secrets/' + str(secretid) + '/fields/' + slug
    result = requests.get(fieldurl,headers=header,verify=True)
    if result.status_code != 200:
        return None
    return result.content

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

def getAllClavisFolders(fqdn,key,take=1000):
    records = []
    skip = 0
    while True:
        page = getClavisFolders(fqdn,key,take=take,skip=skip)
        if page is None:
            return None
        pagerecords = page.get('records', [])
        records.extend(pagerecords)
        if len(pagerecords) < take:
            break
        skip += take
    return records

def getAllClavisSecrets(fqdn,key,folderid=None,take=1000):
    records = []
    skip = 0
    while True:
        page = getClavisSecrets(fqdn,key,folderid=folderid,take=take,skip=skip)
        if page is None:
            return None
        pagerecords = page.get('records', [])
        records.extend(pagerecords)
        if len(pagerecords) < take:
            break
        skip += take
    return records

def _decodeFileFieldValue(rawBytes):
    try:
        return rawBytes.decode('utf-8'), False
    except UnicodeDecodeError:
        return base64.b64encode(rawBytes).decode('ascii'), True

def _buildLoginFields(clavisSecret,items):
    for field in items:
        slug = field.get('slug')
        if slug == 'resource':
            clavisSecret.urls.append({
                'href': field['itemValue'],
                'label': field['fieldName'],
                'primary': True,
            })
        elif slug == 'notes':
            secretField = clavisSecretFieldClass()
            secretField.type = 'STRING'
            secretField.id = 'notesPlain'
            secretField.label = 'notesPlain'
            secretField.value = field['itemValue']
            secretField.purpose = 'NOTES'
            clavisSecret.fields.append(secretField)
        elif slug == 'username':
            secretField = clavisSecretFieldClass()
            secretField.type = 'STRING'
            secretField.id = 'username'
            secretField.label = 'username'
            secretField.value = field['itemValue']
            secretField.purpose = 'USERNAME'
            clavisSecret.fields.append(secretField)
        elif slug == 'password':
            secretField = clavisSecretFieldClass()
            secretField.type = 'CONCEALED'
            secretField.id = 'password'
            secretField.label = 'password'
            secretField.value = field['itemValue']
            secretField.purpose = 'PASSWORD'
            clavisSecret.fields.append(secretField)

# Certificate secrets carry file fields (certificate/private-key/certificate-bundle)
# whose real content isn't in the list/detail response (itemValue is a placeholder) -
# it has to be downloaded separately via getClavisSecretField. A populated file field
# has a non-null fileAttachmentId; an empty one still reports isFile=True but 404s.
def _buildCertificateFields(fqdn,key,clavisId,clavisSecret,items):
    for field in items:
        slug = field.get('slug')
        label = field.get('fieldName') or slug

        if field.get('isFile'):
            if not field.get('fileAttachmentId'):
                continue
            rawBytes = getClavisSecretField(fqdn,clavisId,slug,key)
            if rawBytes is None:
                continue
            value, wasBase64 = _decodeFileFieldValue(rawBytes)
            secretField = clavisSecretFieldClass()
            secretField.type = 'CONCEALED'
            secretField.id = slug
            secretField.label = label + ' (base64)' if wasBase64 else label
            secretField.value = value
            secretField.purpose = ''
            clavisSecret.fields.append(secretField)
        elif field.get('isNotes'):
            secretField = clavisSecretFieldClass()
            secretField.type = 'STRING'
            secretField.id = 'notesPlain'
            secretField.label = 'notesPlain'
            secretField.value = field.get('itemValue', '')
            secretField.purpose = 'NOTES'
            clavisSecret.fields.append(secretField)
        elif field.get('isPassword'):
            # purpose must stay '' here: the SECURE_NOTE template has no PASSWORD-purpose
            # slot, and 1Password Connect rejects the whole item ("too many password
            # fields") if a field claims that purpose outside LOGIN/PASSWORD-style
            # templates. CONCEALED alone still keeps the value masked.
            secretField = clavisSecretFieldClass()
            secretField.type = 'CONCEALED'
            secretField.id = slug
            secretField.label = label
            secretField.value = field.get('itemValue', '')
            secretField.purpose = ''
            clavisSecret.fields.append(secretField)
        else:
            secretField = clavisSecretFieldClass()
            secretField.type = 'STRING'
            secretField.id = slug
            secretField.label = label
            secretField.value = field.get('itemValue', '')
            secretField.purpose = ''
            clavisSecret.fields.append(secretField)

def buildClavisSecretForOnePass(fqdn,key,clavisId,folderId,vaultId,vaultName):
    secretdetails = getClavisSecret(fqdn,clavisId,key)
    if secretdetails is None:
        return None

    clavisSecret = clavisSecretClass()
    clavisSecret.clavisId = secretdetails['id']
    clavisSecret.title = secretdetails['name']

    if folderId is not None:
        secretfolder = getClavisFolders(fqdn,key,folderId)
        if secretfolder:
            clavisFolder = clavisFolderClass()
            clavisFolder.id = secretfolder['id']
            clavisFolder.folderName = secretfolder['folderName']
            clavisFolder.parentFolderId = secretfolder['parentFolderId']
            clavisFolder.folderPath = secretfolder['folderPath']
            clavisSecret.folder = clavisFolder

    clavisSecret.buildTags()
    clavisSecret.sections[0].label = str(clavisSecret.clavisId)
    clavisSecret.vault.id = vaultId
    clavisSecret.vault.name = vaultName

    items = secretdetails.get('items', [])
    if secretdetails.get('secretTemplateName') == CERTIFICATE_TEMPLATE_NAME:
        clavisSecret.category = 'SECURE_NOTE'
        _buildCertificateFields(fqdn,key,clavisSecret.clavisId,clavisSecret,items)
    else:
        _buildLoginFields(clavisSecret,items)

    return clavisSecret

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
    