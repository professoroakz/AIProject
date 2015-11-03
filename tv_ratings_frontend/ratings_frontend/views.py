from django.shortcuts import render


# Create your views here.

def index(request):
    return render(request, 'ratings_frontend/index.html')


def search(request):
    query_string = ''
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        print('Query: ', query_string)

    context = {'query_string': query_string}
    print('context: ' + str(context))

    return render(request, 'ratings_frontend/search.html', context)
