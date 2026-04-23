from django.urls import include, path
from rest_framework import routers
from pkapp.api import views as apiviews

router = routers.DefaultRouter()
router.register(r'etapas', apiviews.EtapaViewSet,basename='etapa')
router.register(r'players', apiviews.PlayerViewSet,basename='player')
router.register(r'ranking', apiviews.RankingViewSet,basename='ranking')
router.register(r'torneios', apiviews.TorneioViewSet,basename='torneio')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('blinds/<int:id>/niveis/', apiviews.blinds_niveis, name='blinds_niveis'),
    path('config/som/',             apiviews.config_som,    name='config_som'),
]
