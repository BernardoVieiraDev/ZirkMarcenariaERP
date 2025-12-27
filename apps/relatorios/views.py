import io
from datetime import datetime

from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render

from apps.comissionamento.models import PagamentoRT
# Imports dos Models
from apps.financeiro.pagar.models import (Boleto, Cheque, FaturaCartao,
                                          FolhaPagamento, GastoContabilidade,
                                          GastoGasolina, GastoGeral,
                                          GastoImovel, GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)
from apps.financeiro.receber.models import Receber

# Imports dos Services
from .extensions import (BNDESExcelService, BoletoExcelService,
                         ChequeExcelService, ComissaoExcelService,
                         FaturaCartaoExcelService,
                         FuncionarioFolhaExcelService,
                         GastoContabilidadeExcelService,
                         GastoGasolinaExcelService, GastoGeralExcelService,
                         GastoImovelExcelService, GastoIPTUExcelService,
                         GastoUtilidadeExcelService,
                         GastoVeiculoConsorcioExcelService,
                         PrestacaoEmprestimoExcelService)
from .services.receber import ReceberExcelService


def list_planilhas(request):
    return render(request, 'core/planilhas/list.html')


def exportar_todos_boletos(request):
    # 1. Busca os dados
    boletos = Boleto.objects.all().order_by('-data_vencimento')

    # 2. Define o nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Boletos_{data_hoje}.xlsx"

    try:
        # 3. Gera o arquivo em MEMÓRIA (buffer)
        # Note que não passamos mais o caminho_arquivo
        buffer = BoletoExcelService.gerar_relatorio_geral(boletos)

        # 4. Retorna o download direto
        return FileResponse(
            buffer, 
            as_attachment=True, 
            filename=nome_arquivo
        )

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_utilidades(request):
    gastos = GastoUtilidade.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Utilidades_{data_hoje}.xlsx"

    try:
        buffer = GastoUtilidadeExcelService.gerar_relatorio_utilidades(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_cheques(request):
    cheques = Cheque.objects.all().order_by('-data_emissao')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Cheques_{data_hoje}.xlsx"

    try:
        buffer = ChequeExcelService.gerar_relatorio_cheques(cheques)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_contabilidade(request):
    gastos = GastoContabilidade.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Contabilidade_{data_hoje}.xlsx"

    try:
        buffer = GastoContabilidadeExcelService.gerar_relatorio_contabilidade(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_cartoes(request):
    # Filtro Sicoob e Bradesco
    gastos = FaturaCartao.objects.filter(
        cartao__in=['PF_SICOOB', 'PF_BRADESCO']
    ).order_by('-data_vencimento')

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Cartoes_SicoobBradesco_{data_hoje}.xlsx"

    try:
        buffer = FaturaCartaoExcelService.gerar_relatorio_cartoes(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_bndes(request):
    # Filtro BNDES
    gastos = FaturaCartao.objects.filter(cartao='BNDES').order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_BNDES_{data_hoje}.xlsx"

    try:
        buffer = BNDESExcelService.gerar_relatorio_bndes(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_gastos_gerais(request):
    gastos = GastoGeral.objects.all().order_by('-data_gasto')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_GastosGerais_{data_hoje}.xlsx"

    try:
        buffer = GastoGeralExcelService.gerar_relatorio_geral(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_veiculos(request):
    gastos = GastoVeiculoConsorcio.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Veiculos_{data_hoje}.xlsx"

    try:
        buffer = GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_condominio(request):
    tipos_desejados = ['CONDO', 'TAXA', 'ACORDO']
    gastos = GastoImovel.objects.filter(
        tipo_gasto__in=tipos_desejados
    ).order_by('-data_vencimento')

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Condominio_{data_hoje}.xlsx"

    try:
        buffer = GastoImovelExcelService.gerar_relatorio_condominio(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_iptu(request):
    gastos = GastoImovel.objects.filter(tipo_gasto='IPTU').order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_IPTU_{data_hoje}.xlsx"

    try:
        buffer = GastoIPTUExcelService.gerar_relatorio_iptu(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_gasolina(request):
    gastos = GastoGasolina.objects.all().order_by('-data_gasto')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Gasolina_{data_hoje}.xlsx"

    try:
        buffer = GastoGasolinaExcelService.gerar_relatorio_gasolina(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_comissoes(request):
    pagamentos = PagamentoRT.objects.select_related('contrato', 'contrato__arquiteta').all().order_by('-data_pagamento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Comissoes_Arquitetos_{data_hoje}.xlsx"

    try:
        buffer = ComissaoExcelService.gerar_relatorio_comissoes(pagamentos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_prestacoes(request):
    gastos = PrestacaoEmprestimo.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Prestacoes_{data_hoje}.xlsx"

    try:
        buffer = PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)


def exportar_folha(request):
    pagamentos = FolhaPagamento.objects.select_related(
        'funcionario', 
        'funcionario__dados_trabalhistas'
    ).order_by('-data_referencia', 'funcionario__nome')

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_FolhaPagamento_{data_hoje}.xlsx"

    try:
        buffer = FuncionarioFolhaExcelService.gerar_relatorio_folha(pagamentos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
import io
from datetime import datetime

import xlsxwriter
from django.http import FileResponse, HttpResponse

# ... imports dos models e services ...

def exportar_multiplas_planilhas(request):
    if request.method != 'POST':
        return redirect('pagar:list_planilhas')

    relatorios = request.POST.getlist('relatorios')
    if not relatorios:
        return HttpResponse("Nenhum relatório selecionado.", status=400)

    # 1. Cria o buffer e o Workbook Mestre
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Data para o nome do arquivo
    hoje_str = datetime.now().strftime("%Y-%m-%d")

    try:
        # 2. Chama cada service passando o 'wb'
        
        if 'boletos' in relatorios:
            dados = Boleto.objects.all().order_by('-data_vencimento')
            # Passamos o wb criado acima
            BoletoExcelService.gerar_relatorio_geral(dados, workbook=wb)

        if 'utilidades' in relatorios:
            dados = GastoUtilidade.objects.all().order_by('-data_vencimento')
            GastoUtilidadeExcelService.gerar_relatorio_utilidades(dados, workbook=wb)

        if 'cheques' in relatorios:
            dados = Cheque.objects.all().order_by('-data_emissao')
            ChequeExcelService.gerar_relatorio_cheques(dados, workbook=wb)

        if 'contabilidade' in relatorios:
            dados = GastoContabilidade.objects.all().order_by('-data_vencimento')
            GastoContabilidadeExcelService.gerar_relatorio_contabilidade(dados, workbook=wb)

        if 'cartoes' in relatorios:
            dados = FaturaCartao.objects.filter(cartao__in=['PF_SICOOB', 'PF_BRADESCO']).order_by('-data_vencimento')
            FaturaCartaoExcelService.gerar_relatorio_cartoes(dados, workbook=wb)

        if 'bndes' in relatorios:
            dados = FaturaCartao.objects.filter(cartao='BNDES').order_by('-data_vencimento')
            BNDESExcelService.gerar_relatorio_bndes(dados, workbook=wb)

        if 'gastos_gerais' in relatorios:
            dados = GastoGeral.objects.all().order_by('-data_gasto')
            GastoGeralExcelService.gerar_relatorio_geral(dados, workbook=wb)

        if 'veiculos' in relatorios:
            dados = GastoVeiculoConsorcio.objects.all().order_by('-data_vencimento')
            GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(dados, workbook=wb)

        if 'condominio' in relatorios:
            dados = GastoImovel.objects.filter(tipo_gasto__in=['CONDO', 'TAXA', 'ACORDO']).order_by('-data_vencimento')
            GastoImovelExcelService.gerar_relatorio_condominio(dados, workbook=wb)

        if 'iptu' in relatorios:
            dados = GastoImovel.objects.filter(tipo_gasto='IPTU').order_by('-data_vencimento')
            GastoIPTUExcelService.gerar_relatorio_iptu(dados, workbook=wb)

        if 'gasolina' in relatorios:
            dados = GastoGasolina.objects.all().order_by('-data_gasto')
            GastoGasolinaExcelService.gerar_relatorio_gasolina(dados, workbook=wb)

        if 'comissoes' in relatorios:
            dados = PagamentoRT.objects.select_related('contrato', 'contrato__arquiteta').all().order_by('-data_pagamento')
            ComissaoExcelService.gerar_relatorio_comissoes(dados, workbook=wb)

        if 'prestacoes' in relatorios:
            dados = PrestacaoEmprestimo.objects.all().order_by('-data_vencimento')
            PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(dados, workbook=wb)

        if 'folha' in relatorios:
            dados = FolhaPagamento.objects.select_related('funcionario').all().order_by('-data_referencia')
            FuncionarioFolhaExcelService.gerar_relatorio_folha(dados, workbook=wb)

    except Exception as e:
        # Se der erro, fecha o wb para não vazar memória, mas avisa o usuário
        wb.close()
        return HttpResponse(f"Erro ao gerar planilhas unificadas: {e}", status=500)

    # 3. Fecha o Workbook Mestre (isso finaliza o arquivo .xlsx com todas as abas)
    wb.close()

    # 4. Prepara o download
    output.seek(0)
    filename = f"Relatorio_Consolidado_{hoje_str}.xlsx"
    
    return FileResponse(
        output, 
        as_attachment=True, 
        filename=filename
    )

def exportar_receber(request):
    # Busca todos os registros ordenados por data de vencimento
    # Você pode adicionar filtros aqui se quiser (ex: apenas ano atual)
    dados = Receber.objects.all().order_by('data_vencimento')
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_ContasReceber_{data_hoje}.xlsx"

    try:
        buffer = ReceberExcelService.gerar_relatorio_receber(dados)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)