from django.db import models


class Tag(models.Model):
    slug = models.SlugField(max_length=30, unique=True)
    label = models.CharField(max_length=100)

    def __str__(self):
        "Returns the label of the tag."
        return self.label

    class Meta:
        ordering = ('label',)


class Preference(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='preferences'
    )

    email_hash = models.CharField(max_length=64)
    subscribed = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        "Returns the email hash as a string."
        return self.email_hash

    class Meta:
        ordering = ('-updated',)
        get_latest_by = 'updated'
