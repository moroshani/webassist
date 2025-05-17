from django.db import models

class Link(models.Model):
    url = models.URLField(unique=True)

    def __str__(self):
        return self.url
