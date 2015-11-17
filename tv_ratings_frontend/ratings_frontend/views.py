from django.shortcuts import render
import re

from ratings_frontend.SentimentAnalysis import twitter_sentiment_analysis
from ratings_frontend.backend.pattern_ml import imdb
from ratings_frontend.backend.pattern_ml import twitter_sentiment_analysis_pattern as tsa

# Create your views here.

def index(request):
    return render(request, 'ratings_frontend/index.html')


def search(request):
    sentiment = None
    sentiment_analysis = twitter_sentiment_analysis.SentimentAnalysis()
    query_string = ''
    show = ''
    tweets = {}
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        show = parse_show(str(query_string))
        if show != 'undetermined':
            print('Searching for: ', str(show))
            try:
                # sentiment = sentiment_analysis.readFromMongo(show, 500)
                client = imdb.ImdbClient()
                imdb_classifier = tsa.Classifier(query_string)
                stats = imdb_classifier.nbClassify()

                print("stats:\n" + str(stats))

                context = {'show': show,
                           'num_tweets': stats[1],
                           'estimated_rating': stats[2],
                           'imdb_rating': stats[3],
                           'percent_error': stats[4]}
                           # 'prop_pos': sentiment[0],
                           # 'prop_neg': sentiment[1],
                           # 'num_tweets': sentiment[2]}
            except ValueError:
                context = {'show': 'unable to match'}
        else:
            context = {'show': 'unable to match ' + query_string + ' to a show',
                       'prop_pos': 'N/A',
                       'prop_neg': 'N/A',
                       'num_tweets': 'N/A'}
    else:
        context = {'show': 'unable to match'}

    return render(request, 'ratings_frontend/search.html', context)

def parse_show(show):
    lower_show = show.lower()
    print('Show: ', show)
    possible_shows = ['Walking Dead', \
            'Arrow',\
            'Family Guy',\
            'Big bang Theory',\
            'South Park',\
            'American Horror Story',\
            'Modern Family',\
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
