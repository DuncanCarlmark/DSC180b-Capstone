import pandas as pd
import numpy as np
import datetime

class billboard:
    def __init__(self):
        #features = pd.read_csv('Hot 100 Audio Features.csv')
        features = pd.read_excel('https://query.data.world/s/2hymngpmogoje5bwt3ikufdxjdgkn3')
        # only include tracks that have a spotify id on file for now
        self.features = features[~features['spotify_track_id'].isnull()][features.columns[0:5]].drop_duplicates()

        #stuff = pd.read_csv('Hot Stuff.csv')
        stuff = pd.read_csv('https://query.data.world/s/go22golrhaeqllglpuxnnd7irb3l2j')
        stuff['WeekID'] = pd.to_datetime(stuff['WeekID'])
        self.stuff = stuff

    def weeklyAvg(self):
        # average weekly position
        avg_pos = self.stuff[['WeekID', 'Week Position', 'SongID']].groupby(by=['SongID']).mean()
        # first week the track appeared in the chart
        minweek = self.stuff[['WeekID', 'SongID']].groupby(by=['SongID']).min().rename(columns={'WeekID':'firstWeekID'})
        # last week the track appeared in the chart
        maxweek = self.stuff[['WeekID', 'SongID']].groupby(by=['SongID']).max().rename(columns={'WeekID':'lastWeekID'})
        # total # of weeks the track was in the chart
        max_occ = self.stuff[['SongID','Instance','Weeks on Chart']].groupby(by=['SongID']).max()

        stats = avg_pos.join(minweek).join(maxweek).join(max_occ)
        self.data = self.features.join(stats, on='SongID').rename(columns={'Week Position':'Avg Weekly'})

    def getList(self, how='avg', length=50, lowerY=2019, lowerM=1, lowerD=1, upperY=2019, upperM=12, upperD=31):
        # songs should have entered chart before upper bound (e.g. 2019 songs should have been on chart before 2019/12/31)
        lowerBound = datetime.datetime(lowerY, lowerM, lowerD)
        # songs should have left chart after lower bound (e.g. 2019 songs should still be on chart after 2019/1/1)
        upperBound = datetime.datetime(upperY, upperM, upperD)

        #if how == ''  ; implement later for other possible ranking methods
        self.weeklyAvg()

        data = self.data
        filtered = data[(data['firstWeekID'] < upperBound) & (data['lastWeekID'] > lowerBound)]
        filtered = filtered.sort_values(['Instance','Avg Weekly','Weeks on Chart'], ascending=[True,True,False]).reset_index(drop=True)
        return filtered[:length]