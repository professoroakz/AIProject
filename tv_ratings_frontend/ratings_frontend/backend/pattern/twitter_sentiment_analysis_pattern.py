from pattern.vector import Document, NB
from pattern.db import csv
from imdbpie import Imdb
from pymongo import MongoClient
import sys


imdb = Imdb()
imdb = Imdb(anonymize=True)  # to proxy requests


# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
# imdb = Imdb(cache=True)
# Specify optional cache directory, the default is '/tmp/imdbpiecache'
# imdb = Imdb(cache=True, cache_dir='/tmp/imdbpiecache/')

nb = NB()

def getTitle(show_title):
    title_list = list(imdb.search_for_title(show_title))
    index = 0
    show_id = None

    while show_id is None:
        if title_list[index][u'title'] == show_title:
            show_id = title_list[index][u'imdb_id']
        index += 1

    return show_id


def searchShow(tvshow):
    title_id = getTitle(tvshow)
    print('title: ', title_id)
    reviews = imdb.get_title_reviews(title_id, max_results=sys.maxint)
    # print(reviews[0].text)
    print len(reviews)
    return reviews


def naive_bayes_train(reviews):

    for review in reviews:
        if review.rating is not None:
            v = Document(review.text, type=int(review.rating), stopwords=True)
            nb.train(v)
    print nb.classes

def nb_test_imdb(reviews):
    list = []
    for review in reviews:
        if review.rating is not None:
            v = Document(review.text, type=int(review.rating), stopwords=True)
            list.append(v)
    print nb.test(list, target=None)

def nb_test_tweets(tweets):
    list = [Document(tweet, stopwords=True) for tweet in tweets]
    print nb.test(list, target=None)



def readFromMongo(show, limit):
    # endpoint: 107.170.228.84, 223947lts488
    # Connect to mongo
    client = MongoClient('107.170.228.84:81', '223947lts488')

    # access movie stream db
    movies = client['movieratings_stream']

    # colletion of tweets
    tweets = movies['tweets']

    tweet_text = []
    counter = 0

    # iterate through cursor that takes the 'limit' most recent tweets with hashtag 'show'
    for tweet in tweets.find({'show_title': show}):  # .sort('created_at', pymongo.DESCENDING):
        if counter < limit:
            tweet_text.append(tweet)
            counter += 1
        else:
            break
    return tweet_text



reviews = searchShow("The Walking Dead")
naive_bayes_train(reviews)

bbtReviews = searchShow("The Big Bang Theory")

nb_test_imdb(bbtReviews)

nb_test_tweets(readFromMongo("The Walking Dead", 500))
