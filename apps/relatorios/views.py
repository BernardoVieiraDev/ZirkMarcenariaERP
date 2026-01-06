import calendar
import io
from datetime import date, datetime
from decimal import Decimal
from itertools import chain

import xlsxwriter
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from apps.comissionamento.models import Arquiteta, ContratoRT
from apps.financeiro.fluxo.services import FluxoCaixaService
# Imports dos Models
from apps.financeiro.pagar.models import (Boleto, Cheque, ComissaoArquiteto,
                                          FaturaCartao, FolhaPagamento,
                                          GastoContabilidade, GastoGasolina,
                                          GastoGeral, GastoImovel,
                                          GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)
from apps.financeiro.receber.models import (Banco, CaixaDiario, MovimentoBanco,
                                            Receber)
from apps.relatorios.services.movimento_banco import MovimentoBancoExcelService
from apps.socios.services import SocioExcelService

# Imports dos Services
from .extensions import (BNDESExcelService, BoletoExcelService,
                         CaixaDiarioExcelService, ChequeExcelService,
                         ComissaoExcelService, ExportRTService,
                         FaturaCartaoExcelService,
                         FuncionarioFolhaExcelService,
                         GastoContabilidadeExcelService,
                         GastoGasolinaExcelService, GastoGeralExcelService,
                         GastoImovelExcelService, GastoIPTUExcelService,
                         GastoUtilidadeExcelService,
                         GastoVeiculoConsorcioExcelService,
                         PrestacaoEmprestimoExcelService, ReceberExcelService,
                         RelatorioPagarMensalService,
                         RelatorioReceberMensalService, VendasExcelService,
                         gerar_relatorio_movimento_banco)
from .services.fluxo_caixa_export import RelatorioFluxoCaixaExport


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
    pagamentos = ContratoRT.objects.select_related('arquiteta')\
        .filter(valor_pago__isnull=False)\
        .order_by('-data_pagamento')
    
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


def exportar_multiplas_planilhas(request):
    """
    Consolidado Rápido (Todas as datas/Geral)
    """
    if request.method != 'POST':
        return redirect('relatorios:list_planilhas')

    relatorios = request.POST.getlist('relatorios')
    if not relatorios:
        return HttpResponse("Nenhum relatório selecionado.", status=400)
    
    now = datetime.now()
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    
    try:
        if 'boletos' in relatorios:
            BoletoExcelService.gerar_relatorio_geral(Boleto.objects.all().order_by('-data_vencimento'), workbook=wb)
        if 'utilidades' in relatorios:
            GastoUtilidadeExcelService.gerar_relatorio_utilidades(GastoUtilidade.objects.all().order_by('-data_vencimento'), workbook=wb)
        if 'cheques' in relatorios:
            ChequeExcelService.gerar_relatorio_cheques(Cheque.objects.all().order_by('-data_emissao'), workbook=wb)
        if 'contabilidade' in relatorios:
            GastoContabilidadeExcelService.gerar_relatorio_contabilidade(GastoContabilidade.objects.all().order_by('-data_vencimento'), workbook=wb)
        if 'cartoes' in relatorios:
            FaturaCartaoExcelService.gerar_relatorio_cartoes(FaturaCartao.objects.filter(cartao__in=['PF_SICOOB', 'PF_BRADESCO']).order_by('-data_vencimento'), workbook=wb)
        if 'bndes' in relatorios:
            BNDESExcelService.gerar_relatorio_bndes(FaturaCartao.objects.filter(cartao='BNDES').order_by('-data_vencimento'), workbook=wb)
        if 'gastos_gerais' in relatorios:
            GastoGeralExcelService.gerar_relatorio_geral(GastoGeral.objects.all().order_by('-data_gasto'), workbook=wb)
        if 'veiculos' in relatorios:
            GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(GastoVeiculoConsorcio.objects.all().order_by('-data_vencimento'), workbook=wb)
        if 'condominio' in relatorios:
            GastoImovelExcelService.gerar_relatorio_condominio(GastoImovel.objects.filter(tipo_gasto__in=['CONDO', 'TAXA', 'ACORDO']).order_by('-data_vencimento'), workbook=wb)
        if 'iptu' in relatorios:
            GastoIPTUExcelService.gerar_relatorio_iptu(GastoImovel.objects.filter(tipo_gasto='IPTU').order_by('-data_vencimento'), workbook=wb)
        if 'gasolina' in relatorios:
            GastoGasolinaExcelService.gerar_relatorio_gasolina(GastoGasolina.objects.all().order_by('-data_gasto'), workbook=wb)
        if 'comissoes' in relatorios:
            ComissaoExcelService.gerar_relatorio_comissoes(ContratoRT.objects.select_related('arquiteta').filter(valor_pago__isnull=False).order_by('-data_pagamento'), workbook=wb)
        if 'prestacoes' in relatorios:
            PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(PrestacaoEmprestimo.objects.all().order_by('-data_vencimento'), workbook=wb)
        if 'folha' in relatorios:
            FuncionarioFolhaExcelService.gerar_relatorio_folha(FolhaPagamento.objects.select_related('funcionario').all().order_by('-data_referencia'), workbook=wb)
        if 'receber' in relatorios:
            ReceberExcelService.gerar_relatorio_receber(Receber.objects.all().order_by('data_vencimento'), workbook=wb)
        
        # --- CORREÇÃO AQUI: Passar argumentos NOMEADOS para evitar erro de formato ---
        if 'pagar_mensal' in relatorios:
            # Gera aba "Pagar_MM_AAAA"
            RelatorioPagarMensalService.gerar_arquivo(mes=now.month, ano=now.year, workbook=wb)
                    
        if 'receber_mensal' in relatorios:
            # Gera aba "Receber_MM_AAAA"
            RelatorioReceberMensalService.gerar_arquivo(mes=now.month, ano=now.year, workbook=wb)

    except Exception as e:
        wb.close()
        return HttpResponse(f"Erro ao gerar planilhas unificadas: {e}", status=500)

    wb.close()
    
    custom_name = request.POST.get('nome_arquivo', '').strip()
    
    if custom_name:
        if not custom_name.lower().endswith('.xlsx'):
            custom_name += '.xlsx'
        filename = custom_name
    else:
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"Relatorio_Consolidado_{hoje_str}.xlsx"

    output.seek(0)
    return FileResponse(output, as_attachment=True, filename=filename)


def exportar_receber(request):
    dados = Receber.objects.all().order_by('data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_ContasReceber_{data_hoje}.xlsx"

    try:
        buffer = ReceberExcelService.gerar_relatorio_receber(dados)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_rt(request):
    arquiteta_id = request.GET.get('arquiteta_id')
    if not arquiteta_id:
        return HttpResponse("Erro: Nenhuma arquiteta selecionada.", status=400)

    arquiteta = get_object_or_404(Arquiteta, pk=arquiteta_id)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    clean_name = "".join(x for x in arquiteta.nome if x.isalnum())
    filename = f"Relatorio_RT_{clean_name}_{datetime.now().strftime('%d%m')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    service = ExportRTService()
    service.generate_relatorio_individual(arquiteta)
    service.save(response)
    
    return response

def list_planilhas_periodo(request):
    bancos = Banco.objects.all()
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    context = {
        'bancos': bancos,
        'meses': meses,
    }
    return render(request, 'core/planilhas/list_periodo.html', context)

def exportar_por_periodo(request):
    if request.method != 'POST':
        return redirect('relatorios:planilhas_por_periodo')

    tipo = request.POST.get('tipo_relatorio')
    inicio_str = request.POST.get('data_inicio')
    fim_str = request.POST.get('data_fim')

    if not inicio_str or not fim_str:
        return HttpResponse("Datas obrigatórias.", status=400)

    dt_inicio = parse_date(inicio_str)
    dt_fim = parse_date(fim_str)
    periodo_str = f"{dt_inicio.strftime('%d%m')}_{dt_fim.strftime('%d%m')}"
    
    buffer = None
    filename = f"Relatorio_{tipo}_{periodo_str}.xlsx"

    try:
        if tipo == 'boletos':
            dados = Boleto.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = BoletoExcelService.gerar_relatorio_geral(dados)

        elif tipo == 'utilidades':
            dados = GastoUtilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = GastoUtilidadeExcelService.gerar_relatorio_utilidades(dados)
            
        elif tipo == 'cheques':
            dados = Cheque.objects.filter(data_emissao__range=[dt_inicio, dt_fim]).order_by('data_emissao')
            buffer = ChequeExcelService.gerar_relatorio_cheques(dados)

        elif tipo == 'contabilidade':
            dados = GastoContabilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = GastoContabilidadeExcelService.gerar_relatorio_contabilidade(dados)

        elif tipo == 'cartoes':
            dados = FaturaCartao.objects.filter(
                cartao__in=['PF_SICOOB', 'PF_BRADESCO'],
                data_vencimento__range=[dt_inicio, dt_fim]
            ).order_by('data_vencimento')
            buffer = FaturaCartaoExcelService.gerar_relatorio_cartoes(dados)

        elif tipo == 'bndes':
            dados = FaturaCartao.objects.filter(cartao='BNDES', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = BNDESExcelService.gerar_relatorio_bndes(dados)

        elif tipo == 'gastos_gerais':
            dados = GastoGeral.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto')
            buffer = GastoGeralExcelService.gerar_relatorio_geral(dados)

        elif tipo == 'veiculos':
            dados = GastoVeiculoConsorcio.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(dados)

        elif tipo == 'condominio':
            dados = GastoImovel.objects.filter(
                tipo_gasto__in=['CONDO', 'TAXA', 'ACORDO'],
                data_vencimento__range=[dt_inicio, dt_fim]
            ).order_by('data_vencimento')
            buffer = GastoImovelExcelService.gerar_relatorio_condominio(dados)

        elif tipo == 'iptu':
            dados = GastoImovel.objects.filter(tipo_gasto='IPTU', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = GastoIPTUExcelService.gerar_relatorio_iptu(dados)

        elif tipo == 'gasolina':
            dados = GastoGasolina.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto')
            buffer = GastoGasolinaExcelService.gerar_relatorio_gasolina(dados)

        elif tipo == 'prestacoes':
            dados = PrestacaoEmprestimo.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(dados)

        elif tipo == 'comissoes':
            dados = ContratoRT.objects.filter(
                data_pagamento__range=[dt_inicio, dt_fim],
                valor_pago__isnull=False
            ).select_related('arquiteta').order_by('data_pagamento')
            buffer = ComissaoExcelService.gerar_relatorio_comissoes(dados)
            
        elif tipo == 'folha':
            dados = FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia')
            buffer = FuncionarioFolhaExcelService.gerar_relatorio_folha(dados)
            
        elif tipo == 'receber':
            dados = Receber.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = ReceberExcelService.gerar_relatorio_receber(dados, ano=dt_inicio.year)
        else:
            return HttpResponse(f"Relatório '{tipo}' desconhecido.", status=400)

        return FileResponse(buffer, as_attachment=True, filename=filename)

    except Exception as e:
        return HttpResponse(f"Erro ao gerar planilha: {e}", status=500)


def exportar_consolidado_periodo(request):
    """
    Consolidado por Período (Com filtro de datas)
    """
    if request.method != 'POST':
        return redirect('relatorios:planilhas_por_periodo')

    relatorios = request.POST.getlist('relatorios')
    inicio_str = request.POST.get('data_inicio')
    fim_str = request.POST.get('data_fim')

    if not relatorios or not inicio_str or not fim_str:
        return HttpResponse("Selecione relatórios e período.", status=400)

    dt_inicio = parse_date(inicio_str)
    dt_fim = parse_date(fim_str)
    
    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})

    try:
        # --- Relatórios Individuais ---
        if 'boletos' in relatorios:
            BoletoExcelService.gerar_relatorio_geral(Boleto.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'utilidades' in relatorios:
            GastoUtilidadeExcelService.gerar_relatorio_utilidades(GastoUtilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'cheques' in relatorios:
            ChequeExcelService.gerar_relatorio_cheques(Cheque.objects.filter(data_emissao__range=[dt_inicio, dt_fim]).order_by('data_emissao'), workbook=wb)
        
        if 'contabilidade' in relatorios:
            GastoContabilidadeExcelService.gerar_relatorio_contabilidade(GastoContabilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'cartoes' in relatorios:
            FaturaCartaoExcelService.gerar_relatorio_cartoes(FaturaCartao.objects.filter(cartao__in=['PF_SICOOB', 'PF_BRADESCO'], data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'bndes' in relatorios:
            BNDESExcelService.gerar_relatorio_bndes(FaturaCartao.objects.filter(cartao='BNDES', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'gastos_gerais' in relatorios:
            GastoGeralExcelService.gerar_relatorio_geral(GastoGeral.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), workbook=wb)
        
        if 'veiculos' in relatorios:
            GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(GastoVeiculoConsorcio.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'condominio' in relatorios:
            GastoImovelExcelService.gerar_relatorio_condominio(GastoImovel.objects.filter(tipo_gasto__in=['CONDO', 'TAXA', 'ACORDO'], data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'iptu' in relatorios:
            GastoIPTUExcelService.gerar_relatorio_iptu(GastoImovel.objects.filter(tipo_gasto='IPTU', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'gasolina' in relatorios:
            GastoGasolinaExcelService.gerar_relatorio_gasolina(GastoGasolina.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), workbook=wb)
        
        if 'prestacoes' in relatorios:
            PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(PrestacaoEmprestimo.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), workbook=wb)
        
        if 'comissoes' in relatorios:
            qs_comissao = ContratoRT.objects.select_related('arquiteta').filter(valor_pago__isnull=False, data_pagamento__range=[dt_inicio, dt_fim]).order_by('-data_pagamento')
            ComissaoExcelService.gerar_relatorio_comissoes(qs_comissao, workbook=wb)

        if 'folha' in relatorios:
            FuncionarioFolhaExcelService.gerar_relatorio_folha(FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia'), workbook=wb)
        
        if 'receber' in relatorios:
            qs_receber_lista = Receber.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            ReceberExcelService.gerar_relatorio_receber(qs_receber_lista, workbook=wb, ano=dt_inicio.year)
        
        # --- ADICIONADO: Pagar e Receber Mensal no Consolidado por Período ---
        if 'pagar_mensal' in relatorios:
            # Usa o modo "Range" do serviço
            RelatorioPagarMensalService.gerar_arquivo(inicio=dt_inicio, fim=dt_fim, workbook=wb)

        if 'receber_mensal' in relatorios:
             # Usa o modo "Range" do serviço
            RelatorioReceberMensalService.gerar_arquivo(inicio=dt_inicio, fim=dt_fim, workbook=wb)
        # ---------------------------------------------------------------------

        # --- Relatório de Análise (Vendas/Desempenho) ---
        if 'vendas' in relatorios or 'vendas_compras' in relatorios:
            qs_receber_vendas = Receber.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            
            dados_pagar = list(chain(
                Boleto.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                GastoUtilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                Cheque.objects.filter(data_emissao__range=[dt_inicio, dt_fim]),
                GastoContabilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                FaturaCartao.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                GastoGeral.objects.filter(data_gasto__range=[dt_inicio, dt_fim]),
                GastoVeiculoConsorcio.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                GastoImovel.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                GastoGasolina.objects.filter(data_gasto__range=[dt_inicio, dt_fim]),
                PrestacaoEmprestimo.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]),
                ContratoRT.objects.filter(data_pagamento__range=[dt_inicio, dt_fim], valor_pago__isnull=False),
                FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim])
            ))
            VendasExcelService.gerar_relatorio_vendas(qs_receber_vendas, dados_pagar, workbook=wb)

    except Exception as e:
        wb.close()
        print(f"Erro ao gerar planilhas: {e}")
        return HttpResponse(f"Erro ao consolidar: {e}", status=500)

    wb.close()

    custom_name = request.POST.get('nome_arquivo', '').strip()
    
    if custom_name:
        if not custom_name.lower().endswith('.xlsx'):
            custom_name += '.xlsx'
        filename = custom_name
    else:
        periodo_str = f"{dt_inicio.strftime('%d%m')}_{dt_fim.strftime('%d%m')}"
        filename = f"Consolidado_Periodo_{periodo_str}.xlsx"
    
    output.seek(0)
    return FileResponse(output, as_attachment=True, filename=filename)


def exportar_vendas(request):
    # 1. Pega ano e MÊS (novo) da URL
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    
    try:
        ano = int(request.GET.get('ano', ano_atual))
    except ValueError:
        ano = ano_atual
        
    mes_param = request.GET.get('mes')
    mes = int(mes_param) if mes_param else None

    # 2. Busca e Filtra dados de Receber (Vendas)
    qs_receber = Receber.objects.all()
    dados_receber = []
    for r in qs_receber:
        if r.data_vencimento and r.data_vencimento.year == ano:
            # Se mês foi informado, filtra também pelo mês
            if mes and r.data_vencimento.month != mes:
                continue
            dados_receber.append(r)
    
    # 3. Busca e Unifica dados de Pagar (Compras/Despesas)
    qs_boletos = Boleto.objects.all()
    qs_gerais = GastoGeral.objects.all()
    qs_cartao = FaturaCartao.objects.all()
    qs_util = GastoUtilidade.objects.all()
    qs_cheque = Cheque.objects.all()
    qs_emp = PrestacaoEmprestimo.objects.all()
    qs_veic = GastoVeiculoConsorcio.objects.all()
    qs_cont = GastoContabilidade.objects.all()
    qs_imov = GastoImovel.objects.all()
    qs_gas = GastoGasolina.objects.all()
    qs_folha = FolhaPagamento.objects.all()
    qs_comissao = ComissaoArquiteto.objects.all()

    todos_pagar = list(chain(
        qs_boletos, qs_gerais, qs_cartao, qs_util, qs_cheque, 
        qs_emp, qs_veic, qs_cont, qs_imov, qs_gas, qs_folha, qs_comissao
    ))
    
    # 4. Filtra Compras pelo Ano (e Mês se selecionado)
    dados_pagar_filtrados = []
    for item in todos_pagar:
        data = getattr(item, 'data_vencimento', None)
        if not data:
            data = getattr(item, 'data_gasto', None)
        if not data:
            data = getattr(item, 'data_pagamento', None)
        if not data:
            data = getattr(item, 'data_referencia', None)

        if data and data.year == ano:
            if mes and data.month != mes:
                continue
            dados_pagar_filtrados.append(item)

    if mes:
        nome_arquivo = f"Relatorio_Vendas_Compras_{mes:02d}_{ano}.xlsx"
    else:
        nome_arquivo = f"Relatorio_Desempenho_Vendas_Compras_{ano}.xlsx"

    try:
        buffer = VendasExcelService.gerar_relatorio_vendas(dados_receber, dados_pagar_filtrados)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

def exportar_caixa_diario(request):
    hoje = date.today()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except ValueError:
        ano = hoje.year
        mes = hoje.month

    data_inicio = date(ano, mes, 1)
    
    entradas_ant = CaixaDiario.objects.filter(data__lt=data_inicio, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    saidas_ant = CaixaDiario.objects.filter(data__lt=data_inicio, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    saldo_anterior = entradas_ant - saidas_ant

    movimentacoes = CaixaDiario.objects.filter(
        data__year=ano, 
        data__month=mes
    ).order_by('data', 'id')

    total_entradas = movimentacoes.filter(tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    total_saidas = movimentacoes.filter(tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    saldo_atual = saldo_anterior + total_entradas - total_saidas

    resumo = {
        'saldo_anterior': saldo_anterior,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_atual': saldo_atual
    }

    try:
        buffer = CaixaDiarioExcelService.gerar_relatorio(movimentacoes, resumo, ano, mes)
        filename = f"Caixa_Diario_{mes:02d}_{ano}.xlsx"
        return FileResponse(buffer, as_attachment=True, filename=filename)
    except Exception as e:
        return HttpResponse(f"Erro ao gerar Excel: {str(e)}", status=500)
    

def exportar_movimentacao_bancaria(request):
    hoje = datetime.now()
    try:
        mes = int(request.GET.get('mes', hoje.month))
        ano = int(request.GET.get('ano', hoje.year))
        banco_id = request.GET.get('banco_id')
        if banco_id:
            banco_id = int(banco_id)
        else:
            return HttpResponse("Erro: Parâmetro 'banco_id' é obrigatório.", status=400)
            
    except ValueError:
        return HttpResponse("Erro: Parâmetros inválidos (mes, ano ou banco_id).", status=400)

    excel_file = gerar_relatorio_movimento_banco(ano, mes, banco_id)

    if not excel_file:
        return HttpResponse("Erro ao gerar o relatório ou banco não encontrado.", status=404)

    filename = f"Movimento_Bancario_{mes:02d}_{ano}.xlsx"
    response = HttpResponse(
        excel_file,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

def _get_mes_ano(request):
    hoje = datetime.now()
    try:
        mes = int(request.GET.get('mes', hoje.month))
        ano = int(request.GET.get('ano', hoje.year))
    except ValueError:
        mes, ano = hoje.month, hoje.year
    return mes, ano

def exportar_pagar_mensal(request):
    dt_inicio = request.GET.get('data_inicio')
    dt_fim = request.GET.get('data_fim')

    if dt_inicio and dt_fim:
        inicio = parse_date(dt_inicio)
        fim = parse_date(dt_fim)
        excel_file = RelatorioPagarMensalService.gerar_arquivo(inicio=inicio, fim=fim)
        filename = f"Pagar_{inicio.strftime('%d%m')}_{fim.strftime('%d%m')}.xlsx"
    else:
        mes, ano = _get_mes_ano(request)
        excel_file = RelatorioPagarMensalService.gerar_arquivo(mes=mes, ano=ano)
        filename = f"Pagar_{mes:02d}_{ano}.xlsx"
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def exportar_receber_mensal(request):
    dt_inicio = request.GET.get('data_inicio')
    dt_fim = request.GET.get('data_fim')

    if dt_inicio and dt_fim:
        inicio = parse_date(dt_inicio)
        fim = parse_date(dt_fim)
        excel_file = RelatorioReceberMensalService.gerar_arquivo(inicio=inicio, fim=fim)
        filename = f"Receber_{inicio.strftime('%d%m')}_{fim.strftime('%d%m')}.xlsx"
    else:
        mes, ano = _get_mes_ano(request)
        excel_file = RelatorioReceberMensalService.gerar_arquivo(mes=mes, ano=ano)
        filename = f"Receber_{mes:02d}_{ano}.xlsx"
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def exportar_pacote(request, tipo_pacote):
    hoje = datetime.now()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except ValueError:
        ano = hoje.year
        mes = hoje.month

    dt_inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    dt_fim = date(ano, mes, ultimo_dia)

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    
    filename = f"Pacote_{tipo_pacote.upper()}_{mes:02d}_{ano}.xlsx"

    try:
        if tipo_pacote == 'pagar':
            BoletoExcelService.gerar_relatorio_geral(
                Boleto.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoUtilidadeExcelService.gerar_relatorio_utilidades(
                GastoUtilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            ChequeExcelService.gerar_relatorio_cheques(
                Cheque.objects.filter(data_emissao__range=[dt_inicio, dt_fim]).order_by('data_emissao'), 
                workbook=wb
            )
            GastoContabilidadeExcelService.gerar_relatorio_contabilidade(
                GastoContabilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(
                PrestacaoEmprestimo.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            FaturaCartaoExcelService.gerar_relatorio_cartoes(
                FaturaCartao.objects.filter(cartao__in=['PF_SICOOB', 'PF_BRADESCO'], data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            BNDESExcelService.gerar_relatorio_bndes(
                FaturaCartao.objects.filter(cartao='BNDES', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoGeralExcelService.gerar_relatorio_geral(
                GastoGeral.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), 
                workbook=wb
            )
            GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(
                GastoVeiculoConsorcio.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoIPTUExcelService.gerar_relatorio_iptu(
                GastoImovel.objects.filter(tipo_gasto='IPTU', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoImovelExcelService.gerar_relatorio_condominio(
                GastoImovel.objects.filter(tipo_gasto__in=['CONDO', 'TAXA', 'ACORDO'], data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoGasolinaExcelService.gerar_relatorio_gasolina(
                GastoGasolina.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), 
                workbook=wb
            )
            ComissaoExcelService.gerar_relatorio_comissoes(
                ContratoRT.objects.select_related('arquiteta').filter(valor_pago__isnull=False, data_pagamento__range=[dt_inicio, dt_fim]).order_by('-data_pagamento'), 
                workbook=wb
            )
            FuncionarioFolhaExcelService.gerar_relatorio_folha(
                FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia'), 
                workbook=wb
            )
            # Passando argumentos nomeados corretamente:
            RelatorioPagarMensalService.gerar_arquivo(mes=mes, ano=ano, workbook=wb)

        elif tipo_pacote == 'sebrae':
            SocioExcelService.gerar_planilha_anual(ano=ano, workbook=wb)
            
            qs_receber = Receber.objects.filter(data_vencimento__year=ano)
            qs_pagar_all = list(chain(
                Boleto.objects.filter(data_vencimento__year=ano),
                GastoGeral.objects.filter(data_gasto__year=ano),
                FaturaCartao.objects.filter(data_vencimento__year=ano),
                GastoUtilidade.objects.filter(data_vencimento__year=ano),
            ))
            VendasExcelService.gerar_relatorio_vendas(qs_receber, qs_pagar_all, workbook=wb)
            
            data_inicio_caixa = date(ano, mes, 1)
            entradas_ant = CaixaDiario.objects.filter(data__lt=data_inicio_caixa, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            saidas_ant = CaixaDiario.objects.filter(data__lt=data_inicio_caixa, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            resumo_caixa = {
                'saldo_anterior': entradas_ant - saidas_ant,
                'total_entradas': CaixaDiario.objects.filter(data__year=ano, data__month=mes, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s'],
                'total_saidas': CaixaDiario.objects.filter(data__year=ano, data__month=mes, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s'],
            }
            resumo_caixa['saldo_atual'] = resumo_caixa['saldo_anterior'] + resumo_caixa['total_entradas'] - resumo_caixa['total_saidas']
            
            mov_caixa = CaixaDiario.objects.filter(data__year=ano, data__month=mes).order_by('data')
            CaixaDiarioExcelService.gerar_relatorio(mov_caixa, resumo_caixa, ano, mes, workbook=wb)
            
            bancos = Banco.objects.all()
            for banco in bancos:
                entradas_b = MovimentoBanco.objects.filter(banco=banco, data__lt=dt_inicio, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
                saidas_b = MovimentoBanco.objects.filter(banco=banco, data__lt=dt_inicio, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
                saldo_ant_b = banco.saldo_inicial + entradas_b - saidas_b
                
                movs_b = MovimentoBanco.objects.filter(banco=banco, data__year=ano, data__month=mes).order_by('data')
                tot_ent = sum(m.valor for m in movs_b if m.tipo == 'E')
                tot_sai = sum(m.valor for m in movs_b if m.tipo == 'S')
                
                resumo_b = {
                    'saldo_anterior': saldo_ant_b,
                    'total_entradas': tot_ent,
                    'total_saidas': tot_sai,
                    'saldo_atual': saldo_ant_b + tot_ent - tot_sai
                }
                MovimentoBancoExcelService.gerar_excel(banco, movs_b, resumo_b, ano, mes, workbook=wb)

            RelatorioReceberMensalService.gerar_arquivo(mes=mes, ano=ano, workbook=wb)
            RelatorioPagarMensalService.gerar_arquivo(mes=mes, ano=ano, workbook=wb)
            
            RelatorioFluxoCaixaExport.gerar_excel(dt_inicio, 31, "Mensal", workbook=wb)

        else:
            return HttpResponse("Tipo de pacote inválido", status=400)

    except Exception as e:
        print(f"Erro pacote: {e}")
        wb.close()
        return HttpResponse(f"Erro ao gerar pacote: {e}", status=500)

    wb.close()
    output.seek(0)
    return FileResponse(output, as_attachment=True, filename=filename)