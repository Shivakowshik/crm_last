from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

def get_default_user():
    """
    Fetch the default admin user if available.
    """
    return User.objects.filter(username='admin').first()

class Agent(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="agent", 
        null=True, 
        blank=True
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, unique=True)
    address = models.TextField(max_length=250)
    certifications = models.CharField(max_length=200, blank=True, null=True)
    languages = models.JSONField(blank=True, null=True)  # Store list of languages
    experience = models.CharField(max_length=200, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='agent_profiles/', blank=True, null=True)
    pan_card = models.CharField(max_length=10, unique=True, blank=True, null=True)
    aadhaar_card = models.CharField(max_length=12, unique=True, blank=True, null=True)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def __str__(self):
        return self.full_name


class Client(models.Model):
    INSURANCE_TYPE_CHOICES = [
        ('Health', 'Health Insurance'),
        ('Life', 'Life Insurance'),
        ('Vehicle', 'Vehicle Insurance'),
        ('Home', 'Home Insurance'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, max_length=100)
    phone = models.CharField(max_length=10, unique=True)
    dob = models.DateField()
    address = models.CharField(max_length=200)
    aadhar = models.CharField(max_length=12, unique=True)
    pan = models.CharField(max_length=10, unique=True)
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPE_CHOICES)
    policy_number = models.CharField(max_length=20, unique=True)
    photo = models.ImageField(upload_to='client_photos/', blank=True, null=True)
    join_date = models.DateField(default=timezone.now)
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="clients"
    )
    is_collected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# Models
from django.db import models

class Campaign(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]

    agent = models.ForeignKey(
        'Agent', 
        on_delete=models.CASCADE, 
        related_name="campaigns"
    )
    campaign_name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    banner_image = models.ImageField(upload_to='campaign_banners/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return self.campaign_name
    
    

class Attendance(models.Model):
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.SET_NULL, 
        null=True
    )
    location = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"Attendance for {self.agent.full_name if self.agent else 'Unknown'} on {self.date}"
