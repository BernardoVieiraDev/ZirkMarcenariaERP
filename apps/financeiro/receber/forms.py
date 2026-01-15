from django import forms

from apps.clientes.models import Cliente  # <--- Importe o modelo Cliente

from .models import Banco, CaixaDiario, MovimentoBanco, Receber


class ReceberForm(forms.ModelForm):
    # Campo "falso" para o usuário escolher o destino
    DESTINO_CHOICES = [
        ('BANCO', 'Conta Bancária'),
        ('CAIXA', 'Caixa Interno (Dinheiro)'),
    ]
    destino_recebimento = forms.ChoiceField(
        choices=DESTINO_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input', 
            'onclick': 'toggleBancoField()' # Chama a função JS ao clicar
        }),
        initial='BANCO',
        label="Destino do Recurso"
    )

    parcelas = forms.IntegerField(
        initial=1, 
        min_value=1, 
        max_value=60, 
        label="Parcelas (x)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1 (À vista) ou 12'})
    )

    class Meta:
        model = Receber
        fields = [
            'destino_recebimento',
            'descricao',
            'cliente',
            'categoria',
            'valor',
            'parcelas',
            'data_vencimento',
            'tipo_recebimento',
            'forma_recebimento',
            'status',
            'valor_recebido',
            'data_recebimento',
            'banco_destino',
            'observacoes',
        ]
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_recebimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            # ALTERADO AQUI: De TextInput para Select
            'cliente': forms.Select(attrs={'class': 'form-select'}), 
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_recebido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_recebimento': forms.Select(attrs={'class': 'form-control'}),
            'banco_destino': forms.Select(attrs={'class': 'form-select', 'id': 'id_banco_destino'}),
            'forma_recebimento': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # O banco não pode ser obrigatório, pois podemos escolher Caixa
        self.fields['banco_destino'].required = False
        
        # Filtra apenas clientes ativos (se houver soft delete implementado)
        # Assumindo que o SoftDeleteMixin usa 'is_deleted' ou similar.
        # Se não usar, pode manter apenas Cliente.objects.all()
        try:
            self.fields['cliente'].queryset = Cliente.objects.filter(is_deleted=False)
        except:
            self.fields['cliente'].queryset = Cliente.objects.all()

        # Se for edição, define o radio button corretamente
        if self.instance.pk:
            if self.instance.movimento_caixa:
                self.fields['destino_recebimento'].initial = 'CAIXA'
            elif self.instance.banco_destino:
                self.fields['destino_recebimento'].initial = 'BANCO'

    def clean(self):
        cleaned_data = super().clean()
        destino = cleaned_data.get('destino_recebimento')
        banco = cleaned_data.get('banco_destino')
        status = cleaned_data.get('status')

        # Se escolheu CAIXA, forçamos o banco a ser None
        if destino == 'CAIXA':
            cleaned_data['banco_destino'] = None
        
        # Se escolheu BANCO e está Recebido, o banco é obrigatório
        elif destino == 'BANCO' and status == 'Recebido' and not banco:
            self.add_error('banco_destino', 'Selecione a conta bancária para confirmar o recebimento.')

        return cleaned_data

class CaixaDiarioForm(forms.ModelForm):
    class Meta:
        model = CaixaDiario
        fields = ['data', 'historico', 'tipo', 'valor']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'historico': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['nome', 'agencia', 'conta', 'saldo_inicial']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class MovimentoBancoForm(forms.ModelForm):
    class Meta:
        model = MovimentoBanco
        fields = ['banco', 'data', 'historico', 'tipo', 'valor']
        widgets = {
            'banco': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'historico': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }