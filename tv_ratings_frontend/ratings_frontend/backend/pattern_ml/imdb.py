from imdb import IMDb
from imdbpie import Imdb
from pymongo import MongoClient
from pytvdbapi import api
from time import sleep
import os
import sys

# get episode links with imdbPy
# get reviews with imdbpie


# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
# imdb = Imdb(cache=True)
# Specify optional cache directory, the default is '/tmp/imdbpiecache'
# imdb = Imdb(cache=True, cache_dir='/tmp/imdbpiecache/')
class ImdbClient:
    def __init__(self):
        self.imdbpy = IMDb()
        self.imdb = Imdb(exclude_episodes=False)
        self.imdb = Imdb(anonymize=True)  # to proxy requests
        self.db = api.TVDB('B43FF87DE395DF56')

    def readFromMongo(self, show, limit):
        # Connect to mongo
        client = MongoClient()

        # access movie stream db
        movies = client['movieratings_stream']

        # colletion of tweets
        tweets = movies['tweets']

        tweet_text = []
        counter = 0

        # iterate through cursor that takes the 'limit' most recent tweets with hashtag 'show'
        for tweet in tweets.find({'show_title': show}):  # .sort('created_at', pymongo.DESCENDING):
            if counter < limit:
                tweet_text.append(tweet.get("tweet_text"))
                counter += 1
            else:
                break
        return tweet_text

    def getTitle(self, show_title):
        m = self.imdbpy.get_movie('0389564')  # The 4400.
        m['kind']    # kind is 'tv series'.
        self.imdbpy.update(m, 'episodes')   # retrieves episodes information.

        m['episodes']    # a dictionary with the format:
                       #    {#season_number: {
                       #                      #episode_number: Movie object,
                       #                      #episode_number: Movie object,
                       #                      ...
                       #                     },
                       #     ...
                       #    }
                       # season_number always starts with 1, episode_number
                       # depends on the series' numbering schema: some series
                       # have a 'episode 0', while others starts counting from 1.

        m['episodes'][1][1] # <Movie id:0502803[http] title:_"The 4400" Pilot (2004)_>

        e = m['episodes'][1][2]  # second episode of the first season.
        e['kind']    # kind is 'episode'.
        e['season'], e['episode']   # return 1, 2.
        e['episode of']  # <Movie id:0389564[http] title:_"4400, The" (2004)_>
                       # XXX: beware that e['episode of'] and m _are not_ the
                       #      same object, while both represents the same series.
                       #      This is to avoid circular references; the
                       #      e['episode of'] object only contains basics
                       #      information (title, movieID, year, ....)
        i.update(e)  # retrieve normal information about this episode (cast, ...)

        e['title']  # 'The New and Improved Carl Morrissey'
        e['series title']  # 'The 4400'
        e['long imdb episode title']  # '"The 4400" The New and Improved Carl Morrissey (2004)'


        # print(show_title)
        # sleep(3)
        # title_list = list(self.imdb.search_for_title(show_title))
        # print(list(self.imdb.search_for_title("Days Gone Bye The Walking Dead")))
        # print(title_list)
        # sleep(3)
        # index = 0
        # show_id = None

        # while show_id is None:
        #     print ("title_list", title_list[index][u'title'])
        #     print ("show title", show_title)
        #     result = title_list[index][u'title'].lower()
        #     query = show_title.lower()
        #     if result in query:
        #         print title_list
        #         show_id = title_list[index][u'imdb_id']
        #         # endless loop
        #     index += 1
        # return show_id

    def searchShow(self, tvshow):
        print tvshow
        title_id = self.getTitle(tvshow)
#        if tvshow is not self.tvshow:
        print title_id
        print tvshow
       # print('title: ', title_id)
        reviews = self.imdb.get_title_reviews(title_id, max_results=sys.maxint)
        title = self.imdb.get_title_by_id(title_id)
        print title_id
        print tvshow
       # print("title: " + str(title.data))
       # print len(reviews)
        return reviews

    def getCurrentImdbRating(self, tvshow):
        tvshowid = self.getTitle(tvshow)
        title = self.imdb.get_title_by_id(tvshowid)
        return float(title.rating)

    def get_all_episode_names(self, tvshow):
        result = self.db.search(tvshow, 'en')
        show = result[0]
        res = []
        for x in range(1, len(show)):
            season = show[x]
            for y in range(1, len(season) + 1):
                if season[y].EpisodeName is not None:
                    res.append(season[y].EpisodeName)
        return res

    def get_specific_episode_names(self, tvshow, season):
        result = self.db.search(tvshow, 'en')
        show = result[0]
        res = []
        season = show[1]
        for x in range(1, len(season) + 1):
            if season[x].EpisodeName is not None:
                print season[x].EpisodeName
                res.append(season[x].EpisodeName)
        return res

    def get_all_episodes(self, episodelist, tvshow):
        for episode in episodelist:
            currEpisode = episode + " " + tvshow
            reviews = []
            reviews.append(searchshow(currEpisode))
        #call searchshow for each

# get list of all episode names given a tv show
# create review list, for each episode name, call searchshow append
# call method that trains