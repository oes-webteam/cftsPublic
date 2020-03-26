from django.urls import path
from . import views

urlpatterns = [
    path( '', views.index, name='index' ),
    path( 'consent', views.consent, name='consent' ),
    path( 'howTo', views.howTo, name='howTo' ),
    path( 'resources', views.resources, name='resources' ),
    path( 'urlShortner', views.urlShortner, name='urlShortner' ),
    path( 'analysts', views.analysts, name='analysts' ),
    path( 'transfer-request/<uuid:id>', views.transferRequest, name='transfer-request' ),
    path( 'create-zip/<str:network_name>', views.createZip, name='create-zip' ),
]
