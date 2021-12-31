from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Players, Torneios, Etapas, Ranking
from .forms import PlayersForm, TorneiosForm, EtapasForm, TorneiosRanking, AdmEtapaForm

import pkapp.api.serializers


def pkapp_index(request):
    vlrtemplate = 'Envio de valor teste para template pela View 12345'
    return render(request, 'pkapp/index.html', {'vlrtemplate': vlrtemplate})


def pkapp_react(request):
    return render(request, 'pkapp/react.html')


def pkapp_players(request):
    players = Players.objects.all()
    form = PlayersForm()
    data = {'players': players, 'form': form}
    return render(request, 'pkapp/players.html', data)


def player_update(request, id):
    data = {}
    player = Players.objects.get(id=id)
    form = PlayersForm(request.POST or None, instance=player)
    data['player'] = player
    data['form'] = form
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('pkapp_players')
    else:
        return render(request, 'pkapp/player_update.html', data)


def pkapp_etapas(request):
    etapas = Etapas.objects.all()
    return render(request, 'pkapp/etapas.html', {'etapas': etapas})


def pkapp_admetapa(request, id):
    data = {}
    etapa = Etapas.objects.get(id=id)
    form = AdmEtapaForm(request.POST or None, instance=etapa)
    data['etapa'] = etapa
    data['form'] = form


def pkapp_torneios(request):
    torneios = Torneios.objects.all()
    return render(request, 'pkapp/torneios.html', {'torneios': torneios})


def pkapp_ranking(request):
    teste = 'Conteudo de ranking'
    return render(request, 'pkapp/ranking.html', {'teste': teste})

def pontuacao_global(request):
    teste = 'Conteudo de ranking'
    return render(request, 'pkapp/ranking.html', {'teste': teste})