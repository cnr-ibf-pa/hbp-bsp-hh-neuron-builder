#! /usr/bin/python3


import requests
import getpass
import json
import os
import argparse


def get_dev_token(username, password):
    r = requests.post(
        url='https://iam.ebrains.eu/auth/realms/hbp/protocol/openid-connect/token',
        auth=('developer', ''),
        data={
            'grant_type': 'password',
            'username': username,
            'password': password
        }
    )

    if r.status_code == 200:
        dev_token = r.json()['access_token']
        return dev_token
    else:
        try:
            print('\nError code: %d\n%s' % (r.status_code, json.dumps(r.json(), indent=4)))
        except:
            print('\nError code: %d\nMessage: %s' % (r.status_code, r.text))
        exit(1)


def create_hhnb_dev_client(username, dev_token):

    client = {
        'clientId': 'hhnb-%s-dev-local-client' % username,
        'name': 'Hodgkin-Huxley Neuron Builder',
        'description': 'Hodgkin-Huxley Neuron Builder developer edition on localhost',
        'rootUrl': 'https://127.0.0.1:8000',
        'baseUrl': '/hh-neuron-builder',
        'redirectUris': [
            '/oidc/callback/'
        ],
        'webOrigins': ['+'],
        'bearerOnly': False,
        'consentRequired': True,
        'standardFlowEnabled': True,
        'implicitFlowEnabled': True,
        'directAccessGrantsEnabled': False,
        'attributes': {
            'contacts': 'first.contact@example.com; second.contact@example.com'
        }
    }

    r = requests.post(
        url='https://iam.ebrains.eu/auth/realms/hbp/clients-registrations/default/',
        headers={'Authorization': 'Bearer %s' % dev_token},
        json=client
    )

    if r.status_code == 200 or r.status_code == 201:
        return r.json()
    else:
        try:
            print('\nError code: %d\n%s' % (r.status_code, json.dumps(r.json(), indent=4)))
        except:
            print('\nError code: %d\nMessage: %s' % (r.status_code, r.text))
        exit(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hodgkin-Huxley Neuron Builder tool to create the OIDC Connect '
                                                 'Client to provide the authentication system with the Ebrains '
                                                 'platform on your local instance of the HHNB.')
    args = parser.parse_args()

    ebrains_username = input('Insert Ebrains username: ')
    ebrains_password = getpass.getpass('Insert Ebrains password: ')

    developer_token = get_dev_token(username=ebrains_username, password=ebrains_password)
    oidc_client = create_hhnb_dev_client(username=ebrains_username, dev_token=developer_token)

    client_filename = 'hhnb-%s-dev-local-client.json' % ebrains_username
    with open(client_filename, 'w') as fd:
        fd.write(json.dumps(oidc_client, indent=4))

    print('Client created in %s\nGood Bye!' % os.path.join(os.getcwd(), client_filename))
