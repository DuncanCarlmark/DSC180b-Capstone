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



# Paths for storing data
DATA_DIR = 'data'
DATA_DIR_RAW = os.path.join(DATA_DIR, 'raw')
DATA_DIR_CLEAN = os.path.join(DATA_DIR, 'clean')
DATA_DIR_RECOMMENDATIONS = os.path.join(DATA_DIR, 'recommendations')

USER_PROFILE = os.path.join(DATA_DIR_RAW, 'usersha1-profile.tsv')
USER_ARTIST = os.path.join(DATA_DIR_RAW, 'usersha1-artmbid-artname-plays.tsv')

BILLBOARD_SONGS = os.path.join(DATA_DIR_RAW, 'billboard_songs.csv')
BILLBOARD_FEATURES = os.path.join(DATA_DIR_RAW, 'billboard_info.xlsx')



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


    if 'all' in targets or 'load-data' in targets or 'test' in targets:

        # Make data directory and subfolders for billboard and last.fm
        print("------------------------- DOWNLOADING RAW TRAINING DATA -------------------------")

        # Make necessary directories if they do not already exist
        print("CREATING DATA DIRECTORIES")
        if os.path.isdir(DATA_DIR):
            print("Data directory already exists. Skipping creation.")
        else:
            os.mkdir(DATA_DIR)
            os.mkdir(DATA_DIR_RAW)
            os.mkdir(DATA_DIR_CLEAN)
            os.mkdir(DATA_DIR_RECOMMENDATIONS)
            print('Data directory files created')


        # Load data if necessary
        print("DOWNLOADING TRAINING DATA")
        if os.path.isfile(USER_PROFILE) and os.path.isfile(USER_ARTIST):
            print("Data files already exist. Skipping download.")

        else:
            # LAST.FM files
            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/usersha1-profile.tsv')
            open(USER_PROFILE, 'wb').write(r.content)

            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/usersha1-artmbid-artname-plays.tsv')
            open(USER_ARTIST, 'wb').write(r.content)
            print('Data files downloaded.')
            
            # Billboard files
            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/billboard-songs.csv')
            open(BILLBOARD_SONGS, 'wb').write(r.content)

            r = requests.get('https://capstone-raw-data.s3-us-west-2.amazonaws.com/billboard-features.xlsx')
            open(BILLBOARD_FEATURES, 'wb').write(r.content)

    # WILL BE IMPLEMENTED IN FUTURE
    # SIMPLE CLEANING OCCURS IN TASK1 AND TASK 2
    if 'all' in targets or 'clean_data' in targets:
        pass

    if 'all' in targets or 'task1' in targets  or 'test' in targets:

        print("------------------------- GENERATING T1 RECOMMENDATIONS BASED ON CONFIG -------------------------")

        # Create billboard client
        print('Creating list of recommended songs')
        billboard_recommender = billboard()
        song_recommendations = billboard_recommender.getList(startY=2010, endY=2020, genre=[GENRE])

        print('Saving list of recommended songs')
        # Save to csv
        print(len(song_recommendations))
        pd.DataFrame({'song_recommendations': song_recommendations}).to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t1.csv'))
    
    if 'all' in targets or 'task2' in targets or 'test' in targets:
        print("------------------------- GENERATING T2 RECOMMENDATIONS BASED ON CONFIG -------------------------")

        print("LOADING FILES")
        # Read in data

        print("Loading Last.fm")
        lastfm_profile = pd.read_csv(os.path.join(DATA_DIR_RAW, 'usersha1-profile.tsv'),
                                    sep='\t', 
                                    names=['user_id', 'gender', 'age', 'country', 'registered'])

        lastfm_usersong = pd.read_csv(os.path.join(DATA_DIR_RAW,'usersha1-artmbid-artname-plays.tsv'), 
                                    sep='\t', 
                                    names=['user_id', 'artist_id', 'artist_name', 'plays'])

        print("CLEANING USER DATA")
        # Minor data cleaning
        cleaned_users = lastfm_profile[['user_id', 'age', 'country']].dropna().reset_index(drop=True)
        cleaned_users_us = cleaned_users[cleaned_users['country'] == 'United States']
        cleaned_users = cleaned_users_us[cleaned_users_us['age'] > 0]

        age_bins = ((cleaned_users.age // 10) * 10).value_counts().reset_index().sort_values(by='index')


        print("CLEANING HISTORY DATA")
        # Choose users
        chosen_users = extract_users(cleaned_users, 55, 5)
        cleaned_history = lastfm_usersong[['user_id', 'artist_id', 'artist_name', 'plays']].dropna().reset_index(drop=True)
        cleaned_history = extract_histories(cleaned_history, cleaned_users)
        chosen_history = extract_histories(cleaned_history, chosen_users)


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

        # Force auth every time
        authUrl = sp_oauth.get_authorize_url()


        try:
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        except:
            os.remove(f'.cache-{username}')
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        print("Created spotipy object")

        ap = chosen_history

        playCount = ap.plays
        normalizedCount = (pc - pc.min()) / (pc.max() - pc.min())
        ap = ap.assign(playCountScaled=normalizedCount)

        ap = ap.drop_duplicates()
        grouped_df = ap.groupby(['user_id', 'artist_id', 'artist_name']).sum().reset_index()

        grouped_df['artist_name'] = grouped_df['artist_name'].astype("category")
        grouped_df['user_id'] = grouped_df['user_id'].astype("category")
        grouped_df['artist_id'] = grouped_df['artist_id'].astype("category")
        grouped_df['user_id'] = grouped_df['user_id'].cat.codes
        grouped_df['artist_id'] = grouped_df['artist_id'].cat.codes

        print("GETTING USER PLAYLISTS")
        r = sp.current_user_playlists()

        playlist_ids = parse_playlist_ids(r)


        # Pull all the tracks from a playlist
        tracks = []
        albums = []
        artists = []

        # Loop through each playlist one by one
        for pid in playlist_ids:
            # Request all track information
            r = sp.playlist_items(pid)
            
            tracks, albums, artists = parse_track_info(r)

        playlist_artists = pd.Series(artists)
        playlist_grouped = playlist_artists.value_counts(normalize=True)

        no_artist = playlist_grouped.shape[0]
        curr_user = grouped_df.iloc[-1]['user_id'] + 1
        curr_user_id = [curr_user] * no_artist

        playlist_df = pd.DataFrame(playlist_grouped, columns=['playCountScaled']) 
        playlist_df.reset_index(level=0, inplace=True)
        playlist_df.columns = ['artist_name', 'playCountScaled']
        playlist_df['user_id'] = pd.Series(curr_user_id)


        cols = playlist_df.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        playlist_df = playlist_df[cols]
        playlist_df.head()

        playlist_df['artist_name'] = playlist_df['artist_name'].str.lower()

        artist_pairing = dict(zip(grouped_df.artist_name, grouped_df.artist_id))
        playlist_df['artist_id'] = playlist_df['artist_name'].map(artist_pairing)
        playlist_df = playlist_df.dropna().reset_index(drop=True)
        playlist_df['artist_id'] = playlist_df['artist_id'].astype(int)

        updated_df = grouped_df.append(playlist_df)

        updated_df['artist_name'] = updated_df['artist_name'].astype("category")
        updated_df['user_id'] = updated_df['user_id'].astype("category")
        updated_df['artist_id'] = updated_df['artist_id'].astype("category")
        updated_df['user_id'] = updated_df['user_id'].cat.codes
        updated_df['artist_id'] = updated_df['artist_id'].cat.codes

        print("CREATING ARTIST-USER AND USER-ARTIST MATRICIES")
        sparse_artist_user = sparse.csr_matrix((updated_df['playCountScaled'].astype(float), (updated_df['artist_id'], updated_df['user_id'])))
        sparse_user_artist = sparse.csr_matrix((updated_df['playCountScaled'].astype(float), (updated_df['user_id'], updated_df['artist_id'])))
        model = implicit.als.AlternatingLeastSquares(factors=20, regularization=0.1, iterations=50)
        

        alpha = 15
        data = (sparse_artist_user * alpha).astype('double')

        print("FITTING ALS MODELS")
        model.fit(data)

        user_vecs = model.user_factors
        artist_vecs = model.item_factors


        # Create recommendations for current user
        user_id = curr_user

        print("GENERATING RECOMMMENDATIONS LIST")
        recommendations = recommend(user_id, sparse_user_artist, user_vecs, artist_vecs, updated_df)

        updated_df.loc[updated_df['user_id'] == curr_user].sort_values(by=['playCountScaled'], ascending=False)[['artist_name', 'user_id', 'playCountScaled']].head(10)

        artist_list = recommendations['artist_name'].to_list()


        recommended_tracks = pd.DataFrame(get_top_recommended_tracks(artist_list, sp), columns=['track_name'])

        recommended_tracks.to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t2.csv'))

if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)