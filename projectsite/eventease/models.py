# events/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F
from django.dispatch import receiver
from django.db.models.signals import post_save

User = get_user_model()


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.USER)
    phone = models.CharField(max_length=20, blank=True)
    course = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)  # optional (install Pillow)
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role})"
    
    def is_admin(self):
        """Check if user is Admin (either through role or Django superuser)."""
        # Django superusers are also considered admins
        if self.user.is_superuser:
            return True
        return self.role == self.Role.ADMIN
    
    def is_user(self):
        """Check if user is User."""
        return self.role == self.Role.USER
    
    def can_manage_events(self):
        """Check if user can create/manage events."""
        return self.is_admin()  # Includes superusers
    
    def can_manage_announcements(self):
        """Check if user can manage announcements."""
        return self.is_admin()  # Includes superusers

    def add_points(self, amount, reason="", event=None):
        """Add points and create a transaction record."""
        if amount == 0:
            return
        self.total_points = F("total_points") + amount
        self.save(update_fields=["total_points"])
        # Refresh from DB to get numeric value after F-expression update
        self.refresh_from_db(fields=["total_points"])
        PointsTransaction.objects.create(
            user_profile=self,
            amount=amount,
            reason=reason,
            event=event,
            balance_after=self.total_points,
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_events")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    venue = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    registration_deadline = models.DateTimeField(null=True, blank=True)
    points = models.PositiveIntegerField(null=True, blank=True, help_text="Points to award when attending this event. Leave blank to use default (10 points).")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to="event_images/", null=True, blank=True)  # optional
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ("-start_datetime",)
        indexes = [
            models.Index(fields=["start_datetime"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    def is_upcoming(self):
        return timezone.now() < self.start_datetime

    @property
    def registered_count(self):
        return self.registrations.filter(status=Registration.Status.PRE_REGISTERED).count()

    def available_slots(self):
        if self.capacity is None:
            return None  # unlimited
        return max(self.capacity - self.registered_count, 0)

    def is_full(self):
        if self.capacity is None:
            return False
        return self.registered_count >= self.capacity
    
    def get_points(self):
        """Return the points for this event, or default if not set."""
        return self.points if self.points is not None else 10


class Registration(models.Model):
    class Status(models.TextChoices):
        PRE_REGISTERED = "PRE", "Pre-registered"
        CONFIRMED = "CONFIRMED", "Confirmed"
        ATTENDED = "ATTENDED", "Attended"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No-show"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registrations")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PRE_REGISTERED)
    registered_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("event", "user")
        ordering = ("-registered_at",)
        indexes = [
            models.Index(fields=["event", "status"]),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.event.title} ({self.status})"

    def mark_attended(self, award_points=0, reason="Participation"):
        """Mark attendance and optionally award points."""
        self.status = self.Status.ATTENDED
        self.checked_in_at = timezone.now()
        self.save(update_fields=["status", "checked_in_at"])
        if award_points and hasattr(self.user, "profile"):
            self.user.profile.add_points(amount=award_points, reason=reason, event=self.event)


class PointsTransaction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="points_transactions")
    amount = models.IntegerField()  # positive or negative
    reason = models.CharField(max_length=255, blank=True)
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    balance_after = models.IntegerField()

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.user_profile.user.username}: {sign}{self.amount} ({self.reason})"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="announcements")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    pinned = models.BooleanField(default=False)
    image = models.ImageField(upload_to="announcement_images/", null=True, blank=True)  # optional

    class Meta:
        ordering = ("-pinned", "-created_at")
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    def is_active(self):
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True
