from django.urls import path
from . import static_views
import pages.views as views

urlpatterns = [
    path( '', views.frontend, name='index' ),
    path( 'consent', static_views.consent, name='consent' ),
    path( 'howTo', static_views.howTo, name='howTo' ),
    path( 'resources', static_views.resources, name='resources' ),
    path( 'urlShortner', static_views.urlShortner, name='urlShortner' ),

    # frontend
    path('frontend', views.frontend, name='frontend'),

    # queue
    path( 'queue', views.queue, name='queue' ),
    path( 'transfer-request/<uuid:id>', views.transferRequest, name='transfer-request' ),
    path( 'create-zip/<str:network_name>', views.createZip, name='create-zip' ),
    
    # pulls
    path( 'pulls', views.pulls, name='pulls' ),
    path( 'pulls-oneeye/<uuid:id>', views.pullsOneEye, name='pulls-oneeye' ),
    path( 'pulls-twoeye/<uuid:id>', views.pullsTwoEye, name='pulls-twoeye' ),
    path( 'pulls-done/<uuid:id>/<int:cd>', views.pullsDone, name='pulls-done' ),
    
    # archive
    path( 'archive', views.archive, name='archive' ),

    # reporting
    path( 'reports', views.reports, name='reports' ),

    # APIs
    path( 'api-getuser/<uuid:id>', views.getUser, name='api-getuser' ),
    path( 'api-setreject', views.setReject, name='api-setreject' ),
    path( 'api-numbers', views.runNumbers, name='api-numbers' ),
    ## path( 'api-processreqeust', views.process, name='api-processrequest' ),

    # dev tools
    path( 'tools-makefiles', views.makeFiles, name='make-files' ),
    path( 'tools-stubget', views.stubGet, name="stub-get" ),
    path( 'tools-stubpost', views.stubPost, name="stub-post" ),
]
