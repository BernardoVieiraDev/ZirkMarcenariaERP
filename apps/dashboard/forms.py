from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class LoginFormComCPF(AuthenticationForm):
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes Bootstrap aos campos padrões do Django
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Usuário'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})

    def clean(self):
        cleaned_data = super().clean()
        cpf_input = cleaned_data.get('cpf')
        user = self.get_user()

        if user and cpf_input:
            # Remove pontuação para comparação segura (caso salve apenas números)
            # Se você salvar com pontuação no banco, remova essa limpeza ou ajuste conforme necessidade
            cpf_limpo_input = ''.join(filter(str.isdigit, cpf_input))
            
            try:
                # Busca o CPF vinculado ao usuário gerente
                perfil = user.perfil
                cpf_cadastrado = ''.join(filter(str.isdigit, perfil.cpf))
                
                if cpf_limpo_input != cpf_cadastrado:
                    raise ValidationError("O CPF informado não confere com o cadastro deste usuário.")
            
            except AttributeError:
                # O usuário logado não tem um PerfilUsuario criado
                raise ValidationError("Este usuário não possui um CPF vinculado para acesso.")
        
        return cleaned_data