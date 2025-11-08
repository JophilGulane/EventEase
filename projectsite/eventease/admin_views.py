"""
Views for Super Admin and Admin management features.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import UserProfile, Event, Registration, Announcement
from .forms import AnnouncementForm
from .mixins import SuperAdminRequiredMixin, AdminRequiredMixin

User = get_user_model()


# ============================================================================
# SUPER ADMIN VIEWS - Manage Admins
# ============================================================================

class UserManagementView(SuperAdminRequiredMixin, ListView):
    """Super Admin view to manage users and assign roles."""
    model = User
    template_name = 'eventease/admin/user_management.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """Filter users based on search query."""
        queryset = User.objects.select_related('profile').all()
        search = self.request.GET.get('search', '')
        role_filter = self.request.GET.get('role', '')
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if role_filter:
            queryset = queryset.filter(profile__role=role_filter)
        
        return queryset.order_by('-date_joined')


class UpdateUserRoleView(SuperAdminRequiredMixin, UpdateView):
    """Super Admin view to update user roles."""
    model = UserProfile
    fields = ['role']
    template_name = 'eventease/admin/update_user_role.html'
    success_url = reverse_lazy('user-management')
    
    def get_object(self):
        """Get UserProfile from User pk."""
        user = User.objects.get(pk=self.kwargs['pk'])
        return user.profile
    
    def form_valid(self, form):
        messages.success(self.request, f'User role updated successfully!')
        return super().form_valid(form)


# ============================================================================
# ADMIN VIEWS - Manage Events and Participants
# ============================================================================

class ManageEventsView(AdminRequiredMixin, ListView):
    """Admin view to manage all events."""
    model = Event
    template_name = 'eventease/admin/manage_events.html'
    context_object_name = 'events'
    paginate_by = 20
    
    def get_queryset(self):
        """Show all events for Admin management."""
        queryset = Event.objects.select_related('created_by').all()
        search = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(venue__icontains=search)
            )
        
        if status_filter == 'upcoming':
            from django.utils import timezone
            queryset = queryset.filter(start_datetime__gte=timezone.now())
        elif status_filter == 'past':
            from django.utils import timezone
            queryset = queryset.filter(end_datetime__lt=timezone.now())
        
        return queryset.order_by('-pinned', '-start_datetime')


class ManageParticipantsView(AdminRequiredMixin, ListView):
    """Admin view to manage event participants."""
    model = Registration
    template_name = 'eventease/admin/manage_participants.html'
    context_object_name = 'registrations'
    paginate_by = 30
    
    def get_queryset(self):
        """Filter registrations based on event and status."""
        queryset = Registration.objects.select_related('event', 'user').all()
        event_id = self.request.GET.get('event', '')
        status_filter = self.request.GET.get('status', '')
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-registered_at')
    
    def get_context_data(self, **kwargs):
        """Add events list for filtering."""
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.all().order_by('-start_datetime')
        return context


class UpdateRegistrationStatusView(AdminRequiredMixin, UpdateView):
    """Admin view to update registration status (confirm, mark attended, etc.)."""
    model = Registration
    fields = ['status', 'notes']
    template_name = 'eventease/admin/update_registration.html'
    
    def get_success_url(self):
        return reverse_lazy('manage-participants')
    
    def form_valid(self, form):
        # Award points if marking as attended
        if form.cleaned_data['status'] == Registration.Status.ATTENDED:
            registration = form.instance
            if registration.status != Registration.Status.ATTENDED:
                # Award points based on event's points setting
                if hasattr(registration.user, 'profile'):
                    points_to_award = registration.event.get_points()
                    registration.mark_attended(award_points=points_to_award, reason="Event Attendance")
        
        messages.success(self.request, 'Registration status updated successfully!')
        return super().form_valid(form)


# ============================================================================
# ANNOUNCEMENT MANAGEMENT
# ============================================================================

class AnnouncementListView(AdminRequiredMixin, ListView):
    """Admin view to manage announcements."""
    model = Announcement
    template_name = 'eventease/admin/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20
    
    def get_queryset(self):
        """Show all announcements."""
        queryset = Announcement.objects.select_related('created_by').all()
        search = self.request.GET.get('search', '')
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset.order_by('-pinned', '-created_at')


class AnnouncementCreateView(AdminRequiredMixin, CreateView):
    """Admin view to create announcements."""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'eventease/admin/announcement_form.html'
    success_url = reverse_lazy('announcement-list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Announcement created successfully!')
        return super().form_valid(form)


class AnnouncementUpdateView(AdminRequiredMixin, UpdateView):
    """Admin view to update announcements."""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'eventease/admin/announcement_form.html'
    success_url = reverse_lazy('announcement-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Announcement updated successfully!')
        return super().form_valid(form)


class AnnouncementDeleteView(AdminRequiredMixin, DeleteView):
    """Admin view to delete announcements."""
    model = Announcement
    template_name = 'eventease/admin/announcement_confirm_delete.html'
    success_url = reverse_lazy('announcement-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Announcement deleted successfully!')
        return super().delete(request, *args, **kwargs)

