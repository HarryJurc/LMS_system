from rest_framework import permissions

class IsModeratorOrReadOnly(permissions.BasePermission):
    """
    Модератор может только читать и редактировать (без создания и удаления).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_authenticated and request.user.groups.filter(name='moderators').exists():
            return request.method in ['PUT', 'PATCH']

        return request.user.is_staff or request.user.is_superuser


class IsOwnerOrModerator(permissions.BasePermission):
    """
    Разрешение для доступа только к своим объектам, кроме модераторов.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.groups.filter(name='Модераторы').exists():
            return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']
        return obj.owner == user
