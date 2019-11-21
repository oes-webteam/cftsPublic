import uuid
from django.conf import settings
from django.db import models

class Classification( models.Model ):
  classification_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=settings.DEBUG)
  full_name = models.CharField( max_length=50 )
  abbrev = models.CharField( max_length=50 )
  sort_order = models.IntegerField()
  class Meta:
    ordering = ['sort_order']
  def __str__(self):
    return self.full_name

class File( models.Model ):
  file_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  filename = models.CharField( max_length=50 )
  path = models.CharField( max_length=100 )
  size = models.IntegerField()
  classification = models.OneToOneField( Classification, on_delete=models.DO_NOTHING )
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
  date_created = models.DateTimeField( auto_now_add=True)
  date_pulled = models.DateTimeField()
  date_oneeye = models.DateTimeField()
  date_twoeye = models.DateTimeField()
  date_complete = models.DateTimeField()
  disc_number = models.IntegerField()
  is_submitted = models.BooleanField()
  user = models.OneToOneField( User, on_delete=models.DO_NOTHING )
  network = models.OneToOneField( Network, on_delete=models.DO_NOTHING )
  emails = models.ManyToManyField( Email )
  pull_number = models.IntegerField( default=None )

  def pending_count_by_network( self, netName ):
    return self.__class__.objects.filter( network__name=netName, date_complete__isnull=True ).count()