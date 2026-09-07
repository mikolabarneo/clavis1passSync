import os
from functions import getSecret, getSecrets, getVaults

def main():
    secrets = []
    fqdn = os.environ.get('FQDN')
    key = os.environ.get('KEY')
    vaults = getVaults(fqdn, key)
    for vault in vaults:
        vaultsecrets = getSecrets(fqdn, vault['id'], key)
        for secret in vaultsecrets:
            fullsecret = getSecret(fqdn, vault['id'], secret['id'], key)
            secrets.append(fullsecret)
    print(secrets)


if __name__== '__main__':
    main()