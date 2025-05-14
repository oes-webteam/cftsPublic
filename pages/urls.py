from django.urls import path
import pages.views as views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('CFTS.cfm', views.frontend, name='index'),
    path('cfts.cfm', views.frontend, name='index'),
    path('', views.frontend, name='index'),
    path('consent', views.consent, name='consent'),

    # auth
    #path('register', views.register, name='register'),
    path('login', views.userLogin, name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('user-info', views.editUserInfo, name='user-info'),

    # resources
    path('resources/<str:file>', views.resources, name='resources'),

    # frontend
    path('frontend', views.frontend, name='frontend'),

    # user requests
    path('my-requests', views.userRequests, name='userRequests'),
    path('request/<uuid:id>', views.requestDetails, name='userRequests'),
    path('cancelUserRequest/<uuid:id>', views.cancelUserRequest, name='cancelUserRequest'),

    # queue
    path('queue', views.queue, name='queue'),
    path('queue/cookie', views.queue, name='cookie'),
    path('transfer-request/<uuid:id>', views.transferRequest, name='transfer-request'),
    path('create-zip/<str:network_name>/<str:rejectPull>', views.createZip, name='create-zip'),
    path('updateFileReview/<uuid:fileID>/<uuid:rqstID>/<str:quit>/<str:completeReview>', views.updateFileReview, name='reviewFile'),
    path('getFile/<str:folder>/<str:fileID>/<str:fileName>', views.getFile, name='getFile'),
    path('removeFileReviewer/<int:stage>', views.removeFileReviewer, name='removeReview'),
    path('getRejectModal/<uuid:fileID>', views.getRejectModal, name='getRejectModal'),
    path('getReviewModal/<uuid:fileID>', views.getReviewModal, name='getReviewModal'),

    # drops
    path('drop-zone', views.dropZone, name='drop-zone'),
    path('process-drop', views.processDrop, name='process-drop'),
    path('drop/<uuid:id>/<str:PIN>', views.dropDetails, name='drop'),
    path('drop/<uuid:id>', views.dropDetails, name='drop'),
    path('generate-drop-email/<uuid:id>', views.dropEmail, name='drop-email'),
    path('download-drop/<uuid:id>/<str:phrase>', views.dropDownload, name='drop-download'),


    # scan
    path('scan/<uuid:rqst_id>', views.scan, name="scan"),
    path('viewscan/<uuid:pull_id>', views.viewScan, name="viewscan"),

    # pulls
    path('pulls', views.pulls, name='pulls'),
    path('getPull/<str:fileName>', views.getPull, name='getPull'),
    path('pulls-done/<uuid:id>/<int:cd>', views.pullsDone, name='pulls-done'),
    path('cancelPull/<uuid:id>/', views.cancelPull, name='cancelPull'),

    # archive
    path('archive', views.archive, name='archive'),
    path('filterArchive', views.filterArchive, name='filterArchive'),

    # reporting
    path('reports', views.reports, name='reports'),

    # feedback
    path('ban-request/<uuid:requestid>', views.feedback, name='ban-request'),
    path('feedback', views.feedback, name='feedback'),
    path('ban-request/submitfeedback', views.submitFeedback, name='submitfeedback'),
    path('submitfeedback', views.submitFeedback, name='submitfeedback'),

    # compliance banner
    path('compliance-banner-settings', views.delayed_compliance, name='compliance-banner-settings'),
    path('accept_compliance_banner', views.delayed_compliance, name='accept_compliance_banner'),

    # APIs
    path('api-setreject', views.setReject, name='api-setreject'),
    path('api-setrejectdupes', views.setRejectDupes, name='api-setrejectdupes'),
    path('api-unreject', views.unReject, name='api-unreject'),
    path('api-setencrypt', views.setEncrypt, name='api-setencrypt'),
    path('api-numbers', views.runNumbers, name='api-numbers'),
    path('api-numbers/<int:api_call>', views.runNumbers, name='api-numbers'),
    path('api-processrequest', views.process, name='api-processrequest'),
    path('api-setconsentcookie', views.setConsentCookie, name='api-setconsentcookie'),
    path('api-requestnotes/<uuid:requestid>', views.requestNotes, name='api-requestnotes'),
    path('api-banuser/<uuid:userid>/<uuid:requestid>/<str:ignore_strikes>/<str:perma_ban>', views.banUser, name='api-banuser'),
    path('api-warnuser/<uuid:userid>/<uuid:requestid>/<str:confirmWarn>', views.warnUser, name='api-warnuser'),
    path('api-warnuser/<uuid:userid>/<uuid:requestid>', views.warnUser, name='api-warnuser'),
    path('api-fileCleanup', views.fileCleanup, name='api-fileCleanup'),

    # dev tools
    path('spaghetti', views.spaghetti, name='spaghetti'),

]
