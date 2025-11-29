from django.contrib import admin
from .models import (
    Funcionario, EnderecoFuncionario, DocumentosFuncionario,
    DadosTrabalhistas
)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'data_nascimento',
        'sexo',
        'estado_civil',
        'grau_instrucao',
        'numero_filhos',
        'data_admissao',
        'salario',
    )
    list_filter = ('sexo', 'estado_civil', 'grau_instrucao')
    search_fields = ('nome', 'cpf', 'documentos__cpf')

    def salario(self, obj):
        return obj.dados_trabalhistas.salario if hasattr(obj, 'dados_trabalhistas') else '-'
    salario.short_description = "Salário"

    def data_admissao(self, obj):
        return obj.dados_trabalhistas.data_admissao_contabilidade if hasattr(obj, 'dados_trabalhistas') else '-'
    data_admissao.short_description = "Admissão"


@admin.register(EnderecoFuncionario)
class EnderecoFuncionarioAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'cidade', 'uf', 'cep')
    search_fields = ('funcionario__nome', 'cidade', 'bairro')


@admin.register(DocumentosFuncionario)
class DocumentosFuncionarioAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'cpf', 'rg', 'titulo_eleitor')
    search_fields = ('funcionario__nome', 'cpf', 'rg')


@admin.register(DadosTrabalhistas)
class DadosTrabalhistasAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data_admissao_contabilidade','data_admissao_marcenaria', 'funcao', 'salario', 'cbo')
    list_filter = ('funcao',)
    search_fields = ('funcionario__nome', 'funcao')


