from rest_framework import permissions


class HasRolePermission(permissions.BasePermission):
    """Bridge DRF actions to the project's custom role permission system."""

    action_aliases = {
        "list": "view",
        "retrieve": "view",
        "create": "create",
        "update": "update",
        "partial_update": "update",
        "destroy": "destroy",
    }

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        permission_map = getattr(view, "permission_map", {})
        action = getattr(view, "action", None)
        alias = self.action_aliases.get(action, action)
        codename = permission_map.get(action) or permission_map.get(alias)
        if not codename:
            return False
        return user.has_role_permission(codename)
