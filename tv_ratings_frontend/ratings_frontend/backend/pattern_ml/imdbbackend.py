from imdb import IMDb
from imdbpie import Imdb
from pymongo import MongoClient
from pytvdbapi import api
from fuzzywuzzy import fuzz
import sys


# get episode links with imdbPy
# get reviews with imdbpie

# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
# imdb = Imdb(cache=True)
# Specify optional cache directory, the default is '/tmp/imdbpiecache'
# imdb = Imdb(cache=True, cache_dir='/tmp/imdbpiecache/')

# TODO create tv show class, save all ids for each episode


class ImdbClient:
    def __init__(self):
        self.imdbpy = IMDb()
        self.imdb = Imdb(exclude_episodes=False)
        self.imdb = Imdb(anonymize=True)  # to proxy requests
        self.db = api.TVDB('B43FF87DE395DF56')

    def readFromMongo(self, show, limit):
        # Connect to mongo
        client = MongoClient()

        # access movRie stream db
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

    def getEpisodeReviews(self, episode_name):
        return self.searchShow(episode_name)

    def get_show_id(self, show_title):
        title_list = list(self.imdb.search_for_title(show_title))
        index = 0
        show_id = None

        while index < len(title_list) and show_id is None:
            if title_list[index] is not None:
                result = title_list[index][u'title'].lower()
                query = show_title.lower()
                # if result in query:
                if fuzz.ratio(result, query) >= 90:
                    # print title_list
                    show_id = title_list[index][u'imdb_id']
            index += 1
        return show_id

    def searchShow(self, tvshow):
        title_id = self.get_show_id(tvshow)
        reviews = []
        print(tvshow)

        if title_id is not None and title_id != '':
            reviews = self.imdb.get_title_reviews(title_id, max_results=sys.maxint)
            title = self.imdb.get_title_by_id(title_id)
        else:
            print("Invalid show id")

        return reviews

    def getCurrentImdbRating(self, tvshow):
        tvshowid = self.get_show_id(tvshow)
        title = self.imdb.get_title_by_id(tvshowid)
        return float(title.rating)

    def get_all_episode_names(self, tvshow):
        result = self.db.search(tvshow, 'en')
        show = result[0]
        res = []
        for x in range(1, len(show)):
            season = show[x]
            for y in range(1, len(season) + 1):
                if season[y].EpisodeName is not None and season[y].EpisodeName != '':
                    res.append(season[y].EpisodeName)
        return res

    # episode names for a specific season of tvshow
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

    def get_all_episode_reviews(self, episodelist, tvshow):
        reviews = []
        for episode in episodelist:
            curEpisode = episode + " " + tvshow
            reviews.append(self.searchShow(curEpisode))
            # call searchshow for each

        print("Episodes:\n" + str(reviews))
        return reviews


# get list of all episode names given a tv show
# create review list, for each episode name, call searchshow append
# call method that trains

class TVShow:
    def __init__(self, show_title):
        self.client = ImdbClient()
        self.title = show_title
        self.show_id = None
        self.episodes = None

    def _get_episodes(self):
        if self.episodes is None:
            self.episodes = self.client.get_all_episode_names(self.title)
        return self.episodes

    def get_show_reviews(self):
        return self.client.searchShow(self.title)

    def get_all_episode_reviews(self):
        reviews = {}
        for episode in self._get_episodes():
            reviews[episode] = self.get_episode_reviews(episode)
        return reviews

    def get_episode_reviews(self, episode_name):
        return self.client.searchShow(episode_name)

if __name__ == "__main__":
    tv = TVShow("The Walking Dead")
    tv.get_all_episode_reviews()