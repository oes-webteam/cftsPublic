from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('consent', views.consent, name='consent'),
    path('howTo', views.howTo, name='howTo'),
    path('resources', views.resources, name='resources'),
    path('urlShortner', views.urlShortner, name='urlShortner'),
    path('testCards', views.testCards, name='testCards'),
    path('testCards2', views.testCards2, name='testCards2'),
    path('testCards3', views.testCards3, name='testCards3'),
    path('adminTabs', views.adminTabs, name='adminTabs'),
]
