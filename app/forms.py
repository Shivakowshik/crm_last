import re
from django import forms
from .models import Agent, Client, Campaign, Attendance
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

from django import forms
from .models import Agent

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = [
            'full_name', 'email', 'phone_number', 'address', 
            'certifications', 'languages', 'experience', 
            'specialization', 'profile_picture', 'pan_card', 
            'aadhaar_card'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'certifications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Enter certifications separated by commas'}),
            'languages': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'experience': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'specialization': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'pan_card': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhaar_card': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.user:
            instance.user.username = instance.email
            if commit:
                instance.user.save()

        # Process 'languages' field
        languages = self.cleaned_data.get('languages')
        if isinstance(languages, list):
            instance.languages = [lang.strip() for lang in languages]
        elif isinstance(languages, str):
            instance.languages = [lang.strip() for lang in languages.split(',')]

        if commit:
            instance.save()

        return instance

    def clean_languages(self):
        # Ensure 'languages' is a list and at least one language is selected
        languages = self.cleaned_data.get('languages', [])
        if not languages:
            raise forms.ValidationError("Please select at least one language.")
        return languages

    def clean_experience(self):
        # Ensure 'experience' is treated as plain text
        experience = self.cleaned_data.get('experience')
        if not experience:
            raise forms.ValidationError("Experience field cannot be empty.")
        return experience.strip()

    def clean_specialization(self):
        # Ensure 'specialization' is treated as plain text
        specialization = self.cleaned_data.get('specialization')
        if not specialization:
            raise forms.ValidationError("Specialization field cannot be empty.")
        return specialization.strip()

    def clean_certifications(self):
        # Ensure 'certifications' is a plain text
        certifications = self.cleaned_data.get('certifications')
        return certifications.strip() if certifications else ""

    def clean_pan_card(self):
        pan_card = self.cleaned_data.get('pan_card')
        if pan_card and (
            len(pan_card) != 10 or not pan_card.isalnum() or 
            not pan_card[:5].isalpha() or not pan_card[5:9].isdigit() or 
            not pan_card[-1].isalpha()
        ):
            raise forms.ValidationError("PAN Card number must be valid (ABCDE1234F format).")
        return pan_card

    def clean_aadhaar_card(self):
        aadhaar_card = self.cleaned_data.get('aadhaar_card')
        if aadhaar_card and (len(aadhaar_card) != 12 or not aadhaar_card.isdigit()):
            raise forms.ValidationError("Aadhaar Card number must be exactly 12 digits.")
        return aadhaar_card

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if len(phone_number) != 10 or not phone_number.isdigit():
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Agent.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email



class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'dob', 'address', 
            'aadhar', 'pan', 'insurance_type', 'policy_number', 'photo'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'aadhar': 'Aadhar Number',
            'pan': 'PAN Number',
        }

    # Validator to ensure the policy number matches the required format
    def clean_policy_number(self):
        policy_number = self.cleaned_data.get('policy_number')
        if policy_number and not re.match(r'^P\d{9}$', policy_number):
            raise forms.ValidationError('Policy number must start with "P" followed by 9 digits (e.g., P123456789).')
        return policy_number

class CampaignForm(forms.ModelForm):
    agent = forms.ModelChoiceField(queryset=Agent.objects.all(), empty_label="Select an Agent", required=True)

    class Meta:
        model = Campaign
        fields = ['agent', 'campaign_name', 'location', 'start_date', 'end_date', 'budget', 'banner_image']


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['location']

class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_new_password1(self):
        new_password = self.cleaned_data.get('new_password1')
        old_password = self.cleaned_data.get('old_password')

        # Check if old and new passwords are the same
        if new_password == old_password:
            raise ValidationError("The new password cannot be the same as the old password.")
        
        return new_password
