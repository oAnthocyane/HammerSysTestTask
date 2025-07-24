from django.urls import path
from . import views

urlpatterns = [
    path('auth/send-code/', views.send_code, name='send-code'),
    path('auth/verify-code/', views.verify_code, name='verify-code'),
    path('profile/', views.profile, name='profile'),
    path('profile/activate-invite/', views.activate_invite, name='activate-invite'),
]