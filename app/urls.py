from django.urls import path
from . import views

urlpatterns = [
    # Homepage
    path('', views.homepage, name='homepage'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin Home
    path('admin_home/', views.admin_home, name='admin_home'),

    # Agent Views
    path('agent/home/', views.agent_home, name='agent_home'),
    path('add-agent/', views.add_agent, name='add_agent'),
    path('add-agent-admin/', views.add_agent_admin, name='add_agent_admin'),
    path('view-agents/', views.view_agents, name='view_agents'),
    path('agent/campaigns/', views.agent_campaigns, name='agent_campaigns'),
    path('agent/location/', views.agent_location, name='agent_location'),
    path('agent/profile/', views.agent_profile, name='agent_profile'),
    path('agent/profile/<int:agent_id>/', views.agent_profile, name='agent_profile_with_id'),
    path('agent/<int:agent_id>/edit/', views.edit_agent_profile, name='edit_agent_profile'),
    path('agents/delete/<int:agent_id>/', views.delete_agent, name='delete_agent'),
    path('agents/<int:agent_id>/edit/', views.edit_agent_admin, name='edit_agent_admin'),
    path('clients/collected/', views.collected_clients, name='collected_clients'),



    # Client Views
    path('clients/', views.clients, name='clients'),
    path('clients/<int:agent_id>/', views.clients, name='clients'),
    path('add-client/', views.add_client, name='add_client'),
    path('delete_client/<int:client_id>/', views.delete_client, name='delete_client'),
    path('delete_client_admin/<int:client_id>/', views.delete_client_admin, name='delete_client_admin'),
    path('client/edit/<int:client_id>/', views.edit_client, name='edit_client'),

    # Campaign Views
    path('create-campaign/', views.create_campaign_view, name='create_campaign'),
    path('campaigns/', views.campaigns_list, name='campaigns_list'),
    path('campaign/edit/<int:id>/', views.edit_campaign, name='edit_campaign'),
    path('delete-campaign/<int:id>/', views.delete_campaign, name='delete_campaign'),
    path('campaign/<int:campaign_id>/complete/', views.mark_campaign_completed, name='mark_campaign_completed'),

    # Attendance and Agent Code
    path('add-attendance/', views.add_attendance, name='add_attendance'),
    path('generate-agent-code/', views.generate_agent_code, name='generate_agent_code'),

    # Agent Navigation
    path('agent-nav/', views.agent_nav, name='agent_nav'),

    # Password Management
    path('change-password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),

    # Agent Approval
    path('approve-agent/', views.approve_agent_view, name='approve_agent'),
]
