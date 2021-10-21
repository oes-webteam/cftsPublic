from pages.views.feedback import feedback
from django.contrib import admin
from pages.models import *

class UserAdmin(admin.ModelAdmin):
    list_filter = ('banned',)
    list_display = (User.__str__,'email','user_identifier','banned')

class RequestAdmin(admin.ModelAdmin):
    list_display = ('user','network','org','has_rejected','all_rejected')
    fields = ('user','request_hash','network','org','pull','date_pulled',('files','target_email'),('comments','notes'),('is_centcom','is_dupe','has_rejected','all_rejected','destFlag'),)

# Register your models here.
admin.site.register( Classification )
admin.site.register( File )
admin.site.register( Network )
admin.site.register( Email )
admin.site.register(User, UserAdmin )
admin.site.register( Pull )
admin.site.register( Rejection )
admin.site.register( Request, RequestAdmin )
admin.site.register( ResourceLink )
admin.site.register( DirtyWord )
admin.site.register( Feedback )