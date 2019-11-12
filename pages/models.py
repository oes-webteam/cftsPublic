import uuid
from django.conf import settings
from django.db import models

class Classification( models.Model ):
  Classification_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=settings.DEBUG)
  FullName = models.CharField( max_length=50 )
  Abbrev = models.CharField( max_length=50 )
  SortOrder = models.IntegerField()
  class Meta:
    ordering = ['SortOrder']
  def __str__(self):
    return self.FullName

class File( models.Model ):
  File_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  Filename = models.CharField( max_length=50 )
  Path = models.CharField( max_length=100 )
  Size = models.IntegerField()
  Classification = models.OneToOneField( Classification, on_delete=models.DO_NOTHING )
  def __str__(self):
    return self.Filename

class Network( models.Model ):
  Network_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=settings.DEBUG )
  Name = models.CharField( max_length=50 )
  Classifications = models.ManyToManyField( Classification )
  def __str__(self):
    return self.Name

class Email( models.Model ):
  Email_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  Address = models.CharField( max_length=255 )

class User( models.Model ):
  User_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  Email = models.OneToOneField( Email, on_delete=models.DO_NOTHING )

class Request( models.Model ):
  Request_id = models.UUIDField( primary_key=True, default=uuid.uuid4, editable=False )
  DateCreated = models.DateTimeField()
  DatePulled = models.DateTimeField()
  DateOneEye = models.DateTimeField()
  DateTwoEye = models.DateTimeField()
  DateComplete = models.DateTimeField()
  DiscNumber = models.IntegerField()
  IsSubmitted = models.BooleanField()
  User = models.OneToOneField( User, on_delete=models.DO_NOTHING )
  Network = models.OneToOneField( Network, on_delete=models.DO_NOTHING )
  Emails = models.ManyToManyField( Email )
  PullNumber = models.IntegerField( default=None )

  def count_by_network( self, netName ):
    return self.network_set.filter( Name=netName ).count()
