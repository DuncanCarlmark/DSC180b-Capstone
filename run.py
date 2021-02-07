import sys
import json
import os
import math
import boto3
from collections import defaultdict

os.environ["AWS_ACCESS_KEY_ID"] = "AKIAIIVZBLJTALI6RFJQ"
os.environ["AWS_SECRET_ACCESS_KEY"] = "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"



# Paths for storing data
DATA_DIR = 'data'
DATA_DIR_RAW = os.path.join(DATA_DIR, 'raw')
DATA_DIR_CLEAN = os.path.join(DATA_DIR, 'clean')

USER_PROFILE = os.path.join(DATA_DIR_RAW, 'usersha1-profile.tsv')
USER_ARTIST = os.path.join(DATA_DIR_RAW, 'usersha1-artmbid-artname-plays.tsv')



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
            print('Data directory files created')


        # Load data if necessary

        print("DOWNLOADING TRAINING DATA")
        if os.path.isfile(USER_PROFILE) and os.path.isfile(USER_ARTIST):
            print("Data files already exist. Skipping download.")

        else:
            s3 = boto3.resource('s3')
            s3.Bucket('capstone-raw-data').download_file('usersha1-profile.tsv', USER_PROFILE)
            s3.Bucket('capstone-raw-data').download_file('usersha1-artmbid-artname-plays.tsv', USER_ARTIST)

            print("All data files downloaded")
        
        

            

        

        

    if 'clean_data' in targets:
        pass

    if 'task1' in targets:
        pass
    
    if 'task2' in targets:
        pass

    if 'all' in targets:
        pass




if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)