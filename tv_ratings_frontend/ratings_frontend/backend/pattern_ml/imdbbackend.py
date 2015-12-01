from imdb import IMDb
from imdb import utils as util
from imdbpie import Imdb
from pymongo import MongoClient
from pytvdbapi import api
from fuzzywuzzy import fuzz
import sys
from datetime import datetime, date, timedelta

TWEETS_DB = 'movieratings_stream'
TWEETS = 'tweets'
TV_SHOW_DB = 'tv_show_reviews'
SHOW_REVIEWS_COLLECTION = 'show_reviews'
EPISODE_REVIEWS_COLLECTION = 'episode_reviews'
SHOWS_COLLECTION = 'shows'


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

    def get_tweets_from_mongo(self, show, limit):
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

    # TODO: get rid of usage of this
    def searchShow(self, tvshow):
        title_id = self.get_show_id(tvshow)
        print(title_id)
        reviews = []
        print(tvshow)

        if title_id is not None and title_id != '':
            reviews = self.imdb.get_title_reviews(title_id, max_results=sys.maxint)
            print reviews
        else:
            print("Invalid show id")

        return reviews

    def fetch_reviews(self, episode_id):
        reviews = self.imdb.get_title_reviews(episode_id, max_results=sys.maxint)

        return reviews

    def getCurrentImdbRating(self, tvshow):
        tvshowid = self.get_show_id(tvshow)
        title = self.imdb.get_title_by_id(tvshowid)
        return float(title.rating)

    # dont use this, use example from
    # http://imdbpy.sourceforge.net/docs/README.series.txt
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

    def get_show(self, show_id):
        show = self.imdbpy.get_movie(show_id.replace('t', ''))
        self.imdbpy.update(show, 'episodes')
        print("show_show(" + show_id + "): " + str(show))

        return show

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


class MovieMongo:
    def __init__(self):
        self.mongo = MongoClient()

    def save_show(self, show_title, episodes_data, show_reviews):
        try:
            print("Saving show: " + show_title)
            review_db = self.mongo[TV_SHOW_DB]
            episode_review_ids = self._save_episode_reviews(episodes_data, show_title)
            overall_review_ids = self._save_show_reviews(show_title, show_reviews)
            review_db[SHOWS_COLLECTION].save({
                'show_title': show_title,
                'episode_review_ids': episode_review_ids,
                'overall_review_ids': overall_review_ids
            })
        except RuntimeError:
            print('Error saving episodes for ' + show_title)

    def _save_show_reviews(self, show_title, reviews):
        review_indices = []

        try:
            show_db = self.mongo[TV_SHOW_DB]
            reviews_db = show_db[SHOW_REVIEWS_COLLECTION]
            index = reviews_db.count()
            for review in reviews:
                review_indices.append(index)
                reviews_db.save({
                    'id': index,
                    'show_title': show_title,
                    'text': review.text,
                    'summary': review.summary,
                    'rating': review.rating,
                    'date': review.date,
                    'username': review.username,
                    'status': review.status,
                    'user_location': review.user_location,
                    'user_score': review.user_score,
                    'user_score_count': review.user_score_count})
                index += 1
        except RuntimeError:
            print('Error saving show reviews for {0}'.format(show_title))

        return review_indices

    def _save_episode_reviews(self, episodes, show_title):
        review_indices = []

        try:
            review_db = self.mongo[TV_SHOW_DB]
            for episode in episodes:
                for review in episode[EPISODE_REVIEWS_COLLECTION]:
                    index = review_db[EPISODE_REVIEWS_COLLECTION].count()

                    review_indices.append(index)
                    review_db[EPISODE_REVIEWS_COLLECTION].save({
                        'id': index,
                        'show_title': show_title,
                        'episode_title': episode['title'],
                        'text': review.text,
                        'summary': review.summary,
                        'rating': review.rating,
                        'date': review.date,
                        'username': review.username,
                        'status': review.status,
                        'user_location': review.user_location,
                        'user_score': review.user_score,
                        'user_score_count': review.user_score_count})
        except RuntimeError:
            print('Error saving episode reviews for {0}'.format(show_title))

        return review_indices

    def get_show(self, show_title):
        db = self.mongo[TV_SHOW_DB]
        shows = db[SHOWS_COLLECTION]
        query = shows.find({'show_title': show_title})
        results = [result for result in query]

        if len(results) > 0:
            show = results[0]
        else:
            print('no show returned from mongo for {0}'.format(show_title))
            show = None
        # print("db returned: " + str(show))
        return show

    def get_overall_reviews(self, show_title):
        show = self.get_show(show_title)
        review_ids = show['overall_review_ids']
        show_db = self.mongo[TV_SHOW_DB]
        reviews_collection = show_db[SHOW_REVIEWS_COLLECTION]
        reviews = []

        for review_id in review_ids:
            new_review = reviews_collection.find({'id': review_id})[0]
            reviews.append(MovieReview.create_from_mongo(new_review))

        return reviews

    def get_episode_reviews(self, show_title):
        show = self.get_show(show_title)
        review_ids = show['episode_review_ids']
        reviews = {}
        show_db = self.mongo[TV_SHOW_DB]
        reviews_collection = show_db[EPISODE_REVIEWS_COLLECTION]

        for review_id in review_ids:
            new_review = reviews_collection.find({'id': review_id})[0]
            reviews[new_review['episode_title']] = MovieReview.create_from_mongo(new_review)

        return reviews

    # dates must be datetime objects
    def get_tweets_in_range(self, show_title, start_date, end_date):
        print('Retrieving tweets for {0} from {1} to {2}'.format(show_title, start_date, end_date))
        tweets_collection = self.mongo[TWEETS_DB][TWEETS]
        tweets = tweets_collection.find({
            'show_title': show_title,
            'created_at': {
                '$gte': start_date,
                '$lte': end_date
            }
        })
        return [tweet for tweet in tweets]


# get list of all episode names given a tv show
# create review list, for each episode name, call searchshow append
# call method that trains
# TODO: Incorporate reading tweets for this show into class functionality (Imdbclient.readShowFromMongo)

class TVShow:
    def __init__(self, show_title):  # option for tvepisode boolean yes or no
        self.client = ImdbClient()
        self.title = show_title
        self.show_id = self.client.get_show_id(show_title).replace('t', '')
        self.episodes = None
        self.movie_mongo = MovieMongo()

    def __str__(self):
        return '<TVReview title: \'{0}\' id: {1}>'.format(self.title, self.show_id)

    @staticmethod
    def parse_show(show_title):
        lower_show = show_title.lower()
        possible_shows = ['Walking Dead', \
                          'Arrow', \
                          'Family Guy', \
                          'Big bang Theory', \
                          'South Park', \
                          'American Horror Story', \
                          'Modern Family', \
                          'Heroes Reborn']
        if 'walking' in lower_show or 'dead' in lower_show:
            return possible_shows[0]
        elif lower_show == 'arrow':
            return possible_shows[1]
        elif lower_show == 'family guy' or 'guy' in lower_show:
            return possible_shows[2]
        elif 'big' in lower_show or 'bang' in lower_show or 'theory' in lower_show:
            return possible_shows[3]
        elif 'south' in lower_show or 'park' in lower_show:
            return possible_shows[4]
        elif 'american' in lower_show or 'horror' in lower_show or 'story' in lower_show:
            return possible_shows[5]
        elif 'modern' in lower_show:
            return possible_shows[6]
        elif 'heroes' in lower_show or 'reborn' in lower_show:
            return possible_shows[7]

        return 'undertermined'

    def _get_episodes(self):
        if self.episodes is None:
            self.episodes = list()
            show = self.movie_mongo.get_show(self.title)

            if show is None:
                show = self.client.get_show(self.show_id)
                episode_collection = show['episodes']

                for season in episode_collection:
                    for episode in episode_collection[season]:
                        self.episodes.append(episode_collection[season][episode])
            else:
                self.episodes = show['episodes']
        return self.episodes

    # returns a list of reviews for the entire show
    def get_show_reviews(self):
        show = self.movie_mongo.get_show(self.title)

        if show is None:
            self._fetch_reviews()

        return self.movie_mongo.get_overall_reviews(self.title)

    # returns a mapping of episodes to their reviews
    def get_all_episode_reviews(self):
        show = self.movie_mongo.get_show(self.title)

        if show is None:
            self._fetch_reviews()

        return self.movie_mongo.get_episode_reviews(self.title)

    # fetch reviews from IMDB
    def _fetch_reviews(self):
        print('Fetching reviews from IMDB for {0}'.format(self.title))
        show_reviews = self._get_reviews(self.show_id)

        episode_reviews = {}
        episodes = self._get_episodes()
        episode_data = []
        index = 0
        for episode in episodes:
            episode_reviews[episode['title']] = self._get_reviews(IMDb().get_imdbID(episode))
            if episode_reviews[episode['title']] is not None:
                episode_data.append({'title': episode['title'],
                                     EPISODE_REVIEWS_COLLECTION: [
                                         review for review in episode_reviews[episode['title']]
                                         if review is not None]})
            else:
                print('No reviews for episode {0} in show: {1}'.format(episode, self.title))
            index += 1

        self.movie_mongo.save_show(self.title, episode_data, show_reviews)

    def _get_reviews(self, show_id):
        imdb_reviews = self.client.fetch_reviews('tt' + str(show_id))
        reviews = None
        if imdb_reviews is not None:
            reviews = [MovieReview(review) for review in imdb_reviews if review is not None]
        else:
            print('No reviews found for {0}, episode: {1}'.format(self.title, show_id))
        return reviews

    def get_all_tweets(self, limit=sys.maxint):
        return self.client.get_tweets_from_mongo(TVShow.parse_show(self.title), limit)

    # retrieves a sample of the last days_back days of tweets
    def sample_recent_tweets(self, days_back):
        now = datetime.utcnow()
        three_days_ago = now - timedelta(days=days_back)
        tweets = self.movie_mongo.get_tweets_in_range(
            TVShow.parse_show(self.title), three_days_ago, now)
        return tweets


