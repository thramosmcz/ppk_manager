from django.urls import include, path, re_path
from . import views
from .views import player_update
from rest_framework import routers

urlpatterns = [
    path('players', views.pkapp_players, name='pkapp_players'),
    re_path(r'player_update/(?P<id>\d+)/$', player_update, name = 'pkapp_player_update'),
    path('etapas', views.pkapp_etapas, name='pkapp_etapas'),
    path('admetapa', views.pkapp_admetapa, name='pkapp_admetapa'),
    path('torneios', views.pkapp_torneios, name='pkapp_torneios'),
    path('ranking', views.pkapp_ranking, name='pkapp_ranking'),
    path('pontuacao_global', views.pontuacao_global, name='pkapp_ranking'),   
    path('api/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('pkapp.api.urls')),
    # path('', views.pkapp_index, name='pkapp_index'),
    path('', views.pkapp_react, name='pkapp_react'),
]