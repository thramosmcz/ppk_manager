from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Players, Etapas, Torneios, Ranking, UserProfile


class PlayersForm(ModelForm):
    class Meta:
        model = Players
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['redesocial'].required = False
        self.fields['participacoes'].required = False
        self.fields['participacoes'].initial = 0


class EtapasForm(ModelForm):
    class Meta:
        model = Etapas
        fields = '__all__'


class TorneiosForm(ModelForm):
    class Meta:
        model = Torneios
        fields = '__all__'


class TorneiosRanking(ModelForm):
    class Meta:
        model = Ranking
        fields = '__all__'


class AdmEtapaForm(ModelForm):
    class Meta:
        model = Etapas
        fields = '__all__'

    def create_etapas_adm(self, etapa, etapas_ids):
        for etapa_id in etapas_ids:
            Etapas_Torneio.objects.create(etapa=etapa, etapa_id=etapa_id)


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )


class UserCreateForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nome', required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Sobrenome', required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='E-mail', required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'can_view_players', 'can_edit_players',
            'can_view_torneios', 'can_edit_torneios',
            'can_view_etapas', 'can_edit_etapas',
            'can_view_ranking', 'can_manage_users',
        ]
        labels = {
            'can_view_players':  'Visualizar Players',
            'can_edit_players':  'Editar Players',
            'can_view_torneios': 'Visualizar Torneios',
            'can_edit_torneios': 'Editar Torneios',
            'can_view_etapas':   'Visualizar Etapas',
            'can_edit_etapas':   'Editar Etapas',
            'can_view_ranking':  'Visualizar Ranking',
            'can_manage_users':  'Gerenciar Usuários',
        }
