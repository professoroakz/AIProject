from django.shortcuts import render

from ratings_frontend.SentimentAnalysis import twitter_sentiment_analysis

# Create your views here.

def index(request):
    return render(request, 'ratings_frontend/index.html')


def search(request):
    sentiment = None
    sentiment_analysis = twitter_sentiment_analysis.SentimentAnalysis()
    query_string = ''
    tweets = {}
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        sentiment = sentiment_analysis.readFromMongo(query_string, 500)

    context = {'query_string': query_string,
               'sentiment': sentiment}
    print('Sentiment ', sentiment)
    print('context: ' + str(context))

    return render(request, 'ratings_frontend/search.html', context)
