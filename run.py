import sys
import json
import os
import pandas as pd
import requests
import spotipy
from collections import defaultdict

# From Sarat
#import scipy.sparse as sparse
#import numpy as np
#import random
#import implicit
#from sklearn.preprocessing import MinMaxScaler
#import ipywidgets
#from ipywidgets import FloatProgress


# Custom Library Imports
from src.build_lib.billboard_build import billboard
#from src.build_lib.task2_utils import *
from src.models.task2 import userParent
#from src.models.model_task2 import *
from src.build_lib.cleaning_utils import *



# Paths for storing data
DATA_DIR = 'data'
# Data subdirectories
DATA_DIR_RAW = os.path.join(DATA_DIR, 'raw')
DATA_DIR_CLEAN = os.path.join(DATA_DIR, 'clean')
DATA_DIR_RECOMMENDATIONS = os.path.join(DATA_DIR, 'recommendations')

# last.fm files 
USER_PROFILE_PATH_RAW = os.path.join(DATA_DIR_RAW, 'user_profile.csv')
USER_ARTIST_PATH_RAW = os.path.join(DATA_DIR_RAW, 'user_artist.csv')

# billboard files
BILLBOARD_SONGS_PATH_RAW = os.path.join(DATA_DIR_RAW, 'billboard_songs.csv')
BILLBOARD_FEATURES_PATH_RAW = os.path.join(DATA_DIR_RAW, 'billboard_features.csv')

# last.fm files
USER_PROFILE_PATH_CLEAN = os.path.join(DATA_DIR_CLEAN, 'user_profile.csv')
USER_ARTIST_PATH_CLEAN = os.path.join(DATA_DIR_CLEAN, 'user_artist.csv')

# billboard files
BILLBOARD_SONGS_PATH_CLEAN = os.path.join(DATA_DIR_CLEAN, 'billboard_songs.csv')
BILLBOARD_FEATURES_PATH_CLEAN = os.path.join(DATA_DIR_CLEAN, 'billboard_features.csv')





def main(targets):

    USERNAME = None
    PARENT_AGE = None
    GENRES = None


    if 'test' in targets:
        # Parse Config File
        with open('config/test.json') as fh:
            run_cfg = json.load(fh)
            USERNAME = run_cfg['username']
            PARENT_AGE = run_cfg['parent_age']
            GENRES = run_cfg['genres']
            CACHE_PATH = os.path.join('test', '.cache-' + USERNAME)
    else:
        # Parse Config File
        with open('config/run.json') as fh:
            run_cfg = json.load(fh)
            USERNAME = run_cfg['username']
            PARENT_AGE = run_cfg['parent_age']
            GENRES = run_cfg['genres']


# ------------------------------------------------------ LOAD DATA ------------------------------------------------------


    if 'all' in targets or 'load-data' in targets or 'test' in targets:

        # Make data directory and subfolders for billboard and last.fm
        print("---------------------------------------- DOWNLOADING RAW TRAINING DATA ----------------------------------------")

        # Make necessary directories if they do not already exist
        print("CREATING DATA DIRECTORIES")
        if os.path.isdir(DATA_DIR):
            print("Data directory already exists. Skipping creation.")
        else:
            os.mkdir(DATA_DIR)
            os.mkdir(DATA_DIR_RAW)
            os.mkdir(DATA_DIR_CLEAN)
            os.mkdir(DATA_DIR_RECOMMENDATIONS)
            print('Data directories created')


        # Load data if necessary
        print("DOWNLOADING TRAINING DATA")
        if os.path.isfile(USER_PROFILE_PATH_RAW) and os.path.isfile(USER_ARTIST_PATH_RAW):
            print("Data files already exist. Skipping download")

        else:
            # LAST.FM files
            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/user_profile.csv')
            open(USER_PROFILE_PATH_RAW, 'wb').write(r.content)

            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/user_artist.csv')
            open(USER_ARTIST_PATH_RAW, 'wb').write(r.content)
            print('Last.fm data downloaded')
            
            # Billboard files
            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/billboard_songs.csv')
            open(BILLBOARD_SONGS_PATH_RAW, 'wb').write(r.content)

            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/billboard_features.csv')
            open(BILLBOARD_FEATURES_PATH_RAW, 'wb').write(r.content)
            print('Billboard data downloaded')


