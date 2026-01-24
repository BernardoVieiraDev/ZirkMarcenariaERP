import calendar
import datetime
import io
from datetime import date, datetime
from decimal import Decimal
from itertools import chain

import xlsxwriter
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
                                          GastoUtilidade, GastoAlmoco,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)
from apps.financeiro.receber.models import (Banco, CaixaDiario, MovimentoBanco,
                                            Receber)
from apps.relatorios.services.movimento_banco import MovimentoBancoExcelService
from apps.socios.models import LancamentoSocio
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
                         HoleriteExcelService, PrestacaoEmprestimoExcelService,
                         ReceberExcelService, RelatorioPagarMensalService,
                         RelatorioReceberMensalService,GastoAlmocoExcelService,
                         gerar_relatorio_movimento_banco)
from .services.fluxo_caixa_export import RelatorioFluxoCaixaExport
from .services.relatorio_anual_consolidado import RelatorioAnualConsolidado


# ... (imports existentes)

@login_required
def list_planilhas(request):
    # ADICIONE ESTE BLOCO DE CÓDIGO
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
    # FIM DA ADIÇÃO
    
    # Passe o context para o render
    return render(request, 'core/planilhas/list.html', context)

@login_required
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

@login_required
def exportar_utilidades(request):
    gastos = GastoUtilidade.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Utilidades_{data_hoje}.xlsx"

    try:
        buffer = GastoUtilidadeExcelService.gerar_relatorio_utilidades(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
def exportar_cheques(request):
    cheques = Cheque.objects.all().order_by('-data_emissao')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Cheques_{data_hoje}.xlsx"

    try:
        buffer = ChequeExcelService.gerar_relatorio_cheques(cheques)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
def exportar_contabilidade(request):
    gastos = GastoContabilidade.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Contabilidade_{data_hoje}.xlsx"

    try:
        buffer = GastoContabilidadeExcelService.gerar_relatorio_contabilidade(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
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

@login_required
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

@login_required
def exportar_gastos_gerais(request):
    gastos = GastoGeral.objects.all().order_by('-data_gasto')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_GastosGerais_{data_hoje}.xlsx"

    try:
        buffer = GastoGeralExcelService.gerar_relatorio_geral(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
def exportar_veiculos(request):
    gastos = GastoVeiculoConsorcio.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Veiculos_{data_hoje}.xlsx"

    try:
        buffer = GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
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

@login_required
def exportar_iptu(request):
    gastos = GastoImovel.objects.filter(tipo_gasto='IPTU').order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_IPTU_{data_hoje}.xlsx"

    try:
        buffer = GastoIPTUExcelService.gerar_relatorio_iptu(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
def exportar_gasolina(request):
    gastos = GastoGasolina.objects.all().order_by('-data_gasto')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Gasolina_{data_hoje}.xlsx"

    try:
        buffer = GastoGasolinaExcelService.gerar_relatorio_gasolina(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
def exportar_comissoes(request):
    # CORREÇÃO: Usando ComissaoArquiteto em vez de ContratoRT
    pagamentos = ComissaoArquiteto.objects.select_related('arquiteto', 'contrato_rt', 'contrato_rt__cliente')\
        .all()\
        .order_by('-data_pagamento')
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Comissoes_Arquitetos_{data_hoje}.xlsx"

    try:
        buffer = ComissaoExcelService.gerar_relatorio_comissoes(pagamentos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    

@login_required
def exportar_prestacoes(request):
    gastos = PrestacaoEmprestimo.objects.all().order_by('-data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Prestacoes_{data_hoje}.xlsx"

    try:
        buffer = PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
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

@login_required
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
        if 'almoco' in relatorios:
            GastoAlmocoExcelService.gerar_relatorio_almoco(
                GastoAlmoco.objects.all().order_by('-data_gasto'), 
                workbook=wb
            )
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
            # CORREÇÃO: Usando ComissaoArquiteto
            ComissaoExcelService.gerar_relatorio_comissoes(
                ComissaoArquiteto.objects.select_related('arquiteto', 'contrato_rt', 'contrato_rt__cliente').all().order_by('-data_pagamento'), 
                workbook=wb
            )
        if 'prestacoes' in relatorios:
            PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(PrestacaoEmprestimo.objects.all().order_by('-data_vencimento'), workbook=wb)
        if 'folha' in relatorios:
            FuncionarioFolhaExcelService.gerar_relatorio_folha(FolhaPagamento.objects.select_related('funcionario').all().order_by('-data_referencia'), workbook=wb)
        if 'receber' in relatorios:
            ReceberExcelService.gerar_relatorio_receber(Receber.objects.all().order_by('data_vencimento'), workbook=wb)
        
        if 'pagar_mensal' in relatorios:
            RelatorioPagarMensalService.gerar_arquivo(mes=now.month, ano=now.year, workbook=wb)
                    
        if 'receber_mensal' in relatorios:
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

@login_required
def exportar_receber(request):
    dados = Receber.objects.all().order_by('data_vencimento')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_ContasReceber_{data_hoje}.xlsx"

    try:
        buffer = ReceberExcelService.gerar_relatorio_receber(dados)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)
    
@login_required
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

@login_required
def exportar_almoco(request):
    gastos = GastoAlmoco.objects.all().order_by('-data_gasto')
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"Relatorio_Almoco_{data_hoje}.xlsx"

    try:
        buffer = GastoAlmocoExcelService.gerar_relatorio_almoco(gastos)
        return FileResponse(buffer, as_attachment=True, filename=nome_arquivo)
    except Exception as e:
        return HttpResponse(f"Erro interno: {str(e)}", status=500)

@login_required
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

@login_required
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
    if not dt_inicio or not dt_fim:
        return HttpResponse("Datas inválidas.", status=400)
    
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
            
        elif tipo == 'relatorio_anual_consolidado':
            service = RelatorioAnualConsolidado(inicio=dt_inicio, fim=dt_fim)
            buffer = service.gerar()
            filename = f"Relatorio_Anual_Consolidado_{periodo_str}.xlsx"    
        elif tipo == 'almoco':
                    dados = GastoAlmoco.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto')
                    buffer = GastoAlmocoExcelService.gerar_relatorio_almoco(dados)

        elif tipo == 'fluxo_caixa':
            # Calcula a diferença de dias entre Inicio e Fim
            dias_delta = (dt_fim - dt_inicio).days + 1
            periodo_nome = f"Período {dt_inicio.strftime('%d/%m')} a {dt_fim.strftime('%d/%m')}"
            
            # Gera usando o serviço já existente
            buffer = RelatorioFluxoCaixaExport.gerar_excel(dt_inicio, dias_delta, periodo_nome)

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

        elif tipo == 'caixa_diario':
            # 1. Calcula saldo anterior ao período
            entradas_ant = CaixaDiario.objects.filter(data__lt=dt_inicio, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            saidas_ant = CaixaDiario.objects.filter(data__lt=dt_inicio, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            saldo_anterior = entradas_ant - saidas_ant

            # 2. Busca movimentações do período
            movimentacoes = CaixaDiario.objects.filter(
                data__range=[dt_inicio, dt_fim]
            ).order_by('data', 'id')

            # 3. Calcula totais do período
            total_entradas = movimentacoes.filter(tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            total_saidas = movimentacoes.filter(tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            saldo_atual = saldo_anterior + total_entradas - total_saidas

            resumo = {
                'saldo_anterior': saldo_anterior,
                'total_entradas': total_entradas,
                'total_saidas': total_saidas,
                'saldo_atual': saldo_atual
            }

            # Reutiliza o serviço existente (passando ano/mês do inicio apenas para referência no título)
            buffer = CaixaDiarioExcelService.gerar_relatorio(movimentacoes, resumo, dt_inicio.year, dt_inicio.month)

        elif tipo == 'socios':
            dados = LancamentoSocio.objects.filter(
                data__range=[dt_inicio, dt_fim]
            ).select_related('socio', 'categoria').order_by('data')

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet("Sócios")

            bold = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0', 'border': 1})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
            money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
            cell_format = workbook.add_format({'border': 1})

            headers = ['Data', 'Sócio', 'Categoria', 'Descrição/Obs', 'Valor']
            worksheet.write_row('A1', headers, bold)

            for idx, item in enumerate(dados, start=1):
                worksheet.write(idx, 0, item.data, date_format)
                worksheet.write(idx, 1, item.socio.nome if item.socio else 'Indefinido', cell_format)
                worksheet.write(idx, 2, item.categoria.nome if item.categoria else '-', cell_format)
                obs_texto = getattr(item, 'observacao', getattr(item, 'descricao', getattr(item, 'obs', '')))
                worksheet.write(idx, 3, obs_texto, cell_format)
                worksheet.write(idx, 4, item.valor, money_format)

            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:C', 25)
            worksheet.set_column('D:D', 45)
            worksheet.set_column('E:E', 15)
            
            workbook.close()
            output.seek(0)
            buffer = output

        elif tipo == 'comissoes':
            dados = ComissaoArquiteto.objects.filter(
                data_pagamento__range=[dt_inicio, dt_fim]
            ).select_related('arquiteto', 'contrato_rt', 'contrato_rt__cliente').order_by('data_pagamento')
            buffer = ComissaoExcelService.gerar_relatorio_comissoes(dados)
            
        elif tipo == 'folha':
            dados = FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia')
            buffer = FuncionarioFolhaExcelService.gerar_relatorio_folha(dados)
            
        elif tipo == 'receber':
            dados = Receber.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento')
            buffer = ReceberExcelService.gerar_relatorio_receber(dados, ano=dt_inicio.year)
        
        elif tipo == 'pacote_pagar':
            # === PACOTE CONTAS A PAGAR (POR PERÍODO) ===
            output = io.BytesIO()
            wb = xlsxwriter.Workbook(output, {'in_memory': True})
            
            # 1. Boletos
            BoletoExcelService.gerar_relatorio_geral(
                Boleto.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 2. Utilidades
            GastoUtilidadeExcelService.gerar_relatorio_utilidades(
                GastoUtilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 3. Cheques
            ChequeExcelService.gerar_relatorio_cheques(
                Cheque.objects.filter(data_emissao__range=[dt_inicio, dt_fim]).order_by('data_emissao'), 
                workbook=wb
            )
            # 4. Contabilidade
            GastoContabilidadeExcelService.gerar_relatorio_contabilidade(
                GastoContabilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 5. Prestações
            PrestacaoEmprestimoExcelService.gerar_relatorio_prestacoes(
                PrestacaoEmprestimo.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 6. Cartões
            FaturaCartaoExcelService.gerar_relatorio_cartoes(
                FaturaCartao.objects.filter(cartao__in=['PF_SICOOB', 'PF_BRADESCO'], data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 7. BNDES
            BNDESExcelService.gerar_relatorio_bndes(
                FaturaCartao.objects.filter(cartao='BNDES', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 8. Gastos Gerais
            GastoGeralExcelService.gerar_relatorio_geral(
                GastoGeral.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), 
                workbook=wb
            )
            # 9. Veículos
            GastoVeiculoConsorcioExcelService.gerar_relatorio_veiculos(
                GastoVeiculoConsorcio.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 10. IPTU
            GastoIPTUExcelService.gerar_relatorio_iptu(
                GastoImovel.objects.filter(tipo_gasto='IPTU', data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 11. Condomínio
            GastoImovelExcelService.gerar_relatorio_condominio(
                GastoImovel.objects.filter(tipo_gasto__in=['CONDO', 'TAXA', 'ACORDO'], data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            # 12. Gasolina
            GastoGasolinaExcelService.gerar_relatorio_gasolina(
                GastoGasolina.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), 
                workbook=wb
            )
            # 13. Comissões
            ComissaoExcelService.gerar_relatorio_comissoes(
                ComissaoArquiteto.objects.select_related('arquiteto', 'contrato_rt', 'contrato_rt__cliente')
                .filter(data_pagamento__range=[dt_inicio, dt_fim])
                .order_by('-data_pagamento'), 
                workbook=wb
            )
            # 14. Folha
            FuncionarioFolhaExcelService.gerar_relatorio_folha(
                FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia'), 
                workbook=wb
            )

            # SUBSTITUIÇÃO: Relatório Anual Consolidado
            RelatorioAnualConsolidado(ano=dt_inicio.year, workbook=wb).gerar()
            
            wb.close()
            output.seek(0)
            buffer = output
            
            # Ajusta nome do arquivo para Pacote
            filename = f"Pacote_Pagar_{periodo_str}.xlsx"

        else:
            return HttpResponse(f"Relatório '{tipo}' desconhecido.", status=400)

        return FileResponse(buffer, as_attachment=True, filename=filename)

    except Exception as e:
        return HttpResponse(f"Erro ao gerar planilha: {e}", status=500)

@login_required
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

    if not dt_inicio or not dt_fim:
        return HttpResponse("Datas inválidas.", status=400)
    
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

        if 'almoco' in relatorios:
                    GastoAlmocoExcelService.gerar_relatorio_almoco(
                        GastoAlmoco.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'),
                        workbook=wb
                    )
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
            # CORREÇÃO: Usando ComissaoArquiteto
            qs_comissao = ComissaoArquiteto.objects.filter(
                data_pagamento__range=[dt_inicio, dt_fim]
            ).select_related('arquiteto', 'contrato_rt', 'contrato_rt__cliente').order_by('-data_pagamento')
            ComissaoExcelService.gerar_relatorio_comissoes(qs_comissao, workbook=wb)

        if 'folha' in relatorios:
            FuncionarioFolhaExcelService.gerar_relatorio_folha(FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia'), workbook=wb)
        
        if 'receber' in relatorios:
            if not dt_inicio or not dt_fim:
                return HttpResponse("Datas inválidas.", status=400)

            qs_receber_lista = Receber.objects.filter(
                data_vencimento__range=[dt_inicio, dt_fim]
            ).order_by('data_vencimento')

            ReceberExcelService.gerar_relatorio_receber(
                qs_receber_lista,
                workbook=wb,
                ano=dt_inicio.year
            )
        
        if 'pagar_mensal' in relatorios:
            RelatorioPagarMensalService.gerar_arquivo(inicio=dt_inicio, fim=dt_fim, workbook=wb)

        if 'receber_mensal' in relatorios:
            RelatorioReceberMensalService.gerar_arquivo(inicio=dt_inicio, fim=dt_fim, workbook=wb)

        # ADIÇÃO: Relatório Anual Consolidado
        if 'relatorio_anual_consolidado' in relatorios:
            RelatorioAnualConsolidado(inicio=dt_inicio, fim=dt_fim, workbook=wb).gerar()


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
        if not dt_inicio or not dt_fim:
            return HttpResponse("Datas inválidas.", status=400)
        periodo_str = f"{dt_inicio.strftime('%d%m')}_{dt_fim.strftime('%d%m')}"
        filename = f"Consolidado_Periodo_{periodo_str}.xlsx"
    
    output.seek(0)
    return FileResponse(output, as_attachment=True, filename=filename)


@login_required
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
    
@login_required
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

@login_required
def exportar_pagar_mensal(request):
    dt_inicio = request.GET.get('data_inicio')
    dt_fim = request.GET.get('data_fim')

    if dt_inicio and dt_fim:
        inicio = parse_date(dt_inicio)
        fim = parse_date(dt_fim)

        if not inicio or not fim:
            return HttpResponse("Datas inválidas.", status=400)
        excel_file = RelatorioPagarMensalService.gerar_arquivo(inicio=inicio, fim=fim)
        filename = f"Pagar_{inicio.strftime('%d%m')}_{fim.strftime('%d%m')}.xlsx"
    else:
        mes, ano = _get_mes_ano(request)
        excel_file = RelatorioPagarMensalService.gerar_arquivo(mes=mes, ano=ano)
        filename = f"Pagar_{mes:02d}_{ano}.xlsx"
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def exportar_receber_mensal(request):
    dt_inicio = request.GET.get('data_inicio')
    dt_fim = request.GET.get('data_fim')

    if dt_inicio and dt_fim:
        inicio = parse_date(dt_inicio)
        fim = parse_date(dt_fim)
        
        
        if not inicio or not fim:
            return HttpResponse("Datas inválidas.", status=400)
        excel_file = RelatorioReceberMensalService.gerar_arquivo(inicio=inicio, fim=fim)
        filename = f"Receber_{inicio.strftime('%d%m')}_{fim.strftime('%d%m')}.xlsx"
    else:
        mes, ano = _get_mes_ano(request)
        excel_file = RelatorioReceberMensalService.gerar_arquivo(mes=mes, ano=ano)
        filename = f"Receber_{mes:02d}_{ano}.xlsx"
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def exportar_pacote(request, tipo_pacote):
    # Tenta pegar datas específicas do request (para exportação por período)
    dt_inicio_get = request.GET.get('data_inicio')
    dt_fim_get = request.GET.get('data_fim')
    
    hoje = datetime.now()
    
    # Lógica de definição de datas
    if dt_inicio_get and dt_fim_get:
        try:
            dt_inicio = parse_date(dt_inicio_get)
            dt_fim = parse_date(dt_fim_get)
            # Para serviços que exigem ano/mês estrito, usamos a data de início como referência
            ano = dt_inicio.year
            mes = dt_inicio.month
            is_periodo_customizado = True
        except:
             return HttpResponse("Datas inválidas.", status=400)
    else:
        # Fallback para lógica mensal original
        try:
            ano = int(request.GET.get('ano', hoje.year))
            mes = int(request.GET.get('mes', hoje.month))
        except ValueError:
            ano = hoje.year
            mes = hoje.month
        
        dt_inicio = date(ano, mes, 1)
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        dt_fim = date(ano, mes, ultimo_dia)
        is_periodo_customizado = False

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Nome do arquivo ajustado conforme o tipo de filtro
    if is_periodo_customizado:
        periodo_str = f"{dt_inicio.strftime('%d%m')}_{dt_fim.strftime('%d%m')}"
        filename = f"Pacote_{tipo_pacote.upper()}_{periodo_str}.xlsx"
    else:
        filename = f"Pacote_{tipo_pacote.upper()}_{mes:02d}_{ano}.xlsx"

    try:
        if tipo_pacote == 'pagar':
            # Todos os services abaixo aceitam querysets, então o filtro por range funciona perfeitamente
            BoletoExcelService.gerar_relatorio_geral(
                Boleto.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoUtilidadeExcelService.gerar_relatorio_utilidades(
                GastoUtilidade.objects.filter(data_vencimento__range=[dt_inicio, dt_fim]).order_by('data_vencimento'), 
                workbook=wb
            )
            GastoAlmocoExcelService.gerar_relatorio_almoco(
                GastoAlmoco.objects.filter(data_gasto__range=[dt_inicio, dt_fim]).order_by('data_gasto'), 
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
                ComissaoArquiteto.objects.select_related('arquiteto', 'contrato_rt', 'contrato_rt__cliente')
                .filter(data_pagamento__range=[dt_inicio, dt_fim])
                .order_by('-data_pagamento'), 
                workbook=wb
            )
            FuncionarioFolhaExcelService.gerar_relatorio_folha(
                FolhaPagamento.objects.filter(data_referencia__range=[dt_inicio, dt_fim]).order_by('data_referencia'), 
                workbook=wb
            )
            
            # --- ALTERAÇÃO: Removido RelatorioPagarMensalService e adicionado RelatorioAnualConsolidado ---
            # Passamos o 'ano' calculado no início da função e o 'workbook' atual
            relatorio_anual = RelatorioAnualConsolidado(ano=ano, workbook=wb)
            relatorio_anual.gerar()

        elif tipo_pacote == 'sebrae':
            # Nota: Alguns relatórios gerenciais do pacote SEBRAE são projetados para lógica MENSAL/ANUAL estrita.
            # Nestes casos, usamos o ano/mês da data de INÍCIO como referência.
            
            SocioExcelService.gerar_planilha_anual(ano=ano, workbook=wb)
            
            # Caixa Diário (Lógica adaptada para o range, mas mantendo a estrutura do service)
            # Se for range customizado, o saldo anterior é calculado até o dia anterior ao inicio
            entradas_ant = CaixaDiario.objects.filter(data__lt=dt_inicio, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            saidas_ant = CaixaDiario.objects.filter(data__lt=dt_inicio, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            
            # Movimentações dentro do range exato
            mov_caixa = CaixaDiario.objects.filter(data__range=[dt_inicio, dt_fim]).order_by('data')
            
            total_entradas_periodo = mov_caixa.filter(tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
            total_saidas_periodo = mov_caixa.filter(tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']

            resumo_caixa = {
                'saldo_anterior': entradas_ant - saidas_ant,
                'total_entradas': total_entradas_periodo,
                'total_saidas': total_saidas_periodo,
            }
            resumo_caixa['saldo_atual'] = resumo_caixa['saldo_anterior'] + resumo_caixa['total_entradas'] - resumo_caixa['total_saidas']
            
            # O service pede ano/mes para título, passamos o do inicio
            CaixaDiarioExcelService.gerar_relatorio(mov_caixa, resumo_caixa, ano, mes, workbook=wb)
            
            # Movimento Banco (Lógica similar ao Caixa)
            bancos = Banco.objects.all()
            for banco in bancos:
                entradas_b = MovimentoBanco.objects.filter(banco=banco, data__lt=dt_inicio, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
                saidas_b = MovimentoBanco.objects.filter(banco=banco, data__lt=dt_inicio, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
                saldo_ant_b = banco.saldo_inicial + entradas_b - saidas_b
                
                movs_b = MovimentoBanco.objects.filter(banco=banco, data__range=[dt_inicio, dt_fim]).order_by('data')
                tot_ent = sum(m.valor for m in movs_b if m.tipo == 'E')
                tot_sai = sum(m.valor for m in movs_b if m.tipo == 'S')
                
                resumo_b = {
                    'saldo_anterior': saldo_ant_b,
                    'total_entradas': tot_ent,
                    'total_saidas': tot_sai,
                    'saldo_atual': saldo_ant_b + tot_ent - tot_sai
                }
                MovimentoBancoExcelService.gerar_excel(banco, movs_b, resumo_b, ano, mes, workbook=wb)

            # Services mensais atualizados para aceitar range
            RelatorioReceberMensalService.gerar_arquivo(inicio=dt_inicio, fim=dt_fim, workbook=wb)
            RelatorioPagarMensalService.gerar_arquivo(inicio=dt_inicio, fim=dt_fim, workbook=wb)
            
            # Fluxo de Caixa (calcula dias com base no delta)
            dias_delta = (dt_fim - dt_inicio).days + 1
            RelatorioFluxoCaixaExport.gerar_excel(dt_inicio, dias_delta, "Periodo", workbook=wb)

        else:
            return HttpResponse("Tipo de pacote inválido", status=400)

    except Exception as e:
        print(f"Erro pacote: {e}")
        wb.close()
        return HttpResponse(f"Erro ao gerar pacote: {e}", status=500)

    wb.close()
    output.seek(0)
    return FileResponse(output, as_attachment=True, filename=filename)


# Em apps/financeiro/pagar/views.py ou local similar

@login_required
def download_holerite_view(request, folha_id):
    folha = FolhaPagamento.objects.get(id=folha_id)
    funcionario = folha.funcionario
    dados_trabalhistas = getattr(funcionario, 'dados_trabalhistas', None)

    # 1. Definir Título e Tipo Baseado em Regra de Negócio
    # Se você tiver um campo "tipo_folha" no model, use-o. Senão, deduza.
    titulo = "RECIBO DE PAGAMENTO DE SALÁRIO"
    if "13" in (folha.observacoes or ""):
        titulo = "RECIBO DE 13º SALÁRIO"
    elif "Ferias" in (folha.observacoes or ""):
        titulo = "RECIBO DE FÉRIAS"

    # 2. Construir Lista de Eventos (Dinâmica)
    eventos = []
    
    # Exemplo: Salário (Provento)
    if folha.salario_real > 0:
        eventos.append({
            'codigo': '001', 
            'descricao': 'SALÁRIO BASE', 
            'ref': '30d', 
            'vencimento': float(folha.salario_real),
            'desconto': 0.0
        })

    # Exemplo: Horas Extras
    if folha.horas_extras_valor > 0:
        eventos.append({
            'codigo': '002', 
            'descricao': 'HORAS EXTRAS', 
            'ref': '', 
            'vencimento': float(folha.horas_extras_valor),
            'desconto': 0.0
        })

    # Exemplo: 1/3 Férias
    if folha.ferias_terco > 0:
        eventos.append({
            'codigo': '003',
            'descricao': '1/3 FÉRIAS CONSTITUCIONAL',
            'vencimento': float(folha.ferias_terco),
            'desconto': 0.0
        })
        
    # Exemplo: Descontos (Adiantamentos/Vales)
    if folha.adiantamento > 0:
        eventos.append({
            'codigo': '101',
            'descricao': 'ADIANTAMENTO SALARIAL',
            'vencimento': 0.0,
            'desconto': float(folha.adiantamento)
        })

    # Calculando Totais (Pode pegar direto do Model se tiver campo calculado)
    total_vencimentos = sum(e['vencimento'] for e in eventos)
    total_descontos = sum(e['desconto'] for e in eventos)
    
    # Estrutura final de dados
    dados_holerite = {
        'empregador': {
            'nome': 'ZIRK MARCENARIA E INTERIORES', # Pode vir de ConfiguracaoGlobal
            'cnpj': '00.000.000/0001-00',
            'endereco': 'Rua Exemplo, 123, Bairro, Cidade-UF'
        },
        'funcionario': {
            'codigo': str(funcionario.id),
            'nome': funcionario.nome.upper(),
            'cbo': dados_trabalhistas.cbo if dados_trabalhistas else '',
            'cargo': dados_trabalhistas.funcao.upper() if dados_trabalhistas else 'NÃO INFORMADO',
            'admissao': (dados_trabalhistas.data_admissao_marcenaria or dados_trabalhistas.data_admissao_contabilidade).strftime('%d/%m/%Y') if dados_trabalhistas else ''

        },
        'cabecalho': {
            'titulo': titulo,
            'referencia': folha.data_referencia.strftime('%m/%Y')
        },
        'eventos': eventos,
        'totais': {
            'bruto': total_vencimentos,
            'descontos': total_descontos,
            'liquido': float(folha.total_funcionario) - float(folha.vale) - float(folha.adiantamento) # Ajuste sua lógica de líquido aqui
        },
        'bases': {
            # Se tiver esses dados salvos, preencha aqui
            'salario_base': float(folha.salario_real),
            'inss_base': float(folha.salario_real), # Exemplo
            'fgts_base': float(folha.salario_real), # Exemplo
            'fgts_mes': float(folha.salario_real) * 0.08
        }
    }

    # 3. Gerar o Arquivo
    output = io.BytesIO()
    service = HoleriteExcelService(output)
    service.gerar_recibo(dados_holerite)
    service.close()
    
    output.seek(0)
    
    # 4. Retornar HTTP Response
    filename = f"Holerite_{funcionario.nome}_{folha.data_referencia.strftime('%m-%Y')}.xlsx"
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response




@login_required
def exportar_consolidado_anual(request):
    try:
        # CORREÇÃO: Usar datetime.now().year em vez de datetime.datetime.now().year
        ano = int(request.GET.get('ano', datetime.now().year))
    except ValueError:
        # CORREÇÃO AQUI TAMBÉM
        ano = datetime.now().year

    service = RelatorioAnualConsolidado(ano)
    excel_file = service.gerar()

    filename = f"Consolidado_Despesas_{ano}.xlsx"
    response = HttpResponse(
        excel_file,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def exportar_fluxo_caixa(request):
    """
    Gera o Fluxo de Caixa padrão de 7 dias a partir de hoje.
    """
    dt_inicio = date.today()
    num_dias = 7
    periodo_nome = "Próximos 7 Dias"

    try:
        buffer = RelatorioFluxoCaixaExport.gerar_excel(dt_inicio, num_dias, periodo_nome)
        filename = f"Fluxo_Caixa_7dias_{dt_inicio.strftime('%d%m')}.xlsx"
        return FileResponse(buffer, as_attachment=True, filename=filename)
    except Exception as e:
        return HttpResponse(f"Erro ao gerar fluxo de caixa: {str(e)}", status=500)
    

@login_required
def folha_exportar_decimo(request):
    from apps.relatorios.services.follha_pagamento import \
        FuncionarioFolhaExcelService

    # Pega o mês/ano da URL ou usa o atual
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    data_ref = date(ano, mes, 1)
    
    # Busca apenas pagamentos que tenham valor de 13º
    pagamentos = FolhaPagamento.objects.filter(
        data_referencia=data_ref,
        decimo_terceiro__gt=0
    ).select_related('funcionario', 'funcionario__dados_trabalhistas').order_by('funcionario__nome')
    
    if not pagamentos.exists():
        messages.warning(request, "Nenhum valor de 13º encontrado para este mês.")
        return redirect(f"{request.META.get('HTTP_REFERER')}?mes={mes}&ano={ano}")

    # Chama o serviço para gerar o Excel
    excel_file = FuncionarioFolhaExcelService.gerar_relatorio_decimo(pagamentos)
    
    # Prepara o download
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=DecimoTerceiro_{mes}_{ano}.xlsx'
    return response