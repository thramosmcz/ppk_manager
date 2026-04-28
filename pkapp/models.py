from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    can_view_players   = models.BooleanField(default=True)
    can_edit_players   = models.BooleanField(default=False)
    can_view_torneios  = models.BooleanField(default=True)
    can_edit_torneios  = models.BooleanField(default=False)
    can_view_etapas    = models.BooleanField(default=True)
    can_edit_etapas    = models.BooleanField(default=False)
    can_view_ranking   = models.BooleanField(default=True)
    can_manage_users   = models.BooleanField(default=False)

    def __str__(self):
        return f'Perfil de {self.user.username}'

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'


# Create your models here.
class Players(models.Model):
    player = models.CharField(max_length=40)
    email = models.EmailField(max_length=40, blank=True, default='')
    redesocial = models.CharField(max_length=30, blank=True, default='')
    telefone = models.CharField(max_length=14)
    participacoes = models.IntegerField(default=0)

    def __str__(self):
        return self.player

    class Meta:
        ordering = ['player']


class Torneios(models.Model):
    torneio = models.CharField(max_length=30)
    qtd_etapas = models.IntegerField()
    qtd_rebuy = models.IntegerField()
    qtd_players = models.IntegerField()
    vlr_buyinn = models.DecimalField(max_digits=7, decimal_places=2)
    vlr_rebuy = models.DecimalField(max_digits=7, decimal_places=2)
    vlr_jackpot = models.DecimalField(max_digits=7, decimal_places=2)
    vlr_txadm = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    estrutura_blinds = models.ForeignKey('EstruturaBlinds', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.torneio

    class Meta:
        ordering = ['torneio']


class ConfiguracaoSom(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config_som')
    som_1min         = models.CharField(max_length=20, default='beep_low')
    som_10sec        = models.CharField(max_length=20, default='tick')
    som_mudanca      = models.CharField(max_length=20, default='fanfare')
    volume           = models.IntegerField(default=70)

    def __str__(self):
        return f'Som de {self.user.username}'

    class Meta:
        verbose_name = 'Configuração de Som'


class EstruturaBlinds(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.TextField(blank=True, default='')

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Estrutura de Blinds'
        verbose_name_plural = 'Estruturas de Blinds'


class NivelBlind(models.Model):
    estrutura = models.ForeignKey('EstruturaBlinds', on_delete=models.CASCADE, related_name='niveis')
    nivel = models.IntegerField()
    small_blind = models.IntegerField()
    big_blind = models.IntegerField()
    ante = models.IntegerField(default=0)
    duracao_minutos = models.IntegerField(default=20)
    break_apos_minutos = models.IntegerField(default=0)

    def __str__(self):
        return f'Level {self.nivel}: {self.small_blind}/{self.big_blind}'

    class Meta:
        ordering = ['nivel']
        verbose_name = 'Nível de Blind'
        verbose_name_plural = 'Níveis de Blinds'


class Etapas(models.Model):
    id_torneio = models.ForeignKey('Torneios', on_delete=models.PROTECT)
    etapa = models.CharField(max_length=30)
    local = models.CharField(max_length=30)
    data = models.DateField()
    status = models.CharField(max_length=1, default='I')

    def __str__(self):
        return self.etapa

    class Meta:
        ordering = ['data']


class Ranking(models.Model):
    id_torneio = models.ForeignKey('Torneios', on_delete=models.PROTECT)
    id_etapa = models.ForeignKey('Etapas', on_delete=models.PROTECT)
    id_player = models.ForeignKey('Players', on_delete=models.PROTECT)
    buy_inn = models.IntegerField()
    qtd_rebuy = models.IntegerField()
    posicao = models.IntegerField()
    pontuacao = models.IntegerField()
    premio = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return str(self.id)

class RankingTorneio(models.Model):
    id_torneio = models.ForeignKey('Torneios', on_delete=models.PROTECT)
    id_player  = models.ForeignKey('Players', on_delete=models.PROTECT)
    row_number = models.IntegerField()
    pontuacao = models.IntegerField()

    objects = models.Manager().raw(
             'select id_player_id, pontuacao, row_number() over '
                    '(partition by id_player_id order by pontuacao desc) '
               'from pkapp_ranking')

    def __str__(self):
        return str(self.id_torneio)

    class Meta:
        abstract = True
        managed  = False

