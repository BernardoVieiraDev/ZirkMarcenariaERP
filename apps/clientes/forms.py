from django import forms

from .models import Cliente, EnderecoCliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['tipo_pessoa', 'nome_completo', 'cpf', 'rg', 'cnpj', 'inscricao_estadual', 'telefone', 'email', 'chave_pix']
        widgets = {
            'tipo_pessoa': forms.RadioSelect(attrs={'class': 'tipo-pessoa-radio'}),
            'nome_completo': forms.TextInput(attrs={'placeholder': 'Ex: João da Silva ou Empresa XYZ'}),
            'cpf': forms.TextInput(attrs={'class': 'mask-cpf', 'placeholder': '000.000.000-00'}),
            'cnpj': forms.TextInput(attrs={'class': 'mask-cnpj', 'placeholder': '00.000.000/0000-00'}),
            'telefone': forms.TextInput(attrs={'class': 'mask-phone', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'placeholder': 'cliente@email.com'}),
            'chave_pix': forms.TextInput(attrs={'placeholder': 'CPF, CNPJ, E-mail, Celular...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['cpf'].required = False
        self.fields['cnpj'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_pessoa = cleaned_data.get('tipo_pessoa')
        cpf = cleaned_data.get('cpf')
        cnpj = cleaned_data.get('cnpj')

        # Limpa pontuação para validação no banco
        if cpf:
            cleaned_data['cpf'] = cpf.replace('.', '').replace('-', '')
        if cnpj:
            cleaned_data['cnpj'] = cnpj.replace('.', '').replace('/', '').replace('-', '')

        if tipo_pessoa == 'F':
            if not cleaned_data.get('cpf'):
                self.add_error('cpf', 'O CPF é obrigatório para Pessoa Física.')
            cleaned_data['cnpj'] = None
            cleaned_data['inscricao_estadual'] = None
            
        elif tipo_pessoa == 'J':
            if not cleaned_data.get('cnpj'):
                self.add_error('cnpj', 'O CNPJ é obrigatório para Pessoa Jurídica.')
            cleaned_data['cpf'] = None
            cleaned_data['rg'] = None

        return cleaned_data


class EnderecoClienteForm(forms.ModelForm):
    class Meta:
        model = EnderecoCliente
        fields = ['cep', 'endereco', 'numero', 'bairro', 'cidade', 'uf', 'complemento']
        widgets = {
            'cep': forms.TextInput(attrs={'class': 'mask-cep', 'placeholder': '00000-000'}),
            'uf': forms.TextInput(attrs={'placeholder': 'UF', 'maxlength': '2'}),
        }