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
    

    if 'test' in targets:
        pass
    
        

    if 'all' in targets or 'load-data' in targets:

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

    if 'all' in targets or 'task1' in targets:

        print("------------------------- GENERATING T1 RECOMMENDATIONS BASED ON CONFIG -------------------------")

        # Create billboard client
        print('Creating list of recommended songs')
        billboard_recommender = billboard()
        song_recommendations = billboard_recommender.getList(startY=2010, endY=2020, genre=['electronica'])

        print('Saving list of recommended songs')
        # Save to csv
        pd.DataFrame({'song_recommendations': song_recommendations}).to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t1.csv'))
    
    if 'all' in targets or 'task2' in targets:
        print("------------------------- GENERATING T2 RECOMMENDATIONS BASED ON CONFIG -------------------------")

        print("LOADING FILES")
        # Read in data
        print("Loading Billboard")
        stuff = pd.read_csv(os.path.join(DATA_DIR_RAW, 'billboard_songs.csv'))

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


        # def extract_users(df, age, age_range):
        #     start = age - age_range
        #     end = age + age_range
        #     users_selected = df[(df['age'] >= start) & (df['age'] <= end)].reset_index(drop=True)
        #     return users_selected

        # def extract_histories(df, users):
        #     extracted_history = df[df['user_id'].isin(users['user_id'])]
        #     return extracted_history

        print("CLEANING HISTORY DATA")
        # Choose users
        chosen_users = extract_users(cleaned_users, 55, 5)
        cleaned_history = lastfm_usersong[['user_id', 'artist_id', 'artist_name', 'plays']].dropna().reset_index(drop=True)
        cleaned_history = extract_histories(cleaned_history, cleaned_users)
        chosen_history = extract_histories(cleaned_history, chosen_users)

        #most_occurrence = pd.DataFrame(chosen_history.groupby('artist_name')['plays'].count().sort_values(ascending=False))


        print("CREATING SPOTIPY OBJECT")
        # Application information
        client_id = 'f78a4f4cfe9c40ea8fe346b0576e98ea'
        client_secret = 'c26db2d4c1fb42d79dc99945b2360ab4'

        # Temporary placeholder until we actually get a website going
        redirect_uri = 'https://google.com/'

        # The permissions that our application will ask for
        scope = " ".join(['playlist-modify-public',"user-top-read","user-read-recently-played","playlist-read-private"])

        username = 'gazzaniga3'

        # Oauth object    
        sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, username=username)
        print("Created Oauth object")

        # Force auth every time
        authUrl = sp_oauth.get_authorize_url()


        try:
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        except:
            os.remove(f'.cache-{username}')
            sp = spotipy.Spotify(auth_manager=sp_oauth)
        print("Created spotipy object")


        # def get_genres(row):
        #     artist = row['artist_name']
        #     uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
        #     artist_info = sp.artist(uri)
        #     genres = artist_info['genres']
        #     row['genres'] = genres
        #     return 
            
        # def get_related_artist(uri):
        #     related = sp.artist_related_artists(uri)
        #     related_lst = []
        #     for artist in related['artists'][:5]:
        #         related_lst.append(artist['name'])
        #     return related_lst

        # def get_top_tracks(uri):
        #     top_tracks = sp.artist_top_tracks(uri)
        #     top_lst = []
        #     for track in top_tracks['tracks'][:5]:
        #         top_lst.append(track['name'])
        #     return top_lst

        # def extract_features(row):
        #     artist = row['artist_name']
        #     uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
        #     related_artists_extracted = get_related_artist(uri)
        #     top_tracks_extracted = get_top_tracks(uri)
        #     artist_info = sp.artist(uri)
        #     genres = artist_info['genres']
        #     popularity = artist_info['popularity']
        #     followers = artist_info['followers']['total']
        #     row['uri'] = uri
        #     row['genres'] = genres
        #     row['related_artists'] = related_artists_extracted
        #     row['top_tracks'] = top_tracks_extracted
        #     row['popularity'] = popularity
        #     row['followers'] = followers
        #     return row

        #print("GETTING TOP ARTISTS")
        # Getting top artists
        #top_artists = most_occurrence
        #top_artists.reset_index(level=0, inplace=True)
        #top_artists = top_artists[top_artists['plays'] > 10]
        #top_artist_df = top_artists.apply(extract_features, axis=1)
        #selection = ['country']
        #top_artist_df = top_artist_df[top_artist_df.genres.apply(lambda x: bool(set(x) & set(selection)))]

        #print("GETTING TOP TRACKS")
        # Getting top tracks
        #top_tracks = pd.DataFrame(top_artist_df['top_tracks'].explode().reset_index(drop=True))
        #top_tracks.columns = ['track_name']
        #top_tracks = top_tracks[:100]

        # def extract_track_features(row):
        #     uri = sp.search(row)['tracks']['items'][0]['uri']
        #     features = sp.audio_features(uri)[0]
        #     dance = features['danceability']
        #     energy = features['energy']
        #     key = features['key']
        #     loudness = features['loudness']
        #     mode = features['mode']
        #     speech = features['speechiness']
        #     acoustic = features['acousticness']
        #     instrument = features['instrumentalness']
        #     live = features['liveness']
        #     valence = features['valence']
        #     tempo = features['tempo']
        #     return uri, dance, energy, key, loudness, mode, speech, acoustic, instrument, live, valence, tempo
            
        #top_tracks['uri'], top_tracks['danceability'], top_tracks['energy'], top_tracks['key'], top_tracks['loudness'], top_tracks['mode'], top_tracks['speechiness'], top_tracks['acousticness'], top_tracks['instrumentalness'], top_tracks['liveness'], top_tracks['valence'], top_tracks['valence'] = zip(*top_tracks['track_name'].apply(extract_track_features))

        ap = chosen_history

        artist_rank = ap.groupby(['artist_name']) \
        .agg({'user_id' : 'count', 'plays' : 'sum'}) \
        .rename(columns={"user_id" : 'totalUniqueUsers', "plays" : "totalArtistPlays"}) \
        .sort_values(['totalArtistPlays'], ascending=False)
        artist_rank['avgUserPlays'] = artist_rank['totalArtistPlays'] / artist_rank['totalUniqueUsers']

        ap = ap.join(artist_rank, on="artist_name", how="inner") \
        .sort_values(['plays'], ascending=False)

        pc = ap.plays
        play_count_scaled = (pc - pc.min()) / (pc.max() - pc.min())
        ap = ap.assign(playCountScaled=play_count_scaled)

        ap = ap.drop_duplicates()
        grouped_df = ap.groupby(['user_id', 'artist_id', 'artist_name']).sum().reset_index()

        grouped_df['artist_name'] = grouped_df['artist_name'].astype("category")
        grouped_df['user_id'] = grouped_df['user_id'].astype("category")
        grouped_df['artist_id'] = grouped_df['artist_id'].astype("category")
        grouped_df['user_id'] = grouped_df['user_id'].cat.codes
        grouped_df['artist_id'] = grouped_df['artist_id'].cat.codes

        print("GETTING USER PLAYLISTS")
        r = sp.current_user_playlists()

        # def parse_playlist_ids(response):
        #     playlist_ids = []
        #     for item in response['items']:
        #         pid = item['id']

        #         playlist_ids.append(pid)
        #     return playlist_ids

        # def parse_track_info(response):
        #     track_names = []
        #     artist_names = []
        #     album_names = []
            
        #     for item in r['items']:
                        
        #         # Gets the name of the track
        #         track = item['track']['name']
        #         # Gets the name of the album
        #         album = item['track']['album']['name']
        #         # Gets the name of the first artist listed under album artists
        #         artist = item['track']['album']['artists'][0]['name']
                    
        #         track_names.append(track)
        #         album_names.append(album)
        #         artist_names.append(artist) 
        #     return track_names, album_names, artist_names

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
            break

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

        # def recommend(user_id, sparse_user_artist, user_vecs, artist_vecs, num_contents=10):
        #     user_interactions = sparse_user_artist[user_id,:].toarray()
        #     user_interactions = user_interactions.reshape(-1) + 1
        #     user_interactions[user_interactions > 1] = 0
        #     rec_vector = user_vecs[user_id,:].dot(artist_vecs.T)
        #     min_max = MinMaxScaler()
        #     rec_vector_scaled = min_max.fit_transform(rec_vector.reshape(-1,1))[:,0]
        #     recommend_vector = user_interactions * rec_vector_scaled
        #     content_idx = np.argsort(recommend_vector)[::-1][:num_contents]
        #     artists = []
        #     scores = []
        #     for idx in content_idx:
        #         artists.append(grouped_df.artist_name.loc[grouped_df.artist_id == idx].iloc[0])
        #         scores.append(recommend_vector[idx])
        #     recommendations = pd.DataFrame({'artist_name': artists, 'score': scores})
        #     return recommendations

        # Create recommendations for current user
        user_id = curr_user

        print("GENERATING RECOMMMENDATIONS LIST")
        recommendations = recommend(user_id, sparse_user_artist, user_vecs, artist_vecs, updated_df)

        updated_df.loc[updated_df['user_id'] == curr_user].sort_values(by=['playCountScaled'], ascending=False)[['artist_name', 'user_id', 'playCountScaled']].head(10)

        artist_list = recommendations['artist_name'].to_list()

        # def get_top_recommended_tracks(artist_list):
        #     top_list = []
        #     for artist in artist_list:
        #         uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
        #         top_tracks = sp.artist_top_tracks(uri)
        #         for track in top_tracks['tracks'][:5]:
        #             top_list.append(track['name'])
        #     return top_list

        recommended_tracks = pd.DataFrame(get_top_recommended_tracks(artist_list, sp), columns=['track_name'])

        recommended_tracks.to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs_t2.csv'))

if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)