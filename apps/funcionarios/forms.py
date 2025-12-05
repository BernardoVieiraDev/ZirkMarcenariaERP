from django import forms
from .models import Funcionario, EnderecoFuncionario, DocumentosFuncionario, DadosTrabalhistas

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'nome', 'data_nascimento', 'sexo', 'natural_de',
            'grau_instrucao', 'estado_civil', 'conjuge', 
            'nome_pai', 'nome_mae', 'numero_filhos'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

class EnderecoFuncionarioForm(forms.ModelForm):
    class Meta:
        model = EnderecoFuncionario
        fields = ['cep', 'endereco', 'numero', 'bairro', 'cidade', 'uf']

class DocumentosFuncionarioForm(forms.ModelForm):
    class Meta:
        model = DocumentosFuncionario
        fields = [
            'pis_pasep', 'rg', 'rg_orgao_expedidor', 'cpf', 
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
            'data_admissao_contabilidade': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao_marcenaria': forms.DateInput(attrs={'type': 'date'}),

        }

        labels = {
            'funcao': 'Função',  # ← aqui você muda o rótulo
            'data_admissao': 'Data de Admissão',  # exemplo adicional
        }

