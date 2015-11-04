
import imdb
from twitter_sentiment_analysis import SentimentAnalysis

if __name__ == '__main__':

    shows = ["Big bang Theory","Walking Dead","South Park","American Horror Story","Modern Family","Heroes Reborn","Family Guy","Arrow"]
    sample_size =100

    sa = SentimentAnalysis()
    ia = imdb.IMDb()

    s_result = ia.search_movie(shows[0])

    '''
    for show in shows:
        #print sa.readFromMongo(show,sample_size)
        s_result = ia.search_movie(show)

        #for item in s_result:
        #   print item['long imdb canonical title'], item['runtime'] , iterm['rating']

        the_unt = s_result[0]
        ia.update(the_unt)
        print the_unt['runtime']
        print the_unt['rating']
    '''
