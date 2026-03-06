from django import forms

from .models import Cliente, EnderecoCliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome_completo', 'cpf', 'rg', 'telefone', 'email', 'chave_pix']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'placeholder': 'Ex: João da Silva'}),
            'cpf': forms.TextInput(attrs={'class': 'mask-cpf', 'placeholder': '000.000.000-00'}),
            'telefone': forms.TextInput(attrs={'class': 'mask-phone', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'placeholder': 'cliente@email.com'}),
            'chave_pix': forms.TextInput(attrs={'placeholder': 'CPF, E-mail, Celular ou Aleatória'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garante que o e-mail não seja obrigatório
        self.fields['email'].required = False


class EnderecoClienteForm(forms.ModelForm):
    class Meta:
        model = EnderecoCliente
        fields = ['cep', 'endereco', 'numero', 'bairro', 'cidade', 'uf', 'complemento']
        widgets = {
            'cep': forms.TextInput(attrs={'class': 'mask-cep', 'placeholder': '00000-000'}),
            'uf': forms.TextInput(attrs={'placeholder': 'UF', 'maxlength': '2'}),
        }