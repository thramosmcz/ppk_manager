from django.urls import include, path, re_path
from . import views

urlpatterns = [
    # Auth
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),

    # Players
    path('players',                            views.pkapp_players,   name='pkapp_players'),
    path('players/novo/',                      views.player_create,   name='player_create'),
    re_path(r'players/(?P<id>\d+)/editar/$',   views.player_update,   name='player_update'),
    re_path(r'players/(?P<id>\d+)/excluir/$',  views.player_delete,   name='player_delete'),
    # compat com URL antiga
    re_path(r'player_update/(?P<id>\d+)/$',    views.player_update,   name='pkapp_player_update'),

    # Torneios
    path('torneios',                           views.pkapp_torneios,  name='pkapp_torneios'),
    path('torneios/novo/',                     views.torneio_create,  name='torneio_create'),
    re_path(r'torneios/(?P<id>\d+)/editar/$',  views.torneio_update,  name='torneio_update'),
    re_path(r'torneios/(?P<id>\d+)/excluir/$', views.torneio_delete,  name='torneio_delete'),

    # Estrutura de Blinds
    path('blinds/',                                views.estrutura_blinds_list,   name='estrutura_blinds_list'),
    path('blinds/nova/',                           views.estrutura_blinds_create, name='estrutura_blinds_create'),
    re_path(r'blinds/(?P<id>\d+)/editar/$',        views.estrutura_blinds_update, name='estrutura_blinds_update'),
    re_path(r'blinds/(?P<id>\d+)/excluir/$',       views.estrutura_blinds_delete, name='estrutura_blinds_delete'),

    # Etapas
    path('etapas',                             views.pkapp_etapas,    name='pkapp_etapas'),
    path('etapas/nova/',                       views.etapa_create,    name='etapa_create'),
    re_path(r'etapas/(?P<id>\d+)/editar/$',    views.etapa_update,    name='etapa_update'),
    re_path(r'etapas/(?P<id>\d+)/excluir/$',   views.etapa_delete,    name='etapa_delete'),
    re_path(r'admetapa/(?P<id>\d+)/$',         views.adm_etapa,       name='pkapp_admetapa'),
    re_path(r'clock/(?P<id>\d+)/$',           views.poker_clock,     name='poker_clock'),

    # Ranking
    path('ranking',                            views.pkapp_ranking,       name='pkapp_ranking'),
    path('pontuacao_global',                   views.pontuacao_global,    name='pkapp_pontuacao_global'),

    # Perfil do usuário logado
    path('perfil/',                            views.meu_perfil,          name='meu_perfil'),

    # Usuários
    path('usuarios/',                          views.user_list,           name='user_list'),
    path('usuarios/novo/',                     views.user_create,         name='user_create'),
    re_path(r'usuarios/(?P<id>\d+)/editar/',   views.user_edit,           name='user_edit'),
    re_path(r'usuarios/(?P<id>\d+)/toggle/',   views.user_toggle_active,  name='user_toggle_active'),

    # API
    path('api/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('pkapp.api.urls')),

    path('', views.pkapp_react, name='pkapp_react'),
]
