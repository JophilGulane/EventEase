from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Event, Announcement
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class EventForm(forms.ModelForm):
    """Form for creating and updating Event instances."""
    
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'start_datetime',
            'end_datetime',
            'venue',
            'capacity',
            'registration_deadline',
            'points',
            'is_public',
            'pinned',
            'image',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'placeholder': 'Enter a compelling event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white resize-none',
                'rows': 5,
                'placeholder': 'Describe your event in detail...'
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'type': 'datetime-local'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'type': 'datetime-local'
            }),
            'venue': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'placeholder': 'Event location or venue'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'placeholder': 'Leave blank for unlimited capacity',
                'min': 1
            }),
            'registration_deadline': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'type': 'datetime-local'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'placeholder': 'Leave blank for default (10 points)',
                'min': 0
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer'
            }),
            'pinned': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer'
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer',
                'accept': 'image/*'
            }),
        }
        
        labels = {
            'title': 'Event Title',
            'description': 'Description',
            'start_datetime': 'Start Date & Time',
            'end_datetime': 'End Date & Time',
            'venue': 'Venue',
            'capacity': 'Capacity',
            'registration_deadline': 'Registration Deadline',
            'points': 'Points Awarded',
            'is_public': 'Make this event public',
            'pinned': 'Pin to top',
            'image': 'Event Image',
        }
        
        help_texts = {
            'capacity': 'Leave blank for unlimited capacity',
            'registration_deadline': 'Participants cannot register after this date',
            'points': 'Points participants will receive when attending this event. Leave blank for default (10 points).',
            'is_public': 'Public events are visible to all users',
            'pinned': 'Pinned events appear at the top of the list',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise forms.ValidationError(
                    "End datetime must be after start datetime."
                )
        
        if registration_deadline and start_datetime:
            if registration_deadline > start_datetime:
                raise forms.ValidationError(
                    "Registration deadline must be before event start time."
                )
        
        return cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """Extended user registration form with email and name fields."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name (optional)',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name (optional)',
            'autocomplete': 'family-name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
        # Remove password validation help text
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class AnnouncementForm(forms.ModelForm):
    """Form for creating and updating Announcement instances."""
    
    class Meta:
        model = Announcement
        fields = [
            'title',
            'content',
            'expires_at',
            'pinned',
            'image',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'placeholder': 'Enter announcement title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white resize-none',
                'rows': 8,
                'placeholder': 'Write your announcement content here...'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white',
                'type': 'datetime-local'
            }),
            'pinned': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer'
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer',
                'accept': 'image/*'
            }),
        }
        
        labels = {
            'title': 'Announcement Title',
            'content': 'Content',
            'expires_at': 'Expiration Date & Time',
            'pinned': 'Pin to top',
            'image': 'Announcement Image',
        }
        
        help_texts = {
            'expires_at': 'Leave blank if this announcement should never expire',
            'pinned': 'Pinned announcements appear at the top of the list',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        expires_at = cleaned_data.get('expires_at')
        
        if expires_at:
            if expires_at < timezone.now():
                raise forms.ValidationError(
                    "Expiration date cannot be in the past."
                )
        
        return cleaned_data

