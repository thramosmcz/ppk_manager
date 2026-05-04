# PKTOUR — Contexto do Projeto

## O que é
Sistema web de gerenciamento de torneios de poker. Controla players, torneios, etapas, ranking e usuários. Roda em produção na AWS EC2.

## Stack
- **Backend:** Python 3.8 + Django 3.0 + Django REST Framework
- **Banco:** SQLite (arquivo em `/home/ubuntu/pktour/db.sqlite3` no servidor)
- **Servidor:** Gunicorn + Nginx na EC2 Ubuntu 22.04 (t2.micro)
- **Frontend:** Templates Django com Bootstrap 4 + tema dark customizado. Há também um bundle React legado em `pkapp/static/pkapp/` (não é a interface principal).
- **Autenticação:** Sistema próprio sobre `django.contrib.auth`, sem usar o admin do Django na interface.

## Estrutura de Diretórios
```
pkproject/          # configurações Django (settings.py, urls.py)
pkapp/              # app principal
  models.py         # todos os models
  views.py          # todas as views (auth, CRUD, dashboard, perfil)
  urls.py           # rotas do app
  forms.py          # formulários Django
  permissions.py    # decorators login_required_custom e permission_required
  signals.py        # cria UserProfile automaticamente ao criar User
  api/              # REST API (DRF ViewSets)
    views.py
    serializers.py
    urls.py
  templates/pkapp/  # todos os templates HTML
  middleware/cors.py
  migrations/
data/
  db.sqlite3        # banco local de desenvolvimento
```

## Models principais
| Model | Descrição |
|---|---|
| `Players` | Jogadores cadastrados. Ordenados por `player` (nome). |
| `Torneios` | Torneios. Ordenados por `torneio` (nome alfabético). Tem FK para `EstruturaBlinds`. |
| `Etapas` | Etapas de um torneio. Status: `I`=Inativo, `A`=Aberto, `F`=Finalizado. Ordenadas por `data`. |
| `Ranking` | Resultado de cada player em cada etapa (buy_in, rebuy, posição, pontuação, prêmio). |
| `UserProfile` | Extensão do User do Django com permissões granulares (can_view_players, can_edit_players, etc). Criado automaticamente via signal. |
| `EstruturaBlinds` | Estrutura de níveis de blind vinculada a um torneio. |
| `NivelBlind` | Cada nível de uma estrutura (SB, BB, ante, duração, break). |
| `ConfiguracaoSom` | Preferências de som do poker clock por usuário. |

## Sistema de Permissões
Definido em `pkapp/permissions.py`. Dois decorators:
- `@login_required_custom` — exige login
- `@permission_required('campo_do_profile')` — verifica campo booleano no `UserProfile`

Superusers têm acesso total. Campos do `UserProfile`:
`can_view_players`, `can_edit_players`, `can_view_torneios`, `can_edit_torneios`, `can_view_etapas`, `can_edit_etapas`, `can_view_ranking`, `can_manage_users`

## URLs principais
```
/                           → dashboard
/login/ /logout/
/pkapp/players              → lista de players
/pkapp/torneios             → lista de torneios
/pkapp/etapas               → lista de etapas
/pkapp/blinds/              → estruturas de blinds
/pkapp/ranking              → ranking por torneio
/pkapp/usuarios/            → gestão de usuários (requer can_manage_users)
/pkapp/perfil/              → perfil do usuário logado (dados + senha)
/pkapp/admetapa/<id>/       → administração de etapa (inscrição de players)
/pkapp/clock/<id>/          → poker clock da etapa
/pkapp/api/                 → REST API (DRF)
```

## REST API
Base: `/pkapp/api/`
| Endpoint | Descrição |
|---|---|
| `GET /etapas/` | Lista etapas |
| `POST /etapas/<id>/inscrito/` | Inscreve players na etapa |
| `DELETE /etapas/<id>/inscrito/` | Remove inscrição |
| `POST /etapas/<id>/rebuy/` | Adiciona rebuy |
| `POST /etapas/<id>/eliminar/` | Elimina player (registra posição e pontuação) |
| `POST /etapas/<id>/alterar_status/` | Muda status da etapa (I/A/F) |
| `GET /torneios/<id>/ranking/` | Ranking de um torneio |
| `GET /blinds/<id>/niveis/` | Níveis de uma estrutura de blinds |
| `GET/POST /config/som/` | Configuração de som do usuário logado |

## Regras de Negócio
- **Pontuação por posição:** 1º=95, 2º=80, 3º=70, 4º=60, 5º=50, 6º=40, 7º=30, 8º=20, 9º=10, demais=0
- **Ranking com descarte:** calcula pontuação mensal por player, descarta as 3 menores, soma o restante
- **Financeiro:** acumulado = (buyins + rebuys) × vlr_buyinn + buyins × vlr_txadm; jackpot = (buyins + rebuys) × vlr_jackpot
- **Etapa finaliza automaticamente** quando todos os inscritos são eliminados via API

## Templates e Layout
- Base: `pkapp/templates/pkapp/_base_dark.html` — tema dark com Bootstrap 4, navbar dinâmica por permissão, mensagens Django
- Navbar mostra links conforme permissões do `UserProfile`
- Badge do usuário no navbar é link para `/pkapp/perfil/`
- Classes CSS customizadas: `.card-dark`, `.btn-gold`, `.section-title`, `.chip`, `.badge-status-A/I/F`

## Configuração (variáveis de ambiente)
O `settings.py` lê via `os.environ`:
```
SECRET_KEY      → chave secreta Django
DEBUG           → True/False (default False)
ALLOWED_HOSTS   → hosts separados por vírgula
DB_ENGINE       → sqlite (default) ou postgres
SQLITE_PATH     → caminho do arquivo SQLite
```
Em produção, definidas no arquivo `.env` na raiz do projeto (não commitado).

## Deploy — Produção
- **Servidor:** AWS EC2 t2.micro, Ubuntu 22.04, IP elástico 52.23.91.204
- **Domínio:** pkbovino.com.br
- **Repositório:** https://github.com/thramosmcz/ppk_manager.git
- **Caminho no servidor:** `/home/ubuntu/pktour/`
- **Serviço Gunicorn:** `sudo systemctl restart pktour`
- **Chave SSH:** `data/ubuntu_aws_key.pem`

Fluxo de deploy:
```bash
# local
git add . && git commit -m "mensagem" && git push origin main

# no servidor (via SSH)
ssh -i data/ubuntu_aws_key.pem ubuntu@52.23.91.204
cd /home/ubuntu/pktour
git pull origin main
source venv/bin/activate
python manage.py migrate
sudo systemctl restart pktour
```

## Observações importantes
- O arquivo `deploy_aws_ec2.txt` contém anotações de deploy e está no `.gitignore` — não deve ser commitado pois continha secrets
- O banco SQLite de produção fica no servidor; para backup: `scp -i data/ubuntu_aws_key.pem ubuntu@52.23.91.204:/home/ubuntu/pktour/db.sqlite3 ./backup_db.sqlite3`
- Não usar o admin do Django (`/admin/`) para gestão — o sistema tem interface própria
- Migrations existentes cobrem até `0008_configuracaosom.py`; novas alterações de model exigem `makemigrations` + `migrate`
