#
# Script for create/update secrets in GitHub using:
# - API requests
# - File with secret
# - GitHub Token
# - Repository public key for encrypting
#
#   Ⓒ Alexander Shydlovskyi
#

from base64 import b64encode
from ipaddress import v4_int_to_packed
from lib2to3.pgen2 import token
import re
from nacl import encoding, public
import requests
import sys, getopt, json


#Encrypt your secret using pynacl with Python 3.
#https://docs.github.com/en/rest/reference/actions#create-or-update-a-repository-secret
def encrypt(public_key: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def read_text(filename) -> str:
    with open(filename, "r") as file:
        data = file.read().replace("\n", "")
    return data

#get public key for API requests
#https://docs.github.com/en/rest/reference/actions#get-a-repository-public-key
def get_public_key(login: str, github_token: str, repository: str) -> json:
    
    url='https://api.github.com/repos/'+login+'/'+repository+'/actions/secrets/public-key'

    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    
    response = requests.get(url, headers=headers, auth=(login, github_token))
    if str(response.status_code) != "200":
        print('Error with API request for get public key. Status code: '+str(response.status_code))
        sys.exit(2)
    return json.loads(response.content)



#Working with GitHub API. Get public key of repository
def update_secret(login: str, github_token: str, secret_name: str, repository: str, filename: str ) -> str:

    url='https://api.github.com/repos/'+login+'/'+repository+'/actions/secrets/'+secret_name

    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
    
    data = get_public_key(login,github_token,repository)
    for key, value in data.items():
        if key == "key_id":
            key_id = value
        if key == "key":
            public_key = value

    encrypted_value = encrypt(public_key, read_text(filename))

    data = '{"encrypted_value":"'+encrypted_value+'","key_id":"'+key_id+'"}'

    response = requests.put(url, headers=headers, data=data, auth=(login, github_token))
    if response.status_code == 204:
        return("Secret has been updated") 
    elif response.status_code == 201:
        return("Secret has been created")
    else: return ('Error with updating secret. Status code:',response.status_code)



#Main function. Usage argumets
def main(argv):

    usage = """Usage: git_secret.py --lg=<github_login> --tk=<github_token> --sn=<secret_name> --repo=<repositoy_name> --filename=<filename_with_sectet>
    """
    if len(sys.argv) <= 5:
        print('You must set all parameters!\n'+usage)
    else:
        try:
            opts, args = getopt.getopt(argv,"h:",["lg=","tk=","sn=","repo=","filename="])
        except getopt.GetoptError:
            print(usage)
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print(usage)
                sys.exit()
            elif opt in ("--lg"):
                login = arg        
            elif opt in ("--tk"):
                github_token = arg
            elif opt in ("--sn"):
                secret_name = arg
            elif opt in ("--repo"):
                repository = arg
            elif opt in ("--filename"):
                filename = arg
        print(update_secret(login, github_token, secret_name, repository, filename))


if __name__ == "__main__":
    main(sys.argv[1:])

