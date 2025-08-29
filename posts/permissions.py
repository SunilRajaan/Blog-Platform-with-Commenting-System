from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only authors to edit their posts/comments.
    Read permissions are allowed to any request.
    """

    def has_permission(self, request, view):
        # Authenticated users are always allowed to read/list objects.
        # This prevents unauthenticated users from hitting the perform_create method.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed for authenticated users.
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """ Read permissions are allowed to any request so we'll always allow GET, HEAD, or OPTIONS requests """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the author of the post/comment.
        return obj.author == request.user