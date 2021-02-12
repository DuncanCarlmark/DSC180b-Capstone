import sys
import json
import os
import pandas as pd
import requests
import spotipy
from collections import defaultdict
import scipy.sparse as sparse
import numpy as np
import random
import implicit
from sklearn.preprocessing import MinMaxScaler
import ipywidgets
from ipywidgets import FloatProgress

def read_datafiles(user_profile_path, user_artist_path):
    # Read datafiles for the LastFM dataset
     
    # Read user-profile data (user_id, gender, age, country, registered)
    user_profile_df = pd.read_csv(user_profile_path,sep='\t', names=['user_id', 'gender', 'age', 'country', 'registered'])
    
    # Read user-artist data (user_id, artist_id, artist name, number of plays)
    user_artist_df = pd.read_csv(user_artist_path, sep='\t', names=['user_id', 'artist_id', 'artist_name', 'plays'])
    
    # Return both datasets
    return user_profile_df, user_artist_df

def clean_datasets(user_profile_df, user_artist_df):
    
    # Drop rows with missing values
    users_wo_na = user_profile_df[['user_id', 'age', 'country']].dropna().reset_index(drop=True)
    
    # Select rows with users from US-recommendation task targeted to US users
    cleaned_users_us = users_wo_na[cleaned_users['country'] == 'United States']
    cleaned_users = cleaned_users_us[cleaned_users_us['age'] > 0]
    
    # Drop rows with missing values
    cleaned_history = user_artist_df[['user_id', 'artist_id', 'artist_name', 'plays']].dropna().reset_index(drop=True)
    
    # Extract listening histories from US users 
    cleaned_history = extract_histories(cleaned_history, cleaned_users)
    
    return cleaned_users, cleaned_history
    
def extract_users(df, age, age_range):
    
    # Build age range for users similar to parents
    start = age - age_range
    end = age + age_range
    
    # Select users from parents' age range
    users_selected = df[(df['age'] >= start) & (df['age'] <= end)].reset_index(drop=True)
    return users_selected

def extract_histories(df, users):
    
    # Extract listening histories from users selected
    extracted_history = df[df['user_id'].isin(users['user_id'])]
    return extracted_history

def prepare_dataset(extracted_history):
    ap = extracted_history
    playCount = ap.plays
    
    #Normalize play count through min-max scaling
    normalizedCount = (pc - pc.min()) / (pc.max() - pc.min())
    ap = ap.assign(playCountScaled=normalizedCount)

    ap = ap.drop_duplicates()
    grouped_df = ap.groupby(['user_id', 'artist_id', 'artist_name']).sum().reset_index()

    # Assign categories to each user and artist
    grouped_df['artist_name'] = grouped_df['artist_name'].astype("category")
    grouped_df['user_id'] = grouped_df['user_id'].astype("category")
    grouped_df['artist_id'] = grouped_df['artist_id'].astype("category")
    grouped_df['user_id'] = grouped_df['user_id'].cat.codes
    grouped_df['artist_id'] = grouped_df['artist_id'].cat.codes
    return grouped_df

def parse_playlist_ids(response):
    # Pull playlist info
    playlist_ids = []
    for item in response['items']:
        pid = item['id']

        playlist_ids.append(pid)
    return playlist_ids

def parse_track_info(response):
    # Pull track, artist, and album info for each track
    track_names = []
    artist_names = []
    album_names = []
    
    for item in response['items']:
                
        # Gets the name of the track
        track = item['track']['name']
        # Gets the name of the album
        album = item['track']['album']['name']
        # Gets the name of the first artist listed under album artists
        artist = item['track']['album']['artists'][0]['name']
            
        track_names.append(track)
        album_names.append(album)
        artist_names.append(artist) 
    return track_names, album_names, artist_names

def pull_user_playlist_info(sp):
    r = sp.current_user_playlists()
    
    # Pull user Spotipy playlists
    playlist_ids = parse_playlist_ids(r)


    # Pull all the tracks from a playlist
    tracks = []
    albums = []
    artists = []

    # Loop through each playlist one by one
    for pid in playlist_ids:
        # Request all track information
        r = sp.playlist_items(pid)
            
        tracks_pulled, albums_pulled, artists_pulled = parse_track_info(r)
        artists.extend(artists_pulled)
    
    
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

    playlist_df['artist_name'] = playlist_df['artist_name'].str.lower()

    artist_pairing = dict(zip(grouped_df.artist_name, grouped_df.artist_id))
    playlist_df['artist_id'] = playlist_df['artist_name'].map(artist_pairing)
    playlist_df = playlist_df.dropna().reset_index(drop=True)
    playlist_df['artist_id'] = playlist_df['artist_id'].astype(int)
    return playlist_df


def recommend(user_id, sparse_user_artist, user_vecs, artist_vecs, grouped_df, num_contents=10):
    # Use user-item interactions
    user_interactions = sparse_user_artist[user_id,:].toarray()
    user_interactions = user_interactions.reshape(-1) + 1
    user_interactions[user_interactions > 1] = 0
    rec_vector = user_vecs[user_id,:].dot(artist_vecs.T)
    min_max = MinMaxScaler()
    rec_vector_scaled = min_max.fit_transform(rec_vector.reshape(-1,1))[:,0]
    recommend_vector = user_interactions * rec_vector_scaled
    content_idx = np.argsort(recommend_vector)[::-1][:num_contents]
    artists = []
    scores = []
    for idx in content_idx:
        artists.append(grouped_df.artist_name.loc[grouped_df.artist_id == idx].iloc[0])
        scores.append(recommend_vector[idx])
        
    # Outputted recommendations and scores
    recommendations = pd.DataFrame({'artist_name': artists, 'score': scores})
    return recommendations

def get_top_recommended_tracks(artist_list, sp):
    top_list = []
    for artist in artist_list:
        uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
        top_tracks = sp.artist_top_tracks(uri)
        # Pull top 5 tracks for each artist
        for track in top_tracks['tracks'][:5]:
            top_list.append(track['name'])
    return top_list
    