# ------------------------------------------------------ CLEAN DATA ------------------------------------------------------


    # WILL BE IMPLEMENTED IN FUTURE
    # SIMPLE CLEANING OCCURS IN TASK1 AND TASK 2
    if 'all' in targets or 'clean-data' in targets:

        print("---------------------------------------- CLEANING TRAINING DATA ----------------------------------------")

        # Cleaning billboard data
        print('CLEANING BILLBOARD DATA')
        billboard_songs = pd.read_csv(BILLBOARD_SONGS_PATH_RAW)
        billboard_features = pd.read_csv(BILLBOARD_FEATURES_PATH_RAW)
        billboard_songs, billboard_features = clean_billboard(billboard_songs, billboard_features)     
        print('Billboard data cleaned')   

        # Cleaning last.fm data
        print('CLEANING LAST.FM DATA')
        user_profile_df = pd.read_csv(USER_PROFILE_PATH_RAW)
        user_artist_df = pd.read_csv(USER_ARTIST_PATH_RAW)
        user_profile_df, user_artist_df = clean_lastfm(user_profile_df, user_artist_df)
        print('Last.fm data cleaned')        

        # Save cleaned files to clean directory
        billboard_songs.to_csv(BILLBOARD_SONGS_PATH_CLEAN, index = False)
        billboard_features.to_csv(BILLBOARD_FEATURES_PATH_CLEAN, index = False)
        user_profile_df.to_csv(USER_PROFILE_PATH_CLEAN, index = False)
        user_artist_df.to_csv(USER_ARTIST_PATH_CLEAN, index = False)
        print('Saving cleaned data to data/clean')


# ------------------------------------------------------ TASK 1 RECOMMENDATION ------------------------------------------------------


    if 'all' in targets or 'task1' in targets  or 'test' in targets:

        print("---------------------------------------- GENERATING T1 RECOMMENDATIONS BASED ON CONFIG ----------------------------------------")

        billboard_songs = pd.read_csv(BILLBOARD_SONGS_PATH_CLEAN)
        billboard_features = pd.read_csv(BILLBOARD_FEATURES_PATH_CLEAN)

        # Create billboard client
        print('Creating list of recommended songs')
        billboard_recommender = billboard(billboard_songs, billboard_features)
        song_recommendations = billboard_recommender.getList(startY=2010, endY=2020, genre=[GENRES])

        print('Saving list of recommended songs')
        # Save to csv
        print(len(song_recommendations))

        pd.DataFrame({'song_recommendations': song_recommendations}).to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t1.csv'))


# ------------------------------------------------------ TASK 2 RECOMMENDATION ------------------------------------------------------


    if 'all' in targets or 'task2' in targets or 'test' in targets:

        print("---------------------------------------- GENERATING T2 RECOMMENDATIONS BASED ON CONFIG ----------------------------------------")

        print("LOADING FILES")
        print("Loading Last.fm")
        
        # Read user-profile data (user_id, gender, age, country, registered)
        user_profile_df = pd.read_csv(USER_PROFILE_PATH_CLEAN)
        # Read user-artist data (user_id, artist_id, artist name, number of plays)
        user_artist_df = pd.read_csv(USER_ARTIST_PATH_CLEAN)
        
        age_range = 5
        N = 30
        
        # Initializing the Model
        user_parent_recommender = userParent(user_profile_df, user_artist_df, PARENT_AGE, age_range, GENRES)
        
        # Initializing Spotipy Object
        print("CREATING SPOTIPY OBJECT")
        # Application information
        client_id = 'f78a4f4cfe9c40ea8fe346b0576e98ea'
        client_secret = 'c26db2d4c1fb42d79dc99945b2360ab4'

        # Temporary placeholder until we actually get a website going
        redirect_uri = 'https://google.com/'

        # The permissions that our application will ask for
        scope = " ".join(['playlist-modify-public',"user-top-read","user-read-recently-played","playlist-read-private"])

        
        sp_oauth = None
        # Oauth object    
        if 'test' in targets:
            sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, 
                                                    scope=scope, cache_path = CACHE_PATH, username=USERNAME)
        else:
            sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, 
                                                    scope=scope, username=USERNAME)
        print("Created Oauth object")

        try:
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        except:
            os.remove(f'.cache-{USERNAME}')
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        print("Created spotipy object")
        
        # Fitting the Model
        
        user_parent_recommender.fit(sp)
        
        # Recommending Songs
        print('Creating list of recommended songs')
        recommended_songs = user_parent_recommender.predict(N)
        
        # Saving recommendations to CSV
        print('Saving list of recommended songs')
        recommended_songs.to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t2.csv'))
        
        print(len(recommended_songs))
        

if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)