import io
import xlsxwriter
from datetime import date
from apps.financeiro.fluxo.services import FluxoCaixaService


class RelatorioFluxoCaixaExport:
    # --- Paleta de Cores ---
    COR_TITLE_BG = '#1F2937'
    COR_TITLE_TEXT = '#FFFFFF'

    COR_HEADER_BG = '#374151'
    COR_HEADER_TEXT = '#FFFFFF'

    COR_SECTION_ENTRADA = '#059669'
    COR_SECTION_SAIDA = '#DC2626'
    COR_SECTION_TEXT = '#FFFFFF'

    COR_ZEBRA_1 = '#FFFFFF'
    COR_TOTAL_BG = '#E5E7EB'
    COR_BORDER = '#D1D5DB'

    COR_SALDO_POS = '#059669'
    COR_SALDO_NEG = '#DC2626'

    # 🔒 Mapeamento seguro dos dias da semana (SEM locale)
    DIAS_SEMANA = {
        0: 'SEG',
        1: 'TER',
        2: 'QUA',
        3: 'QUI',
        4: 'SEX',
        5: 'SÁB',
        6: 'DOM',
    }

    @classmethod
    def gerar_excel(cls, data_inicio, num_dias, periodo_nome="Semanal", workbook=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet("Fluxo de Caixa")

        # Configuração Visual
        ws.hide_gridlines(2)
        ws.set_zoom(90)

        font_name = 'Segoe UI'

        # --- FORMATOS ---
        fmt_main_title = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 16,
            'align': 'left', 'valign': 'vcenter',
            'bg_color': cls.COR_TITLE_BG, 'font_color': cls.COR_TITLE_TEXT,
            'border': 1
        })

        fmt_date_header = workbook.add_format({
            'bold': True, 'font_name': font_name, 'font_size': 10,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': cls.COR_HEADER_BG, 'font_color': cls.COR_HEADER_TEXT,
            'border': 1, 'border_color': cls.COR_BORDER
        })

        fmt_label_category = workbook.add_format({
            'font_name': font_name, 'font_size': 10,
            'align': 'left', 'indent': 1, 'valign': 'vcenter',
            'border': 1, 'border_color': cls.COR_BORDER,
            'bg_color': cls.COR_ZEBRA_1
        })

        fmt_money = workbook.add_format({
            'num_format': '_-R$ * #,##0.00_-;-R$ * #,##0.00_-;_-R$ * "-"??_-;_-@_-',
            'font_name': font_name, 'font_size': 10,
            'border': 1, 'border_color': cls.COR_BORDER,
            'bg_color': cls.COR_ZEBRA_1
        })

        fmt_total_row_label = workbook.add_format({
            'bold': True, 'font_name': font_name,
            'bg_color': cls.COR_TOTAL_BG,
            'align': 'right',
            'top': 1, 'bottom': 1,
            'border_color': '#9CA3AF'
        })

        fmt_total_row_val = workbook.add_format({
            'bold': True, 'font_name': font_name,
            'bg_color': cls.COR_TOTAL_BG,
            'num_format': 'R$ #,##0.00',
            'top': 1, 'bottom': 1,
            'border_color': '#9CA3AF'
        })

        def get_section_fmt(bg_color):
            return workbook.add_format({
                'bold': True,
                'font_name': font_name,
                'font_size': 11,
                'bg_color': bg_color,
                'font_color': cls.COR_SECTION_TEXT,
                'align': 'left',
                'indent': 1,
                'valign': 'vcenter'
            })

        fmt_section_entradas = get_section_fmt(cls.COR_SECTION_ENTRADA)
        fmt_section_saidas = get_section_fmt(cls.COR_SECTION_SAIDA)
        fmt_section_conclusao = get_section_fmt(cls.COR_TITLE_BG)

        fmt_saldo_pos = workbook.add_format({
            'bold': True,
            'font_color': cls.COR_SALDO_POS,
            'bg_color': '#ECFDF5',
            'num_format': 'R$ #,##0.00',
            'border': 1,
            'border_color': cls.COR_BORDER
        })

        fmt_saldo_neg = workbook.add_format({
            'bold': True,
            'font_color': cls.COR_SALDO_NEG,
            'bg_color': '#FEF2F2',
            'num_format': 'R$ #,##0.00',
            'border': 1,
            'border_color': cls.COR_BORDER
        })

        # --- DADOS ---
        dias, timeline = FluxoCaixaService.gerar_fluxo_detalhado(data_inicio, num_dias)

        # --- LAYOUT ---
        ws.set_column('A:A', 40) # type: ignore
        ws.set_column(1, len(dias), 16)
        row = 1

        # Título
        ws.merge_range(row, 0, row + 1, len(dias),
                       f"  FLUXO DE CAIXA - {periodo_nome.upper()}",
                       fmt_main_title)
        row += 3

        # Cabeçalho Datas
        ws.write(row, 0, "", fmt_date_header)
        for idx, dia in enumerate(dias):
            dia_semana = cls.DIAS_SEMANA[dia.weekday()]
            ws.write(
                row,
                idx + 1,
                f"{dia.strftime('%d/%m')}\n{dia_semana}",
                fmt_date_header
            )

        ws.set_row(row, 30)
        row += 1

        def escrever_bloco(titulo_secao, fmt_secao, dados_dict, chaves_labels):
            nonlocal row
            ws.merge_range(row, 0, row, len(dias),
                           f" {titulo_secao.upper()}",
                           fmt_secao)
            row += 1

            for chave, label in chaves_labels:
                valores = dados_dict.get(chave, [])
                ws.write(row, 0, label, fmt_label_category)
                for idx, val in enumerate(valores):
                    ws.write(row, idx + 1, val, fmt_money)
                row += 1

            ws.write(row, 0,
                     f"TOTAL {titulo_secao.upper()}  ",
                     fmt_total_row_label)

            totais = dados_dict.get('total', [])
            for idx, val in enumerate(totais):
                ws.write(row, idx + 1, val, fmt_total_row_val)

            row += 2

        # Entradas
        escrever_bloco(
            "Entradas",
            fmt_section_entradas,
            timeline['entradas'],
            [
                ('vendas_vista', 'Vendas à vista (Caixa/Pix)'),
                ('recebimentos_debito', 'Recebimentos (Débito)'),
                ('recebimentos_credito', 'Recebimentos (Crédito)'),
                ('outras', 'Outras Entradas'),
            ]
        )

        # Saídas
        escrever_bloco(
            "Saídas",
            fmt_section_saidas,
            timeline['saidas'],
            [
                ('compras_vista', 'Compras à vista (Caixa)'),
                ('pagamentos_contas', 'Pagamentos (Contas a Pagar)'),
                ('outros_pagamentos', 'Outros Pagamentos'),
                ('outras_saidas', 'Outras Saídas'),
            ]
        )

        # Resumo
        ws.merge_range(row, 0, row, len(dias),
                       " RESUMO FINANCEIRO",
                       fmt_section_conclusao)
        row += 1

        ws.write(row, 0,
                 "Resultado do Dia (Entradas - Saídas)",
                 fmt_label_category)

        for idx, val in enumerate(timeline['conclusao']['resultado_dia']):
            fmt = fmt_saldo_neg if val < 0 else fmt_saldo_pos
            ws.write(row, idx + 1, val, fmt)

        row += 1

        ws.write(row, 0, "Saldo Anterior", fmt_label_category)
        for idx, val in enumerate(timeline['conclusao']['saldo_anterior']):
            ws.write(row, idx + 1, val, fmt_money)

        row += 2

        ws.write(row, 0,
                 "SALDO FINAL ACUMULADO  ",
                 fmt_total_row_label)

        for idx, val in enumerate(timeline['conclusao']['saldo_final']):
            ws.write(row, idx + 1, val, fmt_total_row_val)



        workbook.close()
        output.seek(0)
        return output
