"""
Legal GraphRAG URL Configuration
"""

from django.urls import path

from .views import chat_view, search_view, sources_view, health_view

app_name = 'legal_graphrag'

urlpatterns = [
    path('chat/', chat_view, name='chat'),
    path('search/', search_view, name='search'),
    path('sources/', sources_view, name='sources'),
    path('health/', health_view, name='health'),
]
