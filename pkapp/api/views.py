from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
import json

from pkapp.api.serializers import *
from pkapp.models import *


@api_view(['GET'])
def blinds_niveis(request, id):
    eb = get_object_or_404(EstruturaBlinds, id=id)
    niveis = list(eb.niveis.values(
        'nivel', 'small_blind', 'big_blind', 'ante',
        'duracao_minutos', 'break_apos_minutos'
    ))
    return Response(niveis)


@api_view(['GET', 'POST'])
def config_som(request):
    cfg, _ = ConfiguracaoSom.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        data = request.data
        cfg.som_1min    = data.get('som_1min',    cfg.som_1min)
        cfg.som_10sec   = data.get('som_10sec',   cfg.som_10sec)
        cfg.som_mudanca = data.get('som_mudanca', cfg.som_mudanca)
        cfg.volume      = int(data.get('volume',  cfg.volume))
        cfg.save()
    return Response({
        'som_1min':    cfg.som_1min,
        'som_10sec':   cfg.som_10sec,
        'som_mudanca': cfg.som_mudanca,
        'volume':      cfg.volume,
    })


PONTUACAO_POR_POSICAO = {1: 95, 2: 80, 3: 70, 4: 60, 5: 50, 6: 40, 7: 30, 8: 20, 9: 10}


class EtapaViewSet(viewsets.ViewSet):

    def list(self, request):
        serializer = EtapaSerializer(Etapas.objects.all(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        etapa = get_object_or_404(Etapas, pk=pk)
        return Response(EtapaSerializer(etapa).data)

    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        etapa = get_object_or_404(Etapas, pk=pk)
        serializer = RankingSerializer(Ranking.objects.filter(id_etapa=etapa.id), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def inscrito(self, request, pk=None):
        json_data = request.data
        body_players_ids = [j['id'] for j in json_data]

        etapa = get_object_or_404(Etapas, pk=pk)

        existing_ids = set(
            Ranking.objects.filter(id_etapa=etapa, id_player__in=body_players_ids)
            .values_list('id_player_id', flat=True)
        )
        to_create = [pid for pid in body_players_ids if pid not in existing_ids]

        for pid in to_create:
            Ranking.objects.create(
                id_etapa=etapa,
                id_torneio=etapa.id_torneio,
                id_player=Players.objects.get(pk=pid),
                buy_inn=1, qtd_rebuy=0, posicao=0, pontuacao=0, premio=0
            )
            Players.objects.filter(pk=pid).update(participacoes=models.F('participacoes') + 1)

        qset_ranking = Ranking.objects.filter(id_etapa=etapa, id_player__in=body_players_ids)
        return Response(RankingSerializer(qset_ranking, many=True).data)

    @inscrito.mapping.delete
    def inscrito_del(self, request, pk=None):
        json_data = request.data
        if isinstance(json_data, list):
            body_players_ids = [j['id'] for j in json_data]
        else:
            body_players_ids = [json_data['id']]

        etapa = get_object_or_404(Etapas, pk=pk)
        Ranking.objects.filter(id_etapa=etapa, id_player__in=body_players_ids).delete()

        return Response(RankingSerializer(Ranking.objects.filter(id_etapa=etapa), many=True).data)

    @action(detail=True, methods=['post'])
    def abrir(self, request, pk=None):
        etapa = get_object_or_404(Etapas, pk=pk)
        if etapa.status != 'I':
            return Response({'error': 'Etapa não está inativa.'}, status=status.HTTP_400_BAD_REQUEST)
        etapa.status = 'A'
        etapa.save()
        return Response({'status': etapa.status})

    @action(detail=True, methods=['post'])
    def alterar_status(self, request, pk=None):
        etapa = get_object_or_404(Etapas, pk=pk)
        novo = request.data.get('status')
        if novo not in ('I', 'A', 'F'):
            return Response({'error': 'Status inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        etapa.status = novo
        etapa.save()
        return Response({'status': etapa.status})

    @action(detail=True, methods=['post'])
    def rebuy(self, request, pk=None):
        etapa = get_object_or_404(Etapas, pk=pk)
        player_id = request.data.get('player_id')
        ranking = get_object_or_404(Ranking, id_etapa=etapa, id_player_id=player_id)

        if ranking.qtd_rebuy >= etapa.id_torneio.qtd_rebuy:
            return Response({'error': 'Limite de rebuys atingido.'}, status=status.HTTP_400_BAD_REQUEST)

        ranking.qtd_rebuy += 1
        ranking.save()
        return Response(RankingSerializer(ranking).data)

    @action(detail=True, methods=['post'])
    def eliminar(self, request, pk=None):
        etapa = get_object_or_404(Etapas, pk=pk)
        player_id = request.data.get('player_id')
        posicao   = request.data.get('posicao')

        ranking = get_object_or_404(Ranking, id_etapa=etapa, id_player_id=player_id)
        if ranking.posicao != 0:
            return Response({'error': 'Player já foi eliminado.'}, status=status.HTTP_400_BAD_REQUEST)

        # Posição = número de players ainda ativos no banco (fonte da verdade)
        posicao = Ranking.objects.filter(id_etapa=etapa, posicao=0).count()
        if posicao < 1:
            posicao = 1

        ranking.posicao   = posicao
        ranking.pontuacao = PONTUACAO_POR_POSICAO.get(posicao, 0)

        if posicao in (1, 2, 3):
            torneio = etapa.id_torneio
            inscritos    = Ranking.objects.filter(id_etapa=etapa)
            total_buyins = inscritos.count()
            total_rebuys = inscritos.aggregate(t=Sum('qtd_rebuy'))['t'] or 0
            arrecadado   = total_buyins * float(torneio.vlr_buyinn) + total_rebuys * float(torneio.vlr_rebuy)
            jackpot      = (total_buyins + total_rebuys) * float(torneio.vlr_jackpot)
            txadm        = total_buyins * float(torneio.vlr_txadm)
            prizepool    = arrecadado - jackpot - txadm
            ranking.premio = round(prizepool * {1: 0.50, 2: 0.30, 3: 0.20}[posicao], 2)

        ranking.save()

        todos_eliminados = not Ranking.objects.filter(id_etapa=etapa, posicao=0).exists()
        if todos_eliminados and Ranking.objects.filter(id_etapa=etapa).exists():
            etapa.status = 'F'
            etapa.save()

        resp = RankingSerializer(ranking).data
        resp['etapa_finalizada'] = todos_eliminados
        return Response(resp)

    def create(self, request):
        pass

    def update(self, request, pk=None):
        json_data = request.data
        body_ranking_ids = [j['id'] for j in json_data]
        for j in json_data:
            try:
                r = Ranking.objects.get(pk=j['id'])
                r.buy_inn   = j['buy_inn']
                r.qtd_rebuy = j['qtd_rebuy']
                r.posicao   = j['posicao']
                r.pontuacao = j['pontuacao']
                r.premio    = j['premio']
                r.save()
            except Ranking.DoesNotExist:
                pass
        return Response(RankingSerializer(Ranking.objects.filter(id__in=body_ranking_ids), many=True).data)

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


class PlayerViewSet(viewsets.ViewSet):

    def list(self, request):
        return Response(PlayerSerializer(Players.objects.all().order_by('-participacoes'), many=True).data)

    def retrieve(self, request, pk=None):
        return Response(PlayerSerializer(get_object_or_404(Players, pk=pk)).data)

    def create(self, request): pass
    def update(self, request, pk=None): pass
    def partial_update(self, request, pk=None): pass
    def destroy(self, request, pk=None): pass


class RankingViewSet(viewsets.ViewSet):

    def list(self, request):
        return Response(TorneioSerializer(Torneios.objects.all(), many=True).data)

    def retrieve(self, request, pk=None):
        return Response(TorneioSerializer(get_object_or_404(Torneios, pk=pk)).data)

    def update(self, request, pk=None):
        json_data = request.data
        body_ranking_ids = [j['id'] for j in json_data]
        for j in json_data:
            try:
                r = Ranking.objects.get(pk=j['id'])
                r.buy_inn = j['buy_inn']; r.qtd_rebuy = j['qtd_rebuy']
                r.posicao = j['posicao']; r.pontuacao = j['pontuacao']
                r.premio  = j['premio'];  r.save()
            except Ranking.DoesNotExist:
                pass
        return Response(RankingSerializer(Ranking.objects.filter(id__in=body_ranking_ids), many=True).data)

    @action(methods=['get'], detail=True)
    def etapas(self, request, pk=None):
        torneio = get_object_or_404(Torneios, pk=pk)
        return Response(EtapaSerializer(Etapas.objects.filter(id_torneio=torneio.id), many=True).data)

    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        torneio = get_object_or_404(Torneios, pk=pk)
        return Response(RankingSerializer(
            Ranking.objects.filter(id_torneio=torneio.id).order_by('id_etapa_id'), many=True
        ).data)

    def create(self, request): pass
    def partial_update(self, request, pk=None): pass
    def destroy(self, request, pk=None): pass


class TorneioViewSet(viewsets.ViewSet):

    def list(self, request):
        return Response(TorneioSerializer(Torneios.objects.all(), many=True).data)

    def retrieve(self, request, pk=None):
        return Response(TorneioSerializer(get_object_or_404(Torneios, pk=pk)).data)

    @action(methods=['get'], detail=True)
    def etapas(self, request, pk=None):
        torneio = get_object_or_404(Torneios, pk=pk)
        return Response(EtapaSerializer(Etapas.objects.filter(id_torneio=torneio.id), many=True).data)

    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        torneio = get_object_or_404(Torneios, pk=pk)
        return Response(RankingSerializer(
            Ranking.objects.filter(id_torneio=torneio.id).order_by('id_etapa_id'), many=True
        ).data)

    def create(self, request): pass
    def update(self, request, pk=None): pass
    def partial_update(self, request, pk=None): pass
    def destroy(self, request, pk=None): pass
