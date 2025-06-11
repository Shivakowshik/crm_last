import json
import random
import string
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.core.paginator import Paginator
from .forms import AgentForm, ClientForm, CampaignForm, AttendanceForm, CustomPasswordChangeForm
from .models import Agent, Client, Campaign, Attendance
from django.db.models import Count, Sum
import calendar
from django.db.models.functions import ExtractMonth





# Agent Navigation View
def agent_nav(request):
    agent = Agent.objects.filter(user=request.user).first()
    return render(request, 'agent_nav.html', {'agent': agent})


# Homepage View
from django.db.models import Count, F

def homepage(request):
    """
    Render the CRM Insurance Dashboard with data dynamically retrieved from models.
    """
    # Fetch total counts
    total_policies = Client.objects.count()  # Assuming Client has policies
    total_clients = Client.objects.count()
    total_agents = Agent.objects.count()
    total_campaigns = Campaign.objects.count()
    total_campaigns_budget = Campaign.objects.aggregate(total_budget=Sum('budget'))['total_budget'] or 0

    # Data for charts
    policy_data = Client.objects.values('insurance_type').annotate(count=Count('id'))
    policy_chart_data = {
        'labels': [item['insurance_type'] for item in policy_data],
        'data': [item['count'] for item in policy_data]
    }

    campaigns_data = Campaign.objects.annotate(month=ExtractMonth('start_date')).values('month').annotate(count=Count('id')).order_by('month')
    campaigns_chart_data = {
        'labels': [calendar.month_name[item['month']] for item in campaigns_data if item['month']],
        'data': [item['count'] for item in campaigns_data]
    }

    client_chart_data = policy_chart_data  # Assuming this data is similar for policies and clients

    # Prepare context
    context = {
        'total_policies': total_policies,
        'total_clients': total_clients,
        'total_agents': total_agents,
        'total_campaigns': total_campaigns,
        'total_campaigns_budget': total_campaigns_budget,
        'policy_chart_data': json.dumps(policy_chart_data),  # Serialize to JSON
        'client_chart_data': json.dumps(client_chart_data),  # Serialize to JSON
        'campaigns_chart_data': json.dumps(campaigns_chart_data),  # Serialize to JSON
    }

    return render(request, 'homepage.html', context)


