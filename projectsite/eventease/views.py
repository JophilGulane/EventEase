from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F, Case, When, IntegerField
from .models import Event, Announcement, UserProfile, Registration
from .forms import EventForm, CustomUserCreationForm
from .mixins import AdminRequiredMixin, SuperAdminRequiredMixin

# Create your views here.

class LandingPageView(ListView):
    """Display landing page with featured events."""
    model = Event
    template_name = 'landing.html'
    context_object_name = 'landing'
    allow_empty = True
    
    def get_queryset(self):
        """Return top 3 upcoming and ongoing public events, prioritized by points."""
        now = timezone.now()
        
        # Annotate with points value (use 10 as default if null)
        events = Event.objects.filter(
            is_public=True,
            end_datetime__gte=now  # Events that haven't ended yet (includes ongoing and upcoming)
        ).annotate(
            points_value=Case(
                When(points__isnull=False, then=F('points')),
                default=10,
                output_field=IntegerField()
            )
        ).order_by(
            '-pinned',  # Pinned events first
            '-points_value',  # Then by points (highest first)
            'start_datetime'  # Finally by start date
        )[:3]  # Limit to 3 events
        
        return events


# Event CRUD Views
class EventListView(LoginRequiredMixin, ListView):
    """List all public events. Requires login."""
    model = Event
    template_name = 'eventease/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        """Return events based on user role. Admin see all, others see public only."""
        # Admin can see all events (including private)
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin():
            queryset = Event.objects.all()
        else:
            queryset = Event.objects.filter(is_public=True)
        
        # Filter by upcoming/past if requested
        filter_type = self.request.GET.get('filter', 'all')
        now = timezone.now()
        
        if filter_type == 'upcoming':
            queryset = queryset.filter(start_datetime__gte=now)
        elif filter_type == 'past':
            queryset = queryset.filter(end_datetime__lt=now)
        
        return queryset.order_by('-pinned', '-start_datetime')
    
    def get_context_data(self, **kwargs):
        """Add current time to context for template comparisons."""
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    """Display detailed view of a single event. Requires login."""
    model = Event
    template_name = 'eventease/event_detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        """Allow viewing public events or events created by the user."""
        # Admin can see all events
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin():
            return Event.objects.all()
        return Event.objects.filter(
            Q(is_public=True) | Q(created_by=self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        """Add registration status for the logged-in user."""
        context = super().get_context_data(**kwargs)
        event = context['event']
        
        # User is always authenticated (LoginRequiredMixin ensures this)
        try:
            registration = Registration.objects.get(
                event=event,
                user=self.request.user
            )
            context['user_registration'] = registration
            context['is_registered'] = True
            context['registration_status'] = registration.status
        except Registration.DoesNotExist:
            context['is_registered'] = False
            context['registration_status'] = None
        
        # Check if registration is still possible
        now = timezone.now()
        context['can_register'] = (
            event.is_public and
            (event.registration_deadline is None or event.registration_deadline > now) and
            event.start_datetime > now and
            not event.is_full()
        )
        
        return context


class EventCreateView(AdminRequiredMixin, CreateView):
    """Create a new event. Only Admin can create events."""
    model = Event
    form_class = EventForm
    template_name = 'eventease/event_form.html'
    success_url = reverse_lazy('event-list')
    
    def form_valid(self, form):
        """Set the created_by field to the current user."""
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Event created successfully!')
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing event."""
    model = Event
    form_class = EventForm
    template_name = 'eventease/event_form.html'
    success_url = reverse_lazy('event-list')
    
    def get_queryset(self):
        """Allow Admin to edit any event, or users to edit their own."""
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin():
            return Event.objects.all()
        return Event.objects.filter(created_by=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Event updated successfully!')
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, DeleteView):
    """Delete an event."""
    model = Event
    template_name = 'eventease/event_confirm_delete.html'
    success_url = reverse_lazy('event-list')
    
    def get_queryset(self):
        """Allow Admin to delete any event, or users to delete their own."""
        if hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin():
            return Event.objects.all()
        return Event.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Event deleted successfully!')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# ANNOUNCEMENTS/NEWSFEED VIEW
# ============================================================================

class AnnouncementsNewsfeedView(LoginRequiredMixin, ListView):
    """Display page showing only announcements. Requires login."""
    model = Announcement
    template_name = 'eventease/announcements_newsfeed.html'
    context_object_name = 'announcements'
    paginate_by = 20
    
    def get_queryset(self):
        """Return only active announcements."""
        now = timezone.now()
        return Announcement.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).order_by('-pinned', '-created_at')


# ============================================================================
# LEADERBOARD VIEW
# ============================================================================

class LeaderboardView(ListView):
    """Display leaderboard of users ranked by total points."""
    model = UserProfile
    template_name = 'eventease/leaderboard.html'
    context_object_name = 'profiles'
    paginate_by = 25
    
    def get_queryset(self):
        """Return user profiles ordered by total_points descending, then by username."""
        queryset = UserProfile.objects.select_related('user').filter(
            user__is_active=True
        ).order_by('-total_points', 'user__username')
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add current user's rank and position."""
        context = super().get_context_data(**kwargs)
        
        # Calculate ranks for displayed users
        queryset = self.get_queryset()
        page_obj = context['page_obj']
        
        # Calculate ranks for all profiles (handling ties correctly)
        all_profiles = list(queryset)
        rank_map = {}  # Maps profile ID to rank
        current_rank = 1
        
        for idx, profile in enumerate(all_profiles):
            # If this profile has different points than the previous one, update rank
            if idx > 0 and all_profiles[idx-1].total_points != profile.total_points:
                current_rank = idx + 1
            rank_map[profile.id] = current_rank
        
        # Build list for current page only
        profiles_with_rank = []
        for profile in page_obj:
            profiles_with_rank.append({
                'profile': profile,
                'rank': rank_map.get(profile.id, 1),
                'is_current_user': self.request.user.is_authenticated and 
                                  hasattr(self.request.user, 'profile') and
                                  profile.user == self.request.user,
            })
        
        context['profiles_with_rank'] = profiles_with_rank
        
        # Get current user's rank if authenticated
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            user_profile = self.request.user.profile
            if user_profile.id in rank_map:
                context['user_rank'] = rank_map[user_profile.id]
                context['user_profile'] = user_profile
        
        # Get top 3 for podium display
        top_3 = all_profiles[:3] if len(all_profiles) >= 3 else all_profiles
        context['top_3'] = top_3
        
        return context


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class SignUpView(CreateView):
    """User registration view."""
    form_class = CustomUserCreationForm
    template_name = 'account/signup.html'
    success_url = reverse_lazy('landing')
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect authenticated users."""
        if request.user.is_authenticated:
            return redirect('landing')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """After successful signup, log the user in."""
        response = super().form_valid(form)
        # UserProfile is created automatically via signal
        login(self.request, self.object)
        messages.success(self.request, f'Welcome to EventEase+, {self.object.username}! Your account has been created successfully.')
        return response


class LoginView(AuthLoginView):
    """Custom login view with redirect to landing page."""
    template_name = 'account/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to landing page after login."""
        return reverse_lazy('landing')
    
    def form_invalid(self, form):
        """Add error message for invalid login."""
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


class LogoutView(AuthLogoutView):
    """Custom logout view."""
    next_page = reverse_lazy('landing')
    
    def dispatch(self, request, *args, **kwargs):
        """Show logout message."""
        if request.user.is_authenticated:
            messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# USER REGISTRATION & PROFILE VIEWS
# ============================================================================

class RegisterForEventView(LoginRequiredMixin, View):
    """Register user for an event."""
    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id, is_public=True)
        
        # Check if registration is still possible
        now = timezone.now()
        if event.registration_deadline and event.registration_deadline < now:
            messages.error(request, 'Registration deadline has passed.')
            return redirect('event-detail', pk=event_id)
        
        if event.start_datetime < now:
            messages.error(request, 'This event has already started.')
            return redirect('event-detail', pk=event_id)
        
        if event.is_full():
            messages.error(request, 'This event is full.')
            return redirect('event-detail', pk=event_id)
        
        # Check if already registered
        registration, created = Registration.objects.get_or_create(
            event=event,
            user=request.user,
            defaults={'status': Registration.Status.PRE_REGISTERED}
        )
        
        if created:
            messages.success(request, f'Successfully pre-registered for "{event.title}"!')
        else:
            if registration.status == Registration.Status.CANCELLED:
                registration.status = Registration.Status.PRE_REGISTERED
                registration.registered_at = timezone.now()
                registration.save()
                messages.success(request, f'Successfully re-registered for "{event.title}"!')
            else:
                messages.info(request, 'You are already registered for this event.')
        
        return redirect('event-detail', pk=event_id)


class UnregisterFromEventView(LoginRequiredMixin, View):
    """Cancel user registration for an event."""
    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        
        try:
            registration = Registration.objects.get(
                event=event,
                user=request.user
            )
            registration.status = Registration.Status.CANCELLED
            registration.save()
            messages.success(request, f'Registration cancelled for "{event.title}".')
        except Registration.DoesNotExist:
            messages.error(request, 'You are not registered for this event.')
        
        return redirect('event-detail', pk=event_id)


class UserProfileView(LoginRequiredMixin, TemplateView):
    """Display user profile with points and registration history."""
    template_name = 'eventease/user_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if hasattr(user, 'profile'):
            profile = user.profile
            context['profile'] = profile
            
            # Get points transactions
            context['points_transactions'] = profile.points_transactions.all()[:20]
            context['total_transactions'] = profile.points_transactions.count()
            
            # Get user registrations
            registrations = Registration.objects.filter(user=user).select_related('event').order_by('-registered_at')[:20]
            context['registrations'] = registrations
            context['total_registrations'] = Registration.objects.filter(user=user).count()
            
            # Get upcoming registrations
            now = timezone.now()
            upcoming_registrations = [
                reg for reg in registrations
                if reg.event.start_datetime > now and reg.status != Registration.Status.CANCELLED
            ]
            context['upcoming_registrations'] = upcoming_registrations
            
            # Stats
            attended_count = Registration.objects.filter(
                user=user,
                status=Registration.Status.ATTENDED
            ).count()
            context['attended_count'] = attended_count
        
        return context


class MyRegistrationsView(LoginRequiredMixin, ListView):
    """Display all user registrations."""
    model = Registration
    template_name = 'eventease/my_registrations.html'
    context_object_name = 'registrations'
    paginate_by = 20
    
    def get_queryset(self):
        """Get all registrations for the current user, optionally filtered by status."""
        queryset = Registration.objects.filter(
            user=self.request.user
        ).select_related('event').order_by('-registered_at')
        
        # Filter by status if requested
        status_filter = self.request.GET.get('status', 'all')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        status_filter = self.request.GET.get('status', 'all')
        context['current_filter'] = status_filter
        
        # Calculate stats from all registrations (not filtered)
        all_registrations = Registration.objects.filter(user=self.request.user).select_related('event')
        context['total_registrations'] = all_registrations.count()
        
        upcoming = [
            r for r in all_registrations
            if r.event.start_datetime > now and r.status != Registration.Status.CANCELLED
        ]
        context['upcoming_count'] = upcoming
        context['attended_count'] = all_registrations.filter(status=Registration.Status.ATTENDED).count()
        
        return context