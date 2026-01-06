import io
import xlsxwriter
from datetime import datetime
from django.db.models import Sum
from .models import LancamentoSocio, CategoriaSocio, Socio

class SocioExcelService:
    @staticmethod
    def gerar_planilha_anual(ano=None, socio_id=None, workbook=None):
        if not ano:
            ano = datetime.now().year

        titulo_planilha = f"RELATÓRIO FINANCEIRO - {ano}"
        nome_socio = "GERAL"
        if socio_id:
            try:
                socio_obj = Socio.objects.get(id=socio_id)
                nome_socio = socio_obj.nome.upper()
                titulo_planilha = f"RELATÓRIO FINANCEIRO - {nome_socio} - {ano}"
            except Socio.DoesNotExist:
                pass

        output = None
        should_close = False
        
        # Se não passar workbook, cria um novo em memória
        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
            
        # --- Cores e Formatação ---
        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 16, 'font_color': '#1F4E78',
            'align': 'center', 'valign': 'vcenter'
        })
        fmt_header = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#1F4E78', 'font_color': '#FFFFFF',
            'border': 1, 'border_color': '#AAAAAA'
        })
        fmt_group = workbook.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 
            'font_color': '#000000', 'align': 'left', 'indent': 1
        })
        fmt_group_total = workbook.add_format({
            'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
            'num_format': 'R$ #,##0.00'
        })
        fmt_group_total_label = workbook.add_format({
            'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
            'align': 'right'
        })
        fmt_text = workbook.add_format({'border': 1, 'border_color': '#DDDDDD'})
        fmt_money = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'border_color': '#DDDDDD'})
        fmt_money_bold = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1, 'bold': True})
        
        fmt_resumo_header = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1, 'align': 'center'})
        fmt_resumo_entrada = workbook.add_format({'bold': True, 'font_color': '#385723', 'bg_color': '#E2EFDA', 'border': 1, 'num_format': 'R$ #,##0.00'})
        fmt_resumo_saida = workbook.add_format({'bold': True, 'font_color': '#C00000', 'bg_color': '#FCE4D6', 'border': 1, 'num_format': 'R$ #,##0.00'})
        fmt_resumo_saldo_pos = workbook.add_format({'bold': True, 'font_color': '#0000FF', 'bg_color': '#D9E1F2', 'border': 1, 'num_format': 'R$ #,##0.00'})
        fmt_resumo_saldo_neg = workbook.add_format({'bold': True, 'font_color': '#FF0000', 'bg_color': '#FFFF00', 'border': 1, 'num_format': 'R$ #,##0.00'})
        fmt_total_row = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})

        # --- CORREÇÃO APLICADA AQUI ---
        worksheet = workbook.add_worksheet("Sócios") 
        
        colunas = ["Categoria", "Média Mensal"] + [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"
        ] + ["Total Anual"]

        worksheet.merge_range('A1:O1', titulo_planilha, fmt_title)
        
        for idx, col in enumerate(colunas):
            worksheet.write(2, idx, col, fmt_header)

        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:N', 13)
        worksheet.set_column('O:O', 16)

        # --- 1. Buscar Dados ---
        qs = LancamentoSocio.objects.filter(data__year=ano)
        if socio_id:
            qs = qs.filter(socio_id=socio_id)

        dados_raw = qs.values('categoria', 'data__month').annotate(total=Sum('valor'))
        
        dados_map = {}
        for d in dados_raw:
            dados_map[(d['categoria'], d['data__month'])] = d['total']

        GRUPOS_ORDEM = [
            'RENDA_FAMILIAR', 'HABITACAO', 'SAUDE', 'TRANSPORTE',
            'AUTOMOVEL', 'DESPESAS_PESSOAIS', 'LAZER', 'DEPENDENTES'
        ]

        row = 3
        total_rendimentos_anual = 0
        total_gastos_anual = 0
        
        # --- 2. Iterar Grupos ---
        for grupo_key in GRUPOS_ORDEM:
            categorias = CategoriaSocio.objects.filter(grupo=grupo_key).order_by('id')
            if not categorias.exists():
                continue

            label_grupo = categorias.first().get_grupo_display().upper()
            worksheet.merge_range(row, 0, row, 14, f"  {label_grupo}", fmt_group)
            row += 1

            subtotal_grupo_meses = {m: 0 for m in range(1, 13)}
            subtotal_grupo_total = 0

            for cat in categorias:
                worksheet.write(row, 0, f"  {cat.nome}", fmt_text)
                
                soma_linha = 0
                for mes in range(1, 13):
                    val = dados_map.get((cat.id, mes), 0)
                    worksheet.write(row, mes + 1, val if val > 0 else "-", fmt_money)
                    soma_linha += val
                    subtotal_grupo_meses[mes] += val

                media = soma_linha / 12 if soma_linha > 0 else 0
                worksheet.write(row, 1, media, fmt_money)
                worksheet.write(row, 14, soma_linha, fmt_money_bold)
                
                subtotal_grupo_total += soma_linha
                row += 1

            worksheet.write(row, 0, f"TOTAL {label_grupo}", fmt_group_total_label)
            media_grupo = subtotal_grupo_total / 12 if subtotal_grupo_total > 0 else 0
            worksheet.write(row, 1, media_grupo, fmt_group_total)

            for mes in range(1, 13):
                worksheet.write(row, mes + 1, subtotal_grupo_meses[mes], fmt_group_total)
            
            worksheet.write(row, 14, subtotal_grupo_total, fmt_group_total)
            row += 2

            if grupo_key == 'RENDA_FAMILIAR':
                total_rendimentos_anual += subtotal_grupo_total
            else:
                total_gastos_anual += subtotal_grupo_total

        # --- 3. Resumo Financeiro Destacado ---
        row += 1
        worksheet.merge_range(row, 0, row, 2, "RESUMO FINANCEIRO ANUAL", fmt_resumo_header)
        row += 1

        worksheet.write(row, 0, " (+) Total Rendimentos", fmt_text)
        worksheet.merge_range(row, 1, row, 2, total_rendimentos_anual, fmt_resumo_entrada)
        row += 1

        worksheet.write(row, 0, " (-) Total Gastos", fmt_text)
        worksheet.merge_range(row, 1, row, 2, total_gastos_anual, fmt_resumo_saida)
        row += 1

        saldo = total_rendimentos_anual - total_gastos_anual
        style_saldo = fmt_resumo_saldo_pos if saldo >= 0 else fmt_resumo_saldo_neg
        
        worksheet.write(row, 0, " (=) SALDO FINAL", fmt_total_row) 
        worksheet.merge_range(row, 1, row, 2, saldo, style_saldo)

        # --- CORREÇÃO CRÍTICA NA FINALIZAÇÃO ---
        # Só fecha e retorna o output se este método CRIOU o workbook.
        # Se recebeu de fora (Shared Workbook), deixa aberto para os outros relatórios.
        if should_close:
            workbook.close()
            output.seek(0)
            return output
        
        return None