from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login', template_name='accounts/logout.html'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Profil utilisateur
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # Gestion des mots de passe
    path('password/change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'), 
        name='password_change_done'
    ),
    path('password/reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'), 
        name='password_reset_done'
    ),
    path('password/reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), 
        name='password_reset_confirm'
    ),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'), 
        name='password_reset_complete'
    ),
    
    # Administration des utilisateurs (admin seulement)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/create/', views.create_user, name='user_create'),
    path('users/create-from-teacher/', views.create_teacher_user, name='create_teacher_user'),
    path('users/<int:pk>/roles/', views.update_user_roles, name='user_roles'),
    path('users/<int:pk>/toggle-active/', views.activate_deactivate_user, name='toggle_user_active'),
    path('users/<int:pk>/delete/', views.delete_user, name='user_delete'),
]
