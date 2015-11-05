import pandas as pd
import nltk
from numpy import *
import re
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
import timeit
import itertools
import sys
import pickle
import pymongo
from pymongo import MongoClient


class SentimentAnalysis():
    # model needs to be a model from sklearn or obj with function that can predict
    # right now model = random forest, features = bag of words
    def sentiment(self, model, features):

        sent = model.predict(features)

        total = sent.shape[0]

        prop_pos = sum(sent) / total
        prop_neg = 1 - prop_pos

        return prop_pos, prop_neg, total

    # vectorizer is something we learn at training time
    # includes vocab and other things
    # tweets - a list
    def process_raw_tweet(self, vectorizer, tweets):

        test_data_features = vectorizer.transform(tweets)
        test_data_features = test_data_features.toarray()
        return test_data_features

    # Reads and Cleans  'n' tweets from corpus so we don't need to read everything
    # each time we train
    def extract_features(self, path, n):
        print
        "Loading Data..."
        train = pd.read_csv("training.1600000.processed.noemoticon.csv", header=None, \
                            delimiter='","', quoting=3, engine='python')
        print
        "Finished Loading!!!"

        # Collect clean review for both positive and negative as well as training and test
        clean_train_reviews_neg = []
        clean_train_reviews_pos = []

        clean_test_reviews_neg = []
        clean_test_reviews_pos = []

        for i in range(n):
            clean_train_reviews_neg.append(review_to_words(train[5][i]))
            clean_test_reviews_neg.append(review_to_words(train[5][i + n]))

            clean_train_reviews_pos.append(review_to_words(train[5][i + 800000]))
            clean_test_reviews_pos.append(review_to_words(train[5][i + 800000 + n]))

            if i % 10000 == 0:
                print
                i


                # Write everything to csv
        pos_output = pd.DataFrame(data=clean_train_reviews_pos)
        neg_output = pd.DataFrame(data=clean_train_reviews_neg)

        test_pos_output = pd.DataFrame(data=clean_test_reviews_pos)
        test_neg_output = pd.DataFrame(data=clean_test_reviews_neg)

        pos_output.to_csv(path + "pos_tweets_train.csv", index=False)
        neg_output.to_csv(path + "neg_tweets_train.csv", index=False)

        test_pos_output.to_csv(path + "pos_tweets_test.csv", index=False)
        test_neg_output.to_csv(path + "neg_tweets_test.csv", index=False)

    # Cleans up a tweet - review is from when this was for IMDB
    def review_to_words(self, raw_review):

        no_url = re.sub("http[s]??://.+?\\..+?[ ]?", "", raw_review)

        # Remove numerics
        letters_only = re.sub("[^a-zA-Z]", " ", no_url)

        # to lowercase
        words = letters_only.lower().split()

        # remove stop words - the, of , a ....
        stops = set(stopwords.words("english"))

        meaningful_words = [w for w in words if not w in stops]

        return (" ".join(meaningful_words))

    # predict is a funtion object that will predict sentiment
    def test_model(self, path, n, predict, vectorizer):

        print
        "Loading Test Data..."
        test_pos = pd.read_csv(path + "pos_tweets_test.csv", header=0, \
                               delimiter=',', quoting=3, engine='python')

        test_neg = pd.read_csv(path + "neg_tweets_test.csv", header=0, \
                               delimiter=',', quoting=3, engine='python')

        test = pd.concat([test_pos.iloc[0:n], test_neg.iloc[0:n]])

        print
        "Test data finished loading !"
        print
        "Processing Features ... "

        test_data_features = vectorizer.transform(test['0'].values.tolist())
        test_data_features = test_data_features.toarray()
        i = 0
        errors = 0
        for tweet in test_data_features:
            sentiment = predict(tweet)
            if i < n:
                if sentiment != 1:
                    errors = errors + 1
            else:
                if sentiment != 0:
                    errors = errors + 1

            i = i + 1

        print
        "Percent Correct:   " + str(float((i - errors)) / i)

    def sentiment_analysis(self, path, n, k):
        print
        "Loading Data"
        train_pos = pd.read_csv(path + "pos_tweets_train.csv", header=0, \
                                delimiter=',', quoting=3, engine='python')

        train_neg = pd.read_csv(path + "neg_tweets_train.csv", header=0, \
                                delimiter=',', quoting=3, engine='python')

        vectorizer = CountVectorizer(analyzer="word", \
                                     tokenizer=None, \
                                     preprocessor=None, \
                                     stop_words=None, \
                                     max_features=k)

        print
        "Finished Loading!!!"

        print
        "Processing Bag of Word Features"
        train = pd.concat([train_pos.iloc[0:n], train_neg.iloc[0:n]])
        sentiment = zeros(2 * n)
        sentiment[0:n] = 1

        train_data_features = vectorizer.fit_transform(train['0'].values.tolist())
        train_data_features = train_data_features.toarray()

        print
        "Beginning Training"
        start = timeit.default_timer()

        forest = RandomForestClassifier(n_estimators=50)
        forest = forest.fit(train_data_features, sentiment)

        stop = timeit.default_timer()

        print
        "Training Finished!!! Total Time:  " + str(stop - start)

        return forest, vectorizer

    # show - a string of the name of the show
    # limit - how many tweets to pull
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
                tweet_text.append(tweet)
                counter += 1
            else:
                break

        model = pickle.load(open("/root/random_forest.p", "rb"))
        vectorizer = pickle.load(open("/root/vectorizer.p", "rb"))

        cleaned_tweets = self.process_raw_tweet(vectorizer,
                                                [self.review_to_words(tweet['tweet_text']) for tweet in tweet_text])

        return self.sentiment(model, cleaned_tweets)


if __name__ == '__main__':
    # DataFrame Structure for the trianingf file
    # 0 - sentiment value
    # 1 - id
    # 2 - date
    # 3 - NO_QUERY ?
    # 4 - person who tweeted
    # 5 - Actual tweet

    # path = "/Users/zachzhang/DeepLearningTutorials/KaggleWarmUp/data/"
    # n = 1000
    # k = 2000
    # extract_features(path,n)
    # [model,vectorizer] = sentiment_analysis(path,n,k)
    # test_model(path,n,model.predict,vectorizer)
    show = 'American Horror Story'
    limit = 1000
    sa = SentimentAnalysis()
    sa.readFromMongo(show, limit)