class MovieReview:
    def __init__(self, imdb_review=None, from_mongo=False):
        if not from_mongo:
            try:
                self.show_title = imdb_review.show_title
            except AttributeError:
                pass
            self.username = imdb_review.username
            self.text = imdb_review.text
            self.date = imdb_review.date
            self.rating = imdb_review.rating
            self.summary = imdb_review.summary
            self.status = imdb_review.status
            self.user_location = imdb_review.user_location
            self.user_score = imdb_review.user_score
            self.user_score_count = imdb_review.user_score_count

    def __str__(self):
        return str(self.username) + ', ' + str(self.rating) + ', ' + str(self.text)

    @staticmethod
    def create_from_mongo(review):
        new_review = MovieReview(from_mongo=True)
        try:
            new_review.show_title = review['show_title']
        except AttributeError:
            pass
        new_review.username = review['username']
        new_review.text = review['text']
        new_review.date = review['date']
        new_review.rating = review['rating']
        new_review.summary = review['summary']
        new_review.status = review['status']
        new_review.user_location = review['user_location']
        new_review.user_score = review['user_score']
        new_review.user_score_count = review['user_score_count']

        return new_review


# Cache show data in the database
if __name__ == "__main__":
    # twd = TVShow("The Walking Dead")
    # twd.get_all_episode_reviews()
    # big_bang = TVShow("The Big Bang Theory")
    # bbt_episode_reviews = big_bang.get_all_episode_reviews()
    # print(str(bbt_episode_reviews))
    arrow = TVShow('Arrow')
    arrow_reviews = arrow.get_all_episode_reviews()
    arrow_overall_reviews = arrow.get_show_reviews()
    arrow.sample_recent_tweets(3)
    # arrow_tweets = arrow.get_tweets()
    # print(str(len(arrow_tweets)))
    # print(str(arrow_overall_reviews[0]))
    # print(arrow_reviews)
    # print(arrow_overall_reviews)
