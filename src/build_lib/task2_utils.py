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


def extract_users(df, age, age_range):
            start = age - age_range
            end = age + age_range
            users_selected = df[(df['age'] >= start) & (df['age'] <= end)].reset_index(drop=True)
            return users_selected

def extract_histories(df, users):
    extracted_history = df[df['user_id'].isin(users['user_id'])]
    return extracted_history

# Not used?   
def get_genres(row):
    artist = row['artist_name']
    uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
    artist_info = sp.artist(uri)
    genres = artist_info['genres']
    row['genres'] = genres
    return 

# Needs to have sp as an argument
def get_related_artist(uri):
    related = sp.artist_related_artists(uri)
    related_lst = []
    for artist in related['artists'][:5]:
        related_lst.append(artist['name'])
    return related_lst

# Needs to have sp as an argument
def get_top_tracks(uri):
    top_tracks = sp.artist_top_tracks(uri)
    top_lst = []
    for track in top_tracks['tracks'][:5]:
        top_lst.append(track['name'])
    return top_lst

# Needs to have sp as an argument
# Keyword argument for apply?
def extract_features(row):
    artist = row['artist_name']
    uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
    related_artists_extracted = get_related_artist(uri)
    top_tracks_extracted = get_top_tracks(uri)
    artist_info = sp.artist(uri)
    genres = artist_info['genres']
    popularity = artist_info['popularity']
    followers = artist_info['followers']['total']
    row['uri'] = uri
    row['genres'] = genres
    row['related_artists'] = related_artists_extracted
    row['top_tracks'] = top_tracks_extracted
    row['popularity'] = popularity
    row['followers'] = followers
    return row

# Needs to have sp as an argument
# Keyword argument for apply?
def extract_track_features(row):
    uri = sp.search(row)['tracks']['items'][0]['uri']
    features = sp.audio_features(uri)[0]
    dance = features['danceability']
    energy = features['energy']
    key = features['key']
    loudness = features['loudness']
    mode = features['mode']
    speech = features['speechiness']
    acoustic = features['acousticness']
    instrument = features['instrumentalness']
    live = features['liveness']
    valence = features['valence']
    tempo = features['tempo']
    return uri, dance, energy, key, loudness, mode, speech, acoustic, instrument, live, valence, tempo


def parse_playlist_ids(response):
    playlist_ids = []
    for item in response['items']:
        pid = item['id']

        playlist_ids.append(pid)
    return playlist_ids

def parse_track_info(response):
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

# Needs grouped df
def recommend(user_id, sparse_user_artist, user_vecs, artist_vecs, grouped_df, num_contents=10):
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
    recommendations = pd.DataFrame({'artist_name': artists, 'score': scores})
    return recommendations

def get_top_recommended_tracks(artist_list, sp):
    top_list = []
    for artist in artist_list:
        uri = sp.search(artist)['tracks']['items'][0]['album']['artists'][0]['uri']
        top_tracks = sp.artist_top_tracks(uri)
        for track in top_tracks['tracks'][:5]:
            top_list.append(track['name'])
    return top_list
    