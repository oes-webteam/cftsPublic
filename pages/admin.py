from django.contrib import admin
from pages.models import *

# Register your models here.
admin.site.register( Classification )
admin.site.register( File )
admin.site.register( Network )
admin.site.register( Email )
admin.site.register( User )
admin.site.register( Pull )
admin.site.register( Rejection )
admin.site.register( Request )