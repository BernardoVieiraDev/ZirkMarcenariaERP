import os
from datetime import date, datetime

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.comissionamento.models import PagamentoRT
from apps.financeiro.pagar.models import (Boleto, Cheque, FaturaCartao,
                                          FolhaPagamento, GastoContabilidade,
                                          GastoGasolina, GastoGeral,
                                          GastoImovel, GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)

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


def list_planilhas(request):
    return render(request, 'core/planilhas/list.html')


def exportar_todos_boletos(request):
    # 1. Busca todos os boletos (pode adicionar order_by se quiser)
    boletos = Boleto.objects.all().order_by('-data_vencimento')

    # 2. Define nome com timestamp para não sobrescrever
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Boletos_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # 3. Chama o novo método do service
        BoletoExcelService.gerar_relatorio_geral(boletos, caminho_arquivo=caminho_temp)

        # 4. Download
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_utilidades(request):
    # Busca todas as utilidades ordenadas por vencimento
    gastos = GastoUtilidade.objects.all().order_by('-data_vencimento')

    # Nome do arquivo com data
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Utilidades_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Chama o serviço
        GastoUtilidadeExcelService.gerar_relatorio_utilidades(gastos, caminho_arquivo=caminho_temp)

        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_cheques(request):
    # 1. Busca todos os cheques (ordenados por data de emissão)
    cheques = Cheque.objects.all().order_by('-data_emissao')

    # 2. Define nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Cheques_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # 3. Gera o arquivo usando o serviço
        ChequeExcelService.gerar_relatorio_cheques(cheques, caminho_arquivo=caminho_temp)

        # 4. Retorna para download
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não encontrado após geração.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno ao gerar Excel: {str(e)}", status=500)
    


def exportar_contabilidade(request):
    # Busca os gastos contábeis ordenados por vencimento
    gastos = GastoContabilidade.objects.all().order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Contabilidade_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        GastoContabilidadeExcelService.gerar_relatorio_contabilidade(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_cartoes(request):
    # FILTRO: Apenas Sicoob e Bradesco (ignora BNDES)
    # Note o uso do __in para filtrar múltiplos valores
    gastos = FaturaCartao.objects.filter(
        cartao__in=['PF_SICOOB', 'PF_BRADESCO']
    ).order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Cartoes_SicoobBradesco_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        FaturaCartaoExcelService.gerar_relatorio_cartoes(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_bndes(request):
    # FILTRO: Apenas BNDES
    gastos = FaturaCartao.objects.filter(cartao='BNDES').order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_BNDES_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel usando o serviço específico
        BNDESExcelService.gerar_relatorio_bndes(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo BNDES não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_gastos_gerais(request):
    # Busca todos os gastos gerais por data
    gastos = GastoGeral.objects.all().order_by('-data_gasto')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_GastosGerais_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        GastoGeralExcelService.gerar_relatorio_geral(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
def exportar_veiculos(request):
    # Busca todos os gastos de veículos
    gastos = GastoVeiculoConsorcio.objects.all().order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Veiculos_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
def exportar_condominio(request):
    # FILTRO: Apenas Condomínio, Taxa de Averbação e Acordo.
    # Excluindo explicitamente IPTU ou filtrando pelos permitidos.
    # Assumindo que o campo no banco se chama 'tipo_gasto'.
    
    tipos_desejados = ['CONDO', 'TAXA', 'ACORDO']
    
    gastos = GastoImovel.objects.filter(
        tipo_gasto__in=tipos_desejados
    ).order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Condominio_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        GastoImovelExcelService.gerar_relatorio_condominio(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_iptu(request):
    # FILTRO: Apenas IPTU
    gastos = GastoImovel.objects.filter(
        tipo_gasto='IPTU'
    ).order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_IPTU_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        GastoIPTUExcelService.gerar_relatorio_iptu(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
def exportar_gasolina(request):
    # Busca ordenado por data do gasto
    gastos = GastoGasolina.objects.all().order_by('-data_gasto')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Gasolina_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        GastoGasolinaExcelService.gerar_relatorio_gasolina(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
def exportar_comissoes(request):
    # Busca todos os pagamentos de RT
    # Otimização: Traz junto os dados do contrato e da arquiteta para evitar N+1 queries
    pagamentos = PagamentoRT.objects.select_related('contrato', 'contrato__arquiteta').all().order_by('-data_pagamento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Comissoes_Arquitetos_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        ComissaoExcelService.gerar_relatorio_comissoes(pagamentos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
def exportar_prestacoes(request):
    # Busca todas as prestações ordenadas por vencimento
    gastos = PrestacaoEmprestimo.objects.all().order_by('-data_vencimento')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Prestacoes_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(gastos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    


def exportar_folha(request):
    # Otimização com select_related para evitar lentidão
    pagamentos = FolhaPagamento.objects.select_related(
        'funcionario', 
        'funcionario__dados_trabalhistas'
    ).order_by('-data_referencia', 'funcionario__nome')

    # Nome do arquivo
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_FolhaPagamento_{data_hoje}.xlsx"
    caminho_temp = os.path.join(settings.MEDIA_ROOT, nome_arquivo)

    try:
        # Gera o Excel
        FuncionarioFolhaExcelService.gerar_relatorio_folha(pagamentos, caminho_arquivo=caminho_temp)

        # Retorna o arquivo
        if os.path.exists(caminho_temp):
            return FileResponse(
                open(caminho_temp, 'rb'), 
                as_attachment=True, 
                filename=nome_arquivo
            )
        else:
            return HttpResponse("Erro: Arquivo não gerado.", status=500)

    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)