from pattern.vector import Document, NB
from pattern.db import csv
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
        self.imdb = Imdb()
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
        print('title: ', title_id)
        reviews = self.imdb.get_title_reviews(title_id, max_results=sys.maxint)
        # print(reviews[0].text)
        print len(reviews)
        return reviews


class NBModel:
    def __init__(self):
        self.nb = NB()
        self.stats = Statistics()
        try:
            self.nb = self.nb.load("./nb_training.p")
            self.new_nb_model = True
        except IOError:
            self.new_nb_model = False
            print("Creating new NB model")

    def naive_bayes_train(self, reviews):
        for review in reviews:
            if review.rating is not None:
                v = Document(review.text, type=int(review.rating), stopwords=True)
                self.nb.train(v)
        self.nb.save("./nb_training.p")
        print self.nb.classes

    def nb_test_imdb(self, reviews):
        arr = []
        for review in reviews:
            if review.rating is not None:
                v = Document(review.text, type=int(review.rating), stopwords=True)
                arr.append(v)
        print self.nb.test(arr, target=None)

    def nb_classify_tweets(self, tweets):
        ratingSum = 0
        tweet_docs = [(self.nb.classify(Document(tweet)), tweet) for tweet in tweets]
        for tweet in tweet_docs:
            ratingSum += tweet[0]
            print tweet
        # print("Doc[0] ", tweet_docs[0])
        print("num documents: ", len(tweet_docs))
        self.stats.printStats(ratingSum, len(tweet_docs))

class Statistics:
    def printStats(self, sum, numItems):
        print("---------- Statistics -----------")
        print("Sum of the ratings from Twitter: ", sum)
        print("Number of classified ratings: ", numItems)
        print("Average value: ", float(sum)/numItems)


def main():
    client = ImdbClient()
    nb = NBModel()

    if nb.new_nb_model:
        reviews = client.searchShow("The Walking Dead")
        nb.naive_bayes_train(reviews)

    bbtReviews = client.searchShow("The Big Bang Theory")

    # nb_test_imdb(bbtReviews)

    nb.nb_classify_tweets(client.readFromMongo("Walking Dead", 5000))
    nb.nb_classify_tweets(client.readFromMongo("Big bang Theory", 5000))


if __name__ == "__main__":
    main()
