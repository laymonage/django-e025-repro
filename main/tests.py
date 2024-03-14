from django.test import TestCase
from main.models import (
    Parent,
    Child,
    Normal,
    WithoutGenericRelation,
    WithoutGenericRelationChild,
)

# Create your tests here.


class E025Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = Parent.objects.create(title="Parent")
        cls.child = Child.objects.create(title="Child", number=123)
        cls.normal = Normal.objects.create(title="Normal")
        cls.without_generic_relation = WithoutGenericRelation.objects.create(
            title="WithoutGenericRelation",
        )
        cls.without_generic_relation_child = WithoutGenericRelationChild.objects.create(
            title="WithoutGenericRelationChild",
            number=456,
        )

    def test_with_most_specific_content_type(self):
        objects = [
            self.parent,
            self.child,
            self.normal,
            self.without_generic_relation,
            self.without_generic_relation_child,
        ]
        for obj in objects:
            with self.subTest(obj=obj):
                self.assertEqual(list(obj.tags.all()), [])
                obj.add_tags("tag1", "tag2")
                obj = type(obj).objects.get(pk=obj.pk)
                self.assertEqual([tag.name for tag in obj.tags.all()], ["tag1", "tag2"])

    def test_multi_table_inheritance(self):
        objects = [
            # Tuple of the child instance, child model, and the parent model
            (
                self.child,
                Child,
                Parent,
            ),
            (
                self.without_generic_relation_child,
                WithoutGenericRelationChild,
                WithoutGenericRelation,
            ),
        ]
        for obj, child_model, parent_model in objects:
            with self.subTest(obj=obj, parent_model=parent_model):
                self.assertIsInstance(obj, child_model)
                self.assertEqual(list(obj.tags.all()), [])

                # Add tags while it is a child model instance
                obj.add_tags("tag1", "tag2")

                # Get the instance as the parent model instance
                obj = parent_model.objects.get(pk=obj.pk)

                # The tags should be the same
                self.assertEqual([tag.name for tag in obj.tags.all()], ["tag1", "tag2"])

                # Add tags while it is a parent model instance
                obj.add_tags("tag3", "tag4")

                # Get the instance as the child model instance
                obj = child_model.objects.get(pk=obj.pk)

                # The tags should be the same
                self.assertEqual(
                    [tag.name for tag in obj.tags.all()],
                    ["tag1", "tag2", "tag3", "tag4"],
                )
