import sys
import json
import os
import pandas as pd
import requests
import spotipy
from collections import defaultdict

# From Sarat
import scipy.sparse as sparse
import numpy as np
import random
import implicit
from sklearn.preprocessing import MinMaxScaler
import ipywidgets
from ipywidgets import FloatProgress


# Custom Library Imports
from src.build_lib.billboard_build import billboard
from src.build_lib.task2_utils import *
from src.models.model_task2 import *
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
    GENRE = None


    if 'test' in targets:
        # Parse Config File
        with open('config/test.json') as fh:
            run_cfg = json.load(fh)
            USERNAME = run_cfg['username']
            PARENT_AGE = run_cfg['parent_age']
            GENRE = run_cfg['genre']
            CACHE_PATH = os.path.join('test', '.cache-' + USERNAME)
    else:
        # Parse Config File
        with open('config/run.json') as fh:
            run_cfg = json.load(fh)
            USERNAME = run_cfg['username']
            PARENT_AGE = run_cfg['parent_age']
            GENRE = run_cfg['genre']


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
        user_profile_df, user_artist_df = clean_billboard(user_profile_df, user_artist_df)
        print('Last.fm data cleaned')        

        # Save cleaned files to clean directory
        billboard_songs.to_csv(BILLBOARD_SONGS_PATH_CLEAN)
        billboard_features.to_csv(BILLBOARD_FEATURES_PATH_CLEAN)
        user_profile_df.to_csv(USER_PROFILE_PATH_CLEAN)
        user_artist_df.to_csv(USER_PROFILE_PATH_CLEAN)
        print('Saving cleaned data to data/clean')


# ------------------------------------------------------ TASK 1 RECOMMENDATION ------------------------------------------------------


    if 'all' in targets or 'task1' in targets  or 'test' in targets:

        print("---------------------------------------- GENERATING T1 RECOMMENDATIONS BASED ON CONFIG ----------------------------------------")

        # Create billboard client
        print('Creating list of recommended songs')
        billboard_recommender = billboard()
        song_recommendations = billboard_recommender.getList(startY=2010, endY=2020, genre=[GENRE])

        print('Saving list of recommended songs')
        # Save to csv
        print(len(song_recommendations))
        pd.DataFrame({'song_recommendations': song_recommendations}).to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t1.csv'))


# ------------------------------------------------------ TASK 2 RECOMMENDATION ------------------------------------------------------


    if 'all' in targets or 'task2' in targets or 'test' in targets:
        print("---------------------------------------- GENERATING T2 RECOMMENDATIONS BASED ON CONFIG ----------------------------------------")

        print("LOADING FILES")
        # Read in data

        print("Loading Last.fm")
        
        user_profile_df, user_artist_df = read_datafiles(USER_PROFILE_PATH_CLEAN, USER_ARTIST_PATH_CLEAN)
        
        parent_age = 55
        age_range = 5
        chosen_users = extract_users(user_profile_df, parent_age, age_range)
        chosen_history = extract_histories(user_artist_df, chosen_users)


        print("CREATING SPOTIPY OBJECT")
        # Application information
        client_id = 'f78a4f4cfe9c40ea8fe346b0576e98ea'
        client_secret = 'c26db2d4c1fb42d79dc99945b2360ab4'

        # Temporary placeholder until we actually get a website going
        redirect_uri = 'https://google.com/'

        # The permissions that our application will ask for
        scope = " ".join(['playlist-modify-public',"user-top-read","user-read-recently-played","playlist-read-private"])

        username = USERNAME
        sp_oauth = None
        # Oauth object    
        if 'test' in targets:
            sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, 
                                                    scope=scope, cache_path = CACHE_PATH, username=username)
        else:
            sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, 
                                                    scope=scope, username=username)
        print("Created Oauth object")

        try:
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        except:
            os.remove(f'.cache-{username}')
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        print("Created spotipy object")

        grouped_df = prepare_dataset(chosen_history)

        print("GETTING USER PLAYLISTS")
        
        playlist_df, current_user = pull_user_playlist_info(sp, grouped_df)
        
        
        updated_df = updated_df_with_user(grouped_df, playlist_df)

        print("CREATING ARTIST-USER AND USER-ARTIST MATRICIES")
        

        alpha = 15
        
        print("FITTING ALS MODELS")

        # Create recommendations for current user
        user_id = current_user
        
        sparse_user_artist, user_vecs, artist_vecs = build_implicit_model(updated_df, alpha)
        
        print("GENERATING RECOMMMENDATIONS LIST")
        
        artist_recommendations = recommend(sp, user_id, sparse_user_artist, user_vecs, artist_vecs, updated_df)

        selection = ['rock']
        N = 50

        recommended_tracks = get_top_recommended_tracks(artist_recommendations, selection, N)

        recommended_tracks.to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t2.csv'))

if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)