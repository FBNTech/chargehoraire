from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Role

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_roles')
    list_filter = BaseUserAdmin.list_filter + ('profile__roles',)
    
    def get_roles(self, obj):
        roles = obj.profile.roles.all()
        if roles:
            return ', '.join([role.name for role in roles])
        return 'Aucun rôle'
    
    get_roles.short_description = 'Rôles'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

# Réenregistrer le modèle User avec notre UserAdmin personnalisé
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Role, RoleAdmin)
