from django.db import models
import uuid

class WebBaseModel(models.Model):
    date_added = models.DateTimeField(db_index=True,auto_now_add=True, editable=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True