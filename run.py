import sys
import json
import os
import pandas as pd
import requests
from collections import defaultdict


# Custom Library Imports
from src.build_lib.billboard_build import billboard




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
    
        

    if 'load-data' in targets:

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

    if 'clean_data' in targets:
        pass

    if 'task1' in targets:

        print("------------------------- GENERATING RECOMMENDATIONS BASED ON CONFIG -------------------------")

        # Create billboard client
        print('Creating list of recommended songs')
        billboard_recommender = billboard()
        song_recommendations = billboard_recommender.getList(startY=2010, endY=2020, genre=['electronica'])

        print('Saving list of recommended songs')
        # Save to csv
        pd.DataFrame({'song_recommendations': song_recommendations}).to_csv(os.path.join(DATA_DIR_RECOMMENDATIONS, 'song_recs.csv'))
    
    if 'task2' in targets:
        pass

    if 'all' in targets:
        pass




if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)