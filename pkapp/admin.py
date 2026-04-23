from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from .models import Players, Torneios, Etapas, Ranking, RankingTorneio, UserProfile
import math, datetime

class EtapasDescarteFilter(SimpleListFilter):
	parameter_name = 'torneio'
	title = "Ranking com descarte "
	def lookups(self, request, model_admin):
		return (
			("analitico", "Analitico"),
			("sintetico", "Sintetico")
			)

	def queryset(self, request, queryset):
		if self.value() == "analitico":
			queryset = queryset

		return queryset

class PlayersAdmin(admin.ModelAdmin):
	list_display = ('player', 'email', 'telefone', 'participacoes')
	list_filter = ('player',)
	fields = ['player', 'email', 'telefone', 'participacoes']
	search_fields = ('player',)

class EtapasList(admin.ModelAdmin):
	list_display = ('etapa', 'local', 'data')
	list_filter = ['id_torneio']


class RankingAdmin(admin.ModelAdmin):
	list_display = ('id_torneio', 'id_etapa', 'id_player', 'buy_inn', 
		'qtd_rebuy', 'pontuacao', 'posicao', 'premio')
	list_filter = ['id_torneio','id_etapa','id_player']

# class RankingTorneioAdmin(admin.ModelAdmin):
# 	list_display = ('id_player', 'pontuacao')
# 	list_filter = ['id_torneio', EtapasDescarteFilter]
		


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_view_players', 'can_edit_players', 'can_view_torneios',
                    'can_edit_torneios', 'can_view_etapas', 'can_edit_etapas',
                    'can_view_ranking', 'can_manage_users')
    list_filter = ('can_manage_users',)


# Register your models here.
admin.site.register(Players, PlayersAdmin)
admin.site.register(Torneios)
admin.site.register(Etapas, EtapasList)
admin.site.register(Ranking, RankingAdmin)
admin.site.register(UserProfile, UserProfileAdmin)


