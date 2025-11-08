"""
URL configuration for projectsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from eventease.views import (
    LandingPageView,
    LeaderboardView,
    SignUpView,
    LoginView,
    LogoutView,
    UserProfileView,
    MyRegistrationsView,
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    EventDeleteView,
    AnnouncementsNewsfeedView,
    RegisterForEventView,
    UnregisterFromEventView,
)
from eventease.admin_views import (
    UserManagementView,
    UpdateUserRoleView,
    ManageEventsView,
    ManageParticipantsView,
    UpdateRegistrationStatusView,
    AnnouncementListView,
    AnnouncementCreateView,
    AnnouncementUpdateView,
    AnnouncementDeleteView,
)

urlpatterns = [
    # Admin Management - Super Admin (must come before Django admin)
    path('admin/users/', UserManagementView.as_view(), name='user-management'),
    path('admin/users/<int:pk>/role/', UpdateUserRoleView.as_view(), name='update-user-role'),
    
    # Admin Management - Events & Participants
    path('admin/events/', ManageEventsView.as_view(), name='manage-events'),
    path('admin/participants/', ManageParticipantsView.as_view(), name='manage-participants'),
    path('admin/registrations/<int:pk>/update/', UpdateRegistrationStatusView.as_view(), name='update-registration'),
    
    # Admin Management - Announcements
    path('admin/announcements/', AnnouncementListView.as_view(), name='announcement-list'),
    path('admin/announcements/add/', AnnouncementCreateView.as_view(), name='announcement-create'),
    path('admin/announcements/<int:pk>/update/', AnnouncementUpdateView.as_view(), name='announcement-update'),
    path('admin/announcements/<int:pk>/delete/', AnnouncementDeleteView.as_view(), name='announcement-delete'),
    
    # Django Admin (must come after custom admin paths)
    path('admin/', admin.site.urls),
    
    # Authentication
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    
    # Landing Page
    path('', LandingPageView.as_view(), name='landing'),
    
    # Events
    path('events/', EventListView.as_view(), name='event-list'),
    path('events/add/', EventCreateView.as_view(), name='event-create'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('events/<int:pk>/update/', EventUpdateView.as_view(), name='event-update'),
    path('events/<int:pk>/delete/', EventDeleteView.as_view(), name='event-delete'),
    path('events/<int:event_id>/register/', RegisterForEventView.as_view(), name='register-event'),
    path('events/<int:event_id>/unregister/', UnregisterFromEventView.as_view(), name='unregister-event'),
    
    # Announcements/Newsfeed
    path('announcements/', AnnouncementsNewsfeedView.as_view(), name='announcements-newsfeed'),
    
    # User Profile & Registrations
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('my-registrations/', MyRegistrationsView.as_view(), name='my-registrations'),
    
    # Leaderboard
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
