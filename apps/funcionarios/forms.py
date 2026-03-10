from django import forms
from django.forms import inlineformset_factory

from .models import (BeneficioFuncionario, DadosTrabalhistas,
                     DocumentosFuncionario, EnderecoFuncionario, Funcionario)


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'nome', 'data_nascimento', 'sexo', 'natural_de',
            'grau_instrucao', 'estado_civil', 'conjuge', 
            'nome_pai', 'nome_mae', 'numero_filhos','chave_pix'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'  ),
            'chave_pix': forms.TextInput(attrs={'placeholder': 'CPF, E-mail, Celular ou Aleatória'}),
            }

class EnderecoFuncionarioForm(forms.ModelForm):
    class Meta:
        model = EnderecoFuncionario
        fields = ['cep', 'endereco', 'numero', 'bairro', 'cidade', 'uf']

class DocumentosFuncionarioForm(forms.ModelForm):
    class Meta:
        model = DocumentosFuncionario
        fields = [
            'pis_pasep', 'tipo_pis_pasep', 'rg', 'rg_orgao_expedidor', 'cpf', 
            'ctps_numero', 'ctps_serie', 'ctps_uf', 'titulo_eleitor', 'certificado_reservista'
        ]


class DadosTrabalhistasForm(forms.ModelForm):
    class Meta:
        model = DadosTrabalhistas
        fields = [
            'data_admissao_contabilidade','data_admissao_marcenaria', 'funcao', 'cbo', 'salario', 
            'insalubridade', 'horario_trabalho', 
            'contrato_experiencia_dias', 'prorrogação_dias'
        ]
        widgets = {
            'data_admissao_contabilidade': forms.DateInput(
                attrs={'type': 'date'}, 
                format='%Y-%m-%d'),
            'data_admissao_marcenaria': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'),

        }

        labels = {
            'funcao': 'Função',  # ← aqui você muda o rótulo
            'data_admissao': 'Data de Admissão',  # exemplo adicional
        }

class BeneficioFuncionarioForm(forms.ModelForm):
    class Meta:
        model = BeneficioFuncionario
        fields = ['nome', 'valor_desconto']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Odontológico'}),
            'valor_desconto': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Ex: 300.00'})
        }

# Cria o FormSet (Gerenciador de múltiplos formulários)
BeneficioFormSet = inlineformset_factory(
    Funcionario, 
    BeneficioFuncionario, 
    form=BeneficioFuncionarioForm, 
    extra=1, # Começa com 1 espaço em branco
    can_delete=True # Permite excluir benefícios existentes
)