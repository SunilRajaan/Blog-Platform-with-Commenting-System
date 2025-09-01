from django.contrib.auth import get_user_model
from rest_framework import viewsets
from .models import Post, Tag, Comment, Category
from .serializers import CommentSerializer, PostSerializer, TagSerializer, UserSerializer, CategorySerializer
from .permissions import IsAuthorOrReadOnly
from .pagination import PostPagination, CommentPagination

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    # only provides read-only endpoints
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    # Handle CRUD for category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class TagViewSet(viewsets.ModelViewSet):
    # Handle CRUD for tag
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class PostViewSet(viewsets.ModelViewSet):
    # Handle CRUD for post
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = PostPagination
    filterset_fields = ['tag__name', 'created_at',]
    search_fields = ['title', 'category__name', 'author__username',]

    # logged-in user will be as author when creating a post.
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    # Handle CRUD for comment
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CommentPagination

    def get_queryset(self):
        """ Return the comments to the given post by filtering aginst 'post_id' query parameter in the URL"""
        queryset = Comment.objects.all()
        post_id = self.request.query_params.get('post_id')
        if post_id:
            queryset = queryset.filter(post__id=post_id)
        return queryset

    # logged-in user will be as author when creating a comment.
    def perform_create(self, serializer):
        serializer.save(author = self.request.user)

