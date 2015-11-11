from django.shortcuts import render
import re

from ratings_frontend.SentimentAnalysis import twitter_sentiment_analysis

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
        print('Searching for: ', str(show))
        sentiment = sentiment_analysis.readFromMongo(show, 500)

    context = {'show': show,
               'sentiment': sentiment}
    print('Sentiment ', sentiment)
    print('context: ' + str(context))

    return render(request, 'ratings_frontend/search.html', context)

def parse_show(show):
    lower_show = show.lower()
    possible_shows = ['Walking Dead', \
            'Arrow',\
            'Family Guy',\
            'Big Bang Theory',\
            'South Park',\
            'American Horror Story',\
            'Modern Family',\
            'Heroes Reborn']
    if bool(re.search(lower_show, 'walking|dead')):
        return possible_shows[0]
    elif lower_show == 'arrow':
        return possible_shows[1]
    elif lower_show == 'family guy' or bool(re.search(lower_show, 'guy')):
        return possible_shows[2]
    elif bool(re.search(lower_show, 'big|bang|theory')):
        return possible_shows[3]
    elif bool(re.search(lower_show, 'south|park')):
        return possible_shows[4]
    elif bool(re.search(lower_show, 'american|horror|story')):
        return possible_shows[5]
    elif bool(re.search(lower_show, 'modern')):
        return possible_shows[6]
    elif bool(re.search(lower_show, 'heroes|reborn')):
        return possible_shows[7]
    
    return 'undertermined show'
