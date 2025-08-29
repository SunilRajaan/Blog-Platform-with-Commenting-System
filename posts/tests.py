from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Tag, Post, Comment
from .serializers import (
    PostSerializer,
    CommentSerializer,
)

User = get_user_model()


class TestModel(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.category = Category.objects.create(name="Technology")
        self.tag = Tag.objects.create(name="Django")
        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            category=self.category,
            author=self.user,
        )
        self.post.tag.add(self.tag)
        self.comment = Comment.objects.create(
            post=self.post, content="Test comment.", author=self.user
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), "Technology")

    def test_tag_str(self):
        self.assertEqual(str(self.tag), "Django")

    def test_post_str(self):
        self.assertEqual(str(self.post), "Test Post")

    def test_comment_str(self):
        expected_str = f"Comment by {self.user.username} on {self.post.title}"
        self.assertEqual(str(self.comment), expected_str)

    def test_post_relationships(self):
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.category, self.category)
        self.assertIn(self.tag, self.post.tag.all())

    def test_comment_relationships(self):
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.author, self.user)


# ---

class TestPermissions(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="password123"
        )
        self.post = Post.objects.create(
            title="Permission Test Post",
            content="Content.",
            author=self.author,
        )

    def test_safe_method_allowed_for_any_user(self):
        # GET request by an unauthenticated user
        response = self.client.get(reverse("posts-detail", args=[self.post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # GET request by an authenticated user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(reverse("posts-detail", args=[self.post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_write_method_allowed_for_author(self):
        self.client.force_authenticate(user=self.author)
        data = {"title": "Updated Title"}
        response = self.client.patch(
            reverse("posts-detail", args=[self.post.id]), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_write_method_denied_for_non_author(self):
        self.client.force_authenticate(user=self.other_user)
        data = {"title": "Updated Title"}
        response = self.client.patch(
            reverse("posts-detail", args=[self.post.id]), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_write_method_denied_for_unauthenticated_user(self):
        data = {"title": "Updated Title"}
        response = self.client.patch(
            reverse("posts-detail", args=[self.post.id]), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---

class TestSerializers(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.category = Category.objects.create(name="Programming")
        self.tag1 = Tag.objects.create(name="Python")
        self.tag2 = Tag.objects.create(name="REST API")
        self.post = Post.objects.create(
            title="Serializer Test",
            content="Content",
            author=self.user,
            category=self.category,
        )
        self.post.tag.add(self.tag1, self.tag2)
        self.comment = Comment.objects.create(
            post=self.post, content="First comment", author=self.user
        )
        self.reply = Comment.objects.create(
            post=self.post,
            content="Reply to first comment",
            author=self.user,
            parent=self.comment,
        )

    def test_post_serializer(self):
        serializer = PostSerializer(instance=self.post)
        expected_data = {
            "id": self.post.id,
            "title": "Serializer Test",
            "content": "Content",
            "author": self.user.username,
            "category": self.category.name,
            "tag": [self.tag1.name, self.tag2.name],
            "created_at": serializer.data["created_at"],
            "updated_at": serializer.data["updated_at"],
        }
        self.assertEqual(serializer.data, expected_data)

    def test_comment_serializer_with_replies(self):
        serializer = CommentSerializer(instance=self.comment)
        self.assertIn("replies", serializer.data)
        self.assertEqual(len(serializer.data["replies"]), 1)
        self.assertEqual(serializer.data["replies"][0]["id"], self.reply.id)
        self.assertEqual(serializer.data["replies"][0]["content"], "Reply to first comment")

    def test_comment_serializer_create_with_parent(self):
        data = {
            "post": self.post.title,
            "content": "Another reply",
            "parent": self.comment.id,
        }
        # The serializer save requires the author
        self.client.force_authenticate(user=self.user)
        # We need to test the serializer through a view to get a request context
        response = self.client.post(
            reverse("comments-list"), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_comment = Comment.objects.get(id=response.data['id'])
        self.assertEqual(new_comment.parent, self.comment)
        self.assertEqual(new_comment.content, "Another reply")


# ---

class TestViewSet(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="password123"
        )
        self.category = Category.objects.create(name="Technology")
        self.tag = Tag.objects.create(name="Testing")
        self.post = Post.objects.create(
            title="Test Post",
            content="This is content.",
            author=self.user,
            category=self.category,
        )
        self.post.tag.add(self.tag)
        self.comment = Comment.objects.create(
            post=self.post, content="A great comment.", author=self.user
        )

    def test_category_list_and_detail(self):
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_post_list(self):
        response = self.client.get(reverse("posts-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_post_creation_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "New Post",
            "content": "New content.",
            "category": self.category.name,
            "tag": [self.tag.name],
        }
        response = self.client.post(reverse("posts-list"), data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Post.objects.last().author, self.user)

    def test_post_creation_unauthenticated(self):
        data = {
            "title": "Unauthorized Post",
            "content": "Content.",
            "category": self.category.name,
            "tag": [self.tag.name],
        }
        response = self.client.post(reverse("posts-list"), data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)

    def test_post_update_as_author(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "Updated Post Title"}
        response = self.client.patch(
            reverse("posts-detail", args=[self.post.id]), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Post Title")

    def test_post_update_as_non_author(self):
        self.client.force_authenticate(user=self.other_user)
        data = {"title": "Forbidden Update"}
        response = self.client.patch(
            reverse("posts-detail", args=[self.post.id]), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.title, "Forbidden Update")

    def test_comment_list_with_post_id_filter(self):
        # Create a second post and comment to test filtering
        new_post = Post.objects.create(
            title="Second Post", content="More content.", author=self.other_user
        )
        Comment.objects.create(
            post=new_post, content="Comment on second post.", author=self.other_user
        )
        # Test filtered list
        response = self.client.get(
            reverse("comments-list") + f"?post_id={self.post.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["content"], "A great comment.")

    def test_comment_creation_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {"post": self.post.title, "content": "New comment on post."}
        response = self.client.post(
            reverse("comments-list"), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 2)

    def test_comment_delete_as_author(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse("comments-detail", args=[self.comment.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_delete_as_non_author(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(reverse("comments-detail", args=[self.comment.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)
