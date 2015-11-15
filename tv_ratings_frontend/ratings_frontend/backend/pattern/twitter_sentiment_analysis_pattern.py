# from pattern.vector import Document, NB
# from pattern.db import csv

# nb = NB()
# for review, rating in csv('reviews.csv'):
#     v = Document(review, type=int(rating), stopwords=True)
#     nb.train(v)

# print nb.classes
# print nb.classify(Document('A good movie!'))

from imdbpie import Imdb
imdb = Imdb()
imdb = Imdb(anonymize=True) # to proxy requests

# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
#imdb = Imdb(cache=True)
# Specify optional cache directory, the default is '/tmp/imdbpiecache'
#imdb = Imdb(cache=True, cache_dir='/tmp/imdbpiecache/')


def searchShow(tvshow):
    title = imdb.search_for_title(tvshow)
   # titleId = title.imdb_id
   # print imdb.get_title_reviews(titleId, max_results=15)

searchShow("The Walking Dead")

#print imdb.get_title_reviews("The Walking Dead", max_results=15)

