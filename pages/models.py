import uuid, os
from django.conf import settings
from django.db import models

def randomize_path( instance, filename ):
  path = uuid.uuid4()
  os.mkdir( path )
  return os.path.join( path, filename )

class Classification( models.Model ):
  classification_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=settings.DEBUG )
  full_name = models.CharField( max_length=50 )
  abbrev = models.CharField( max_length=50 )
  sort_order = models.IntegerField()
  class Meta:
    ordering = ['sort_order']
  def __str__(self):
    return self.full_name

class Rejection( models.Model ):
  rejection_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  subject = models.CharField( max_length=255 )
  text = models.TextField()

class File( models.Model ):
  file_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  file_object = models.FileField( upload_to=randomize_path )
  classification = models.OneToOneField( Classification, on_delete=models.DO_NOTHING )
  rejection_reason = models.OneToOneField( Rejection, on_delete=models.DO_NOTHING, null=True, blank=True )
  rejection_text = models.TextField( default=None, blank=True )
  def __str__(self):
    return self.filename

class Network( models.Model ):
  network_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=settings.DEBUG )
  name = models.CharField( max_length=50 )
  classifications = models.ManyToManyField( Classification )
  def __str__(self):
    return self.name

class Email( models.Model ):
  email_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  address = models.CharField( max_length=255 )

class User( models.Model ):
  user_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  email = models.OneToOneField( Email, on_delete=models.DO_NOTHING )

class Request( models.Model ):
  request_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  date_created = models.DateTimeField( auto_now_add=True )
  user = models.OneToOneField( User, on_delete=models.DO_NOTHING )
  network = models.OneToOneField( Network, on_delete=models.DO_NOTHING )
  files = models.ManyToManyField( File )
  target_emails = models.ManyToManyField( Email )
  is_submitted = models.BooleanField( default=False )
  date_pulled = models.DateTimeField( null=True, blank=True )
  pull_number = models.IntegerField( null=True, blank=True )
  date_oneeye = models.DateTimeField( null=True, blank=True )
  date_twoeye = models.DateTimeField( null=True, blank=True )
  date_complete = models.DateTimeField( null=True, blank=True )
  disc_number = models.IntegerField( null=True, blank=True )

  def pending_count_by_network( self, netName ):
    return self.__class__.objects.filter( network__name=netName, is_submitted=True, date_complete__isnull=True ).count()
