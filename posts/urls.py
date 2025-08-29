from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PostViewSet, CommentViewSet, TagViewSet, CategoryViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("posts", PostViewSet, basename="posts") 
router.register("comments", CommentViewSet, basename="comments")
router.register("tags", TagViewSet, basename="tags")
router.register("category", CategoryViewSet, basename="category")

urlpatterns = router.urls