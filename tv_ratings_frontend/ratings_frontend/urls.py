from django.conf.urls import url, patterns
from ratings_frontend import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^search/$', views.search, name='search'))
