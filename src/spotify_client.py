import requests
import base64
import datetime
from urllib.parse import urlencode

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import time
import re
import json
from datetime import datetime, time, date

import datetime
import time

from requests.exceptions import SSLError
from requests.exceptions import ConnectionError

# #Client identification for API requests
client_id = 'f78a4f4cfe9c40ea8fe346b0576e98ea'
client_secret = 'c26db2d4c1fb42d79dc99945b2360ab4'
def temp():
    print('it worked')

# Rough client for simplifying API calls
class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = 'https://accounts.spotify.com/api/token'
    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        
    def get_client_credentials(self):
        '''
        returns a base 64 encoded string
        '''
        client_id = self.client_id
        client_secret = self.client_secret

        if client_id == None or client_secret == None:
            raise Exception("Must set client_id and client_secret")
        
        client_creds = f'{client_id}:{client_secret}'
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
    
    def get_token_header(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            'Authorization' : f'Basic {client_creds_b64}' # Basic <base64 encoded client_id:client_secret>
        }
    
    def get_token_data(self):
        return {
            'grant_type': 'client_credentials'
        }
    
    def auth(self):
        token_data = self.get_token_data()
        token_headers = self.get_token_header()
        token_url = self.token_url

        
        r = requests.post(token_url, data = token_data, headers = token_headers)
        
        
        if r.status_code not in range (200, 299):
            return False
        token_response_data = r.json()
        now = datetime.datetime.now()
        access_token = token_response_data['access_token']
        expires_in = token_response_data['expires_in'] #seconds
        expires = now + datetime.timedelta(seconds = expires_in)
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        self.access_token = access_token
        return True
        
    def searchTrack(self, item):
        access_token = self.access_token
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = 'https://api.spotify.com/v1/search'
        data = urlencode({'q': item, 'type':'track'})

        lookup_url = f'{endpoint}?{data}'
        # print(lookup_url)

        r = requests.get(lookup_url, headers=headers)
        # print(r.status_code)
        return r.json()
    
    def searchAlbum(self, item):
        access_token = self.access_token
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = 'https://api.spotify.com/v1/search'
        data = urlencode({'q': item, 'type':'album'})

        lookup_url = f'{endpoint}?{data}'
        print(lookup_url)

        r = requests.get(lookup_url, headers=headers)
        print(r.status_code)
        return r.json()
    
    def searchArtist(self, item):
        access_token = self.access_token
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        endpoint = 'https://api.spotify.com/v1/search'
        data = urlencode({'q': item, 'type':'artist'})

        lookup_url = f'{endpoint}?{data}'
        print(lookup_url)

        r = requests.get(lookup_url, headers=headers)
        print(r.status_code)
        return r.json()