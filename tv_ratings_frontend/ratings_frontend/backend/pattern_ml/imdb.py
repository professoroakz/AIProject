from imdbpie import Imdb
from pymongo import MongoClient
import sys


# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
# imdb = Imdb(cache=True)
# Specify optional cache directory, the default is '/tmp/imdbpiecache'
# imdb = Imdb(cache=True, cache_dir='/tmp/imdbpiecache/')
class ImdbClient:
    def __init__(self):
        self.imdb = Imdb(exclude_episodes=False)
        self.imdb = Imdb(anonymize=True)  # to proxy requests

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
        title_list = list(self.imdb.search_for_title(show_title))
        index = 0
        show_id = None

        while show_id is None:
            if title_list[index][u'title'] == show_title:
                show_id = title_list[index][u'imdb_id']
            index += 1

        return show_id

    def searchShow(self, tvshow):
        title_id = self.getTitle(tvshow)
       # print('title: ', title_id)
        reviews = self.imdb.get_title_reviews(title_id, max_results=sys.maxint)
        title = self.imdb.get_title_by_id(title_id)
       # print("title: " + str(title.data))
       # print len(reviews)
        return reviews

    def getCurrentImdbRating(self, tvshow):
        tvshowid = self.getTitle(tvshow)
        title = self.imdb.get_title_by_id(tvshowid)
        return float(title.rating)

    def _get_episode(self, tvshow, episode_title):
        pass

    # get list of all episodes

    def get_all_episodes(self, tvshow):
        pass

# get list of all episode names given a tv show
# create review list, for each episode name, call searchshow append
# call method that trains