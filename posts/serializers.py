from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tag, Post, Comment, Category

"""
Serializer for the User model.
It's used to provide read-only user information for the blog posts and comments.
"""
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username',)

#Serializer for Category model
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

#Serializer for Tag model
class TagSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Tag
        fields = '__all__'

class RecursiveField(serializers.Serializer):
    """
    Helper serializer for recursive nested replies in CommentSerializer.
    """
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

# Serializer for blog comment
class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    Uses SlugRelatedField for the related post (by title) and author (by username).
    Handles nested replies and allows creating comments using post title and parent comment ID.
    """
    post = serializers.SlugRelatedField(
        queryset=Post.objects.all(),
        slug_field='title'
    )

    author = serializers.StringRelatedField(read_only=True)
    
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        allow_null=True,
        required=False
    )
    replies = RecursiveField(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'post', 'content', 'author', 'parent', 'created_at', 'updated_at', 'replies',)
        read_only_fields = ['replies', 'created_at']

# Serializer for blog post
class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for the Post model.
    Uses SlugRelatedField for category and tags so users can create/update posts
    using the category name and tag names instead of IDs.
    """
    # Use the category name instead of its ID for write/read
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='name'
    )
    # Use tag names instead of their IDs for write/read, supports multiple tags
    tag = serializers.SlugRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        slug_field='name'
    )
    author = serializers.StringRelatedField(read_only=True)  # Display username

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'category', 'tag', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']
        