# Admin Home View
def admin_home(request):
    """
    View to render the admin dashboard with data for charts.
    """

    # Data for Bar Chart: Monthly Agent Registrations
    agent_data = (
        Agent.objects.annotate(month=ExtractMonth('user__date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    bar_chart_data = {
        'labels': [calendar.month_name[item['month']] for item in agent_data if item['month']],
        'data': [item['count'] for item in agent_data],
    }

    # Data for Line Chart: Campaign Budgets Over Time
    campaign_data = (
        Campaign.objects.annotate(month=ExtractMonth('start_date'))
        .values('month')
        .annotate(total_budget=Sum('budget'))
        .order_by('month')
    )
    line_chart_data = {
        'labels': [calendar.month_name[item['month']] for item in campaign_data if item['month']],
        'data': [float(item['total_budget']) for item in campaign_data],
    }

    # Data for Pie Chart: Insurance Type Distribution
    insurance_data = (
        Client.objects.values('insurance_type')
        .annotate(count=Count('id'))
    )
    pie_chart_data = {
        'labels': [item['insurance_type'] for item in insurance_data],
        'data': [item['count'] for item in insurance_data],
    }

    # Context for the template
    context = {
        'bar_chart_data': json.dumps(bar_chart_data),
        'line_chart_data': json.dumps(line_chart_data),
        'pie_chart_data': json.dumps(pie_chart_data),
    }

    return render(request, 'admin_home.html', context)




@login_required
def agent_home(request):
    try:
        # Fetch the Agent instance for the logged-in user
        agent = Agent.objects.get(user=request.user)

        # Get the current month
        current_month = datetime.now().month

        # Get the total number of clients added this month by this agent
        clients_added_count = Client.objects.filter(agent=agent, join_date__month=current_month).count()

        # Get the total number of campaigns created this month by this agent
        campaigns_count = Campaign.objects.filter(agent=agent, start_date__month=current_month).count()

        # Get the total number of collected clients for this agent
        collected_clients_count = Client.objects.filter(agent=agent, is_collected=True).count()

        # Calculate the number of clients added this month (for the chart)
        clients_this_month = Client.objects.filter(agent=agent, join_date__month=current_month).count()

        # Calculate the number of campaigns in this month (for the chart)
        campaigns_this_month = Campaign.objects.filter(agent=agent, start_date__month=current_month).count()

        # Pass data to template context
        context = {
            'clients_added_count': clients_added_count,
            'campaigns_count': campaigns_count,
            'collected_clients_count': collected_clients_count,
            'clients_this_month_data': clients_this_month,
            'campaigns_this_month_data': campaigns_this_month,
        }

        return render(request, 'agent_home.html', context)
    
    except Agent.DoesNotExist:
        # Handle case when the Agent doesn't exist (maybe user is not an Agent)
        messages.error(request, "You are not authorized to view this page.")
        return redirect('login')  # Redirect to login or some other page





# Login View
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successful!")  # Add success message
            return redirect('admin_home' if user.is_superuser else 'agent_home')
        else:
            messages.error(request, "Invalid username or password!")  # Add error message
    return render(request, 'login.html')



# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out!")
    return redirect('login')






# Generate Agent Code
def generate_agent_code():
    letter = random.choice(string.ascii_uppercase)
    number = random.randint(1, 999)
    return f"{letter}{number:03d}"


# Add Agent View
def add_agent(request):
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    email = form.cleaned_data['email']

                    if User.objects.filter(email=email).exists() or Agent.objects.filter(email=email).exists():
                        messages.error(request, "An account with this email already exists.")
                        return redirect('add_agent')

                    agent = form.save(commit=False)
                    agent.save()

                    # Notify agent about approval pending
                    subject = "Agent Registration Pending Approval"
                    message = f"""
                    Dear {agent.full_name},

                    Your registration has been received and is pending admin approval. 
                    Once approved, you will receive your login credentials.

                    Best regards,
                    CRM Insurance
                    """
                    send_mail(subject, message, 'admin@example.com', [email], fail_silently=False)

                    messages.success(request, "Agent registered successfully! Pending admin approval.")
                    return redirect('add_agent')

            except IntegrityError as e:
                messages.error(request, f"Failed to add agent due to a database error: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AgentForm()

    return render(request, 'add_agent.html', {'form': form})



@login_required
def add_agent_admin(request):
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    email = form.cleaned_data['email']

                    # Check if email already exists in User or Agent model
                    if User.objects.filter(email=email).exists() or Agent.objects.filter(email=email).exists():
                        messages.error(request, "An account with this email already exists.")
                        return redirect('add_agent_admin')

                    # Save the agent instance
                    agent = form.save(commit=False)
                    agent.save()

                    # Generate agent code and user credentials
                    agent_code_prefix = "X"
                    new_code = f"{agent_code_prefix}{agent.id:03d}"
                    username = email
                    password = str(random.randint(100000, 999999))

                    # Create user account for the agent
                    user = User.objects.create_user(username=username, password=password, email=email)
                    agent.user = user
                    agent.code = new_code
                    agent.save()

                    # Notify the agent with login credentials
                    subject = "Agent Registration Successful - Login Credentials"
                    message = f"""
                    Dear {agent.full_name},

                    Your registration is successful! Below are your login credentials:

                    Username: {username}
                    Password: {password}

                    Your agent code: {new_code}

                    Please log in and change your password upon first login.

                    Best regards,
                    CRM Insurance
                    """
                    send_mail(subject, message, 'admin@example.com', [email], fail_silently=False)

                    messages.success(request, "Agent registered successfully! Login credentials have been sent.")
                    return redirect('add_agent_admin')

            except IntegrityError as e:
                messages.error(request, f"Failed to add agent due to a database error: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AgentForm()

    return render(request, 'add_agent_admin.html', {'form': form})





# Approve Agent View
@login_required
def approve_agent_view(request):
    if request.method == "POST":
        agent_id = request.POST.get('agent_id')
        action = request.POST.get('action')
        agent = Agent.objects.get(id=agent_id)

        if action == "approve":
            agent_code_prefix = "X"
            new_code = f"{agent_code_prefix}{agent.id:03d}"
            username = agent.email

            if User.objects.filter(username=username).exists():
                messages.error(request, f"A user with the email {username} already exists.")
                return redirect('approve_agent')

            password = str(random.randint(100000, 999999))
            user = User.objects.create_user(username=username, password=password, email=agent.email)
            agent.user = user
            agent.code = new_code
            agent.save()

            subject = "Agent Approval - Login Credentials"
            message = f"""
            Dear {agent.full_name},

            Your agent account has been approved. Below are your login credentials:

            Username: {username}
            Password: {password}

            Your agent code: {new_code}

            Please log in and change your password upon first login.

            Best regards,
            Admin Team, CRM Insurance
            """
            send_mail(subject, message, 'admin@example.com', [agent.email], fail_silently=False)

            messages.success(request, f"Agent {agent.full_name} approved successfully with code {new_code}!")

        elif action == "reject":
            subject = "Agent Application Rejection"
            message = f"""
            Dear {agent.full_name},

            We are sorry to inform you that your application has been rejected. Please try again next time.

            Best regards,
            Admin Team, CRM Insurance
            """
            send_mail(subject, message, 'admin@example.com', [agent.email], fail_silently=False)

            agent.delete()

            messages.success(request, f"Agent {agent.full_name} has been rejected and removed.")

        return redirect('approve_agent')

    pending_agents = Agent.objects.filter(user__isnull=True)
    return render(request, 'approve_agent.html', {'pending_agents': pending_agents})


# Delete Agent View
@login_required
def delete_agent(request, agent_id):
    try:
        agent = get_object_or_404(Agent, id=agent_id)
        user = agent.user
        with transaction.atomic():
            agent.delete()
            user.delete()

        messages.success(request, "Agent deleted successfully!")
    except Exception as e:
        messages.error(request, f"Failed to delete agent: {e}")

    return redirect('view_agents')




# Agent Profile View
@login_required
def agent_profile(request):
    agent = get_object_or_404(Agent, user=request.user)
    return render(request, 'agent_profile.html', {'agent': agent})


# Edit Agent Profile View
@login_required
def edit_agent_profile(request, agent_id):
    agent = get_object_or_404(Agent, id=agent_id)
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('agent_profile')  # Replace with the appropriate redirect
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AgentForm(instance=agent)
    return render(request, 'edit_agent_profile.html', {'form': form, 'agent': agent})


# Change Password View
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in after the password change
            messages.success(request, "Your password was successfully updated!")
            return redirect('agent_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate a random 6-digit password
            random_password = get_random_string(length=6, allowed_chars='0123456789')
            user.set_password(random_password)
            user.save()

            # Send email with the new password and additional details
            email_subject = 'Your New Password'
            email_body = (
                f"Dear {user.username},\n\n"
                f"We have generated a new password for your account as requested:\n\n"
                f"New Password: {random_password}\n\n"
                f"Please use this password to log in and change your password immediately for security reasons.\n\n"
                f"If you did not request this password reset, please contact our support team immediately.\n\n"
                f"Best regards,\n"
                f"The Support Team\n"
            )
            send_mail(
                email_subject,
                email_body,
                'noreply@example.com',  # Replace with your sender email
                [email],
                fail_silently=False,
            )
            messages.success(request, "A new password has been sent to your email.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")
    return render(request, 'forgot_password.html')


# View Agents
@login_required
def view_agents(request):
    agents = Agent.objects.all()
    return render(request, 'view_agents.html', {'agents': agents})

@login_required
def edit_agent_admin(request, agent_id):
    # Fetch the agent object based on the provided agent_id
    agent = get_object_or_404(Agent, id=agent_id)

    if request.method == 'POST':
        # If the request is POST, the user has submitted the form
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            updated_agent = form.save(commit=False)  # Save changes without committing yet
            if updated_agent.user:  # Check if the agent is linked to a user
                updated_agent.user.username = updated_agent.email  # Update username to match email
                updated_agent.user.save()  # Save changes to the user object
            updated_agent.save()  # Save changes to the agent object
            messages.success(request, "Agent updated successfully.")
            return redirect('view_agents')  # Redirect to the list of agents
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Create a form instance pre-filled with agent data
        form = AgentForm(instance=agent)

    return render(request, 'edit_agent_admin.html', {'form': form, 'agent': agent})



# Add Client
@login_required
def add_client(request):
    try:
        # Ensure the logged-in user is associated with an Agent
        agent = get_object_or_404(Agent, user=request.user)
    except Agent.DoesNotExist:
        messages.error(request, "You are not associated with an agent profile.")
        return redirect('agent_home')  # Redirect to a suitable page

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.save(commit=False)
            client.join_date = now()
            client.agent = agent  # Assign the logged-in agent
            client.save()
            messages.success(request, "Client added successfully!")
            return redirect('collected_clients')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClientForm()

    return render(request, 'add_client.html', {'form': form})


# Collected Clients
@login_required
def collected_clients(request):
    try:
        # Retrieve the logged-in agent's profile
        agent = get_object_or_404(Agent, user=request.user)
        # Fetch clients linked to the agent
        clients = Client.objects.filter(agent=agent)
        return render(request, 'collected_clients.html', {'clients': clients})
    except Agent.DoesNotExist:
        messages.error(request, "You are not associated with an agent profile.")
        return redirect('agent_home')


# Clients List
@login_required
def clients(request, agent_id):
    """
    View to display clients for a specific agent, with pagination.
    """
    agent = get_object_or_404(Agent, id=agent_id)
    clients = agent.clients.all() 
    paginator = Paginator(clients, 10)  
    page_number = request.GET.get('page')
    page_clients = paginator.get_page(page_number)

    return render(request, 'clients.html', {
        'agent': agent,
        'clients': page_clients,
    })

# Delete Client (Agent)
@login_required
def delete_client(request, client_id):
    try:
        # Fetch the logged-in agent's clients and delete the specific client
        agent = get_object_or_404(Agent, user=request.user)
        client = get_object_or_404(Client, id=client_id, agent=agent)
        client.delete()
        messages.success(request, "Client deleted successfully!")
    except Client.DoesNotExist:
        messages.error(request, "Client not found or not associated with you.")
    return redirect('collected_clients')


# Delete Client (Admin)
@login_required
def delete_client_admin(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    messages.success(request, "Client deleted successfully!")
    return redirect('clients')


# Edit Client
@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully.')
            return redirect('collected_clients')  # Redirect after successful edit
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClientForm(instance=client)

    return render(request, 'edit_client.html', {'form': form, 'client': client})


@login_required
def add_attendance(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            # Ensure the user has an associated agent
            if hasattr(request.user, 'agent'):
                attendance.agent = request.user.agent  
                attendance.save()  # Save the attendance record
                messages.success(request, "Attendance added successfully!")
                return redirect('add_attendance')
            else:
                messages.error(request, "You are not associated with any agent.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AttendanceForm()

    return render(request, 'add_attendance.html', {
        'form': form,
        'current_date': now().strftime('%Y-%m-%d'),
        'current_time': now().strftime('%H:%M:%S'),  
    })


# Agent Location (View Attendance)
@login_required
def agent_location(request):
    # Fetch attendance records along with related agent information 
    attendance_records = Attendance.objects.select_related('agent').all()
    return render(request, 'agent_location.html', {'attendance_records': attendance_records})




@login_required
def campaigns_list(request):
    # Fetch campaigns and order by status and start date
    campaigns = Campaign.objects.all().order_by('-status', 'start_date')
    return render(request, 'campaigns_list.html', {'campaigns': campaigns})

# Create Campaign
@login_required
def create_campaign_view(request):
    if request.method == "POST":
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Campaign created successfully!")
            return redirect('campaigns_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CampaignForm()

    # Fetching all agents from the database to pass to the template
    agents = Agent.objects.all()

    return render(request, 'create_campaign.html', {'form': form, 'agents': agents})

# Edit Campaign
@login_required

def edit_campaign(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    agents = Agent.objects.all()

    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, "Campaign updated successfully!")
                    return redirect('campaigns_list')
            except Exception as e:
                messages.error(request, f"An error occurred while updating the campaign: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = CampaignForm(instance=campaign)

    return render(request, 'edit_campaigns.html', {
        'form': form,
        'campaign': campaign,
        'agents': agents,
    })



# Delete Campaign
@login_required
def delete_campaign(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    campaign.delete()
    messages.success(request, "Campaign deleted successfully!")
    return redirect('campaigns_list')

# Agent's Assigned Campaigns
@login_required
def agent_campaigns(request):
    """
    View to display campaigns assigned to the currently logged-in agent.
    """
    try:
        # Fetch the agent profile of the currently logged-in user
        agent = request.user.agent
        # Fetch campaigns assigned to the agent that are not completed
        campaigns = Campaign.objects.filter(agent=agent).exclude(status='Completed')
        return render(request, 'agent_campaigns.html', {'campaigns': campaigns})
    except Agent.DoesNotExist:
        # If the logged-in user is not linked to an Agent profile
        messages.error(request, "You are not associated with an agent profile.")
        return redirect('agent_home')

# Mark Campaign as Completed
@login_required
def mark_campaign_completed(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id, agent=request.user.agent)
    campaign.status = 'Completed'
    campaign.save()
    messages.success(request, f"Campaign '{campaign.campaign_name}' marked as Completed.")
    return redirect('agent_campaigns')