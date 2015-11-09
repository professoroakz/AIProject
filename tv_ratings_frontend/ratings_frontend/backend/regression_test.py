
import imdb
from twitter_sentiment_analysis import SentimentAnalysis
from sklearn import linear_model
from numpy import *

def regression_model(shows,sample_size):
    #shows = ["Big bang Theory","Walking Dead","South Park","American Horror Story","Modern Family","Heroes Reborn","Family Guy","Arrow"]
    #sample_size =10000
    sa = SentimentAnalysis()
    ia = imdb.IMDb()
    model = linear_model.LinearRegression()

    ratings = []
    sentiment = []
    for show in shows:
        s_result = ia.search_movie(show)
        episode = s_result[0]
        ia.update(episode)

        sent = sa.readFromMongo(show,sample_size)

        print(sent)
        ratings.append(episode['rating'])
        sentiment.append([ sent[0], sent[1] ])

    ratings = array(ratings)
    sentiment = array(sentiment)

    model.fit(sentiment, ratings)
    print(model.score(sentiment,ratings))

if __name__ == '__main__':
    shows = ["Big bang Theory","Walking Dead","South Park","American Horror Story","Modern Family","Heroes Reborn","Family Guy","Arrow"]
    sample_size =10000

    regression_model(shows,sample_size)

