from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Imagine this is a third-party app


class ItemTag(models.Model):
    name = models.CharField(max_length=255)
    base_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+",
    )
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey("content_type", "object_id")


# This doesn't technically need to inherit from models.Model, but we're doing it
# to make it clear that this is a model mixin.
class TaggableItem(models.Model):
    def get_base_content_type(self):
        parents = self._meta.get_parent_list()
        # Get the last non-abstract parent in the MRO as the base_content_type.
        # Note: for_concrete_model=False means that the model can be a proxy model.
        if parents:
            return ContentType.objects.get_for_model(
                parents[-1], for_concrete_model=False
            )
        # This model doesn't inherit from a non-abstract model,
        # use it as the base_content_type anyway (they are the same).
        return self.get_content_type()

    def get_content_type(self):
        return ContentType.objects.get_for_model(self, for_concrete_model=False)

    @property
    def tags(self):
        """
        Returns a queryset of ItemTag objects for this object.

        Instead of using a GenericRelation, we use a @property that queries the
        ItemTag model directly. This is to ensure that we are using the base
        content type when querying for tags, so models that use multi-table
        inheritance always get the same tags, regardless which model is used to
        query for them.

        Workaround for https://code.djangoproject.com/ticket/31269.
        """
        return ItemTag.objects.filter(
            base_content_type=self.get_base_content_type(),
            object_id=str(self.pk),
        )

    def add_tags(self, *tag_names):
        tags = [
            ItemTag(
                name=tag_name,
                base_content_type=self.get_base_content_type(),
                content_type=self.get_content_type(),
                object_id=str(self.pk),
            )
            for tag_name in tag_names
        ]
        ItemTag.objects.bulk_create(tags, ignore_conflicts=True)

    class Meta:
        abstract = True
