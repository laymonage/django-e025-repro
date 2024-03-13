from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from taggable.models import ItemTag, TaggableItem

# Create your models here.


def get_default_parent_content_type():
    return ContentType.objects.get_for_model(Parent, for_concrete_model=False)


class Parent(TaggableItem, models.Model):
    """
    A model that knows about being used with multi-table inheritance
    and tries to be smart about it by storing the most specific content type.

    https://code.djangoproject.com/ticket/31269
    """

    # The most specific content type that this object is an instance of.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET(get_default_parent_content_type),
        related_name="+",
    )
    title = models.CharField(max_length=255)

    _tags = GenericRelation(
        ItemTag,
        object_id_field="object_id",
        content_type_field="base_content_type",
        related_query_name="parent",
        for_concrete_model=False,
    )
    _specific_tags = GenericRelation(
        ItemTag,
        object_id_field="object_id",
        content_type_field="content_type",
        related_query_name="specific_parent",
        for_concrete_model=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def get_content_type(self):
        # Ensure we are using the most specific content type.
        return self.content_type

    @property
    def tags(self):
        # Handle the case where we are accessing the tags of a specific instance
        # or a non-specific instance.
        # See https://code.djangoproject.com/ticket/31269
        if self.is_specific:
            return self._specific_tags
        return self._tags

    def add_tags(self, *tag_names):
        # Ensure we are adding tags to the most specific instance, so the
        # ItemTag is created with the correct content_type.
        if not self.is_specific:
            return self.specific.add_tags(*tag_names)
        return super().add_tags(*tag_names)

    @property
    def specific(self):
        if self.specific_class is None:
            return self
        return self.specific_class._default_manager.get(pk=self.pk)

    @property
    def specific_class(self):
        return self.content_type.model_class()

    @property
    def is_specific(self):
        return self.specific_class is not None and isinstance(self, self.specific_class)


class Child(Parent):
    """A model that inherits from Parent, with additional fields."""

    number = models.IntegerField(default=0)


class Normal(TaggableItem, models.Model):
    """A model that is not involved in multi-table inheritance."""

    title = models.CharField(max_length=255)

    # We know this model won't be subclassed, so we replace the
    # TaggableItem.tags property with a GenericRelation directly.
    tags = GenericRelation(
        ItemTag,
        object_id_field="object_id",
        content_type_field="content_type",
        related_query_name="normal",
        for_concrete_model=False,
    )


class WithoutGenericRelation(TaggableItem, models.Model):
    """
    A model that does not have a GenericRelation and is being used with
    multi-table inheritance, but does not try to be smart about it.

    It relies on TaggableModel.tags default @property to get the tags.
    """

    title = models.CharField(max_length=255)


class WithoutGenericRelationChild(WithoutGenericRelation):
    """A model that inherits from WithoutGenericRelation, with additional fields."""

    number = models.IntegerField(default=0)
