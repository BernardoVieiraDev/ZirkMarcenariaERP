import io
import xlsxwriter
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from django.db.models.functions import ExtractMonth

class ReceberExcelService:
    # Cores
    COR_PRIMARIA_AZUL = '#004F9F'   
    COR_HEADER_TABELA = '#F3F4F6'   
    COR_FUNDO_SECAO = '#E2E8F0'     
    COR_TEXTO_PRETO = '#1F2937'     
    COR_BORDA = '#D1D5DB'           

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        border_style = {'border': 1, 'border_color': cls.COR_BORDA}
        
        return {
            'main_title': workbook.add_format({
                'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
                'font_name': 'Calibri'
            }),
            'section_title': workbook.add_format({
                'bold': True, 'font_size': 14, 'align': 'left', 'valign': 'vcenter',
                'font_name': 'Calibri', 'color': cls.COR_PRIMARIA_AZUL,
                'bottom': 2, 'bottom_color': cls.COR_PRIMARIA_AZUL # Linha azul embaixo
            }),
            'summary_header': workbook.add_format({
                'bold': True, 'font_size': 11, 'align': 'left', 'valign': 'vcenter',
                'fg_color': cls.COR_HEADER_TABELA, 'font_color': cls.COR_TEXTO_PRETO,
                'font_name': 'Calibri', 'indent': 1, **border_style
            }),
            'summary_text': workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'font_name': 'Calibri', 
                'font_size': 11, 'indent': 1, **border_style
            }),
            'summary_money': workbook.add_format({
                'align': 'right', 'valign': 'vcenter', 'font_name': 'Calibri', 
                'font_size': 11, 'num_format': 'R$ #,##0.00', **border_style, 'bold': True
            }),
            # --- Formatos existentes ---
            'title_month': workbook.add_format({
                'bold': True, 'font_size': 16, 'align': 'left', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
                'font_name': 'Calibri', 'indent': 1
            }),
            'header_table': workbook.add_format({
                'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_HEADER_TABELA, 'font_color': cls.COR_TEXTO_PRETO,
                'font_name': 'Calibri', **border_style
            }),
            'data_text': workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'font_name': 'Calibri', 
                'font_size': 10, 'indent': 1, **border_style
            }),
            'data_date': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'font_name': 'Calibri', 
                'font_size': 10, 'num_format': 'dd/mm/yyyy', **border_style
            }),
            'data_money': workbook.add_format({
                'align': 'right', 'valign': 'vcenter', 'font_name': 'Calibri', 
                'font_size': 10, 'num_format': 'R$ #,##0.00', 'right': 1, **border_style
            }),
            'total_label': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter',
                'font_name': 'Calibri', 'font_size': 11, 'bg_color': cls.COR_FUNDO_SECAO,
                'font_color': cls.COR_TEXTO_PRETO, **border_style
            }),
            'total_money': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter', 
                'font_name': 'Calibri', 'font_size': 11, 'bg_color': cls.COR_FUNDO_SECAO,
                'font_color': cls.COR_TEXTO_PRETO, 'num_format': 'R$ #,##0.00', **border_style
            })
        }

    @staticmethod
    def gerar_relatorio_receber(dados_queryset, workbook=None):
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True

        try:
            ws = workbook.add_worksheet("Contas a Receber")
            fmt = ReceberExcelService._define_formats(workbook)

            # --- 1. Espaçamento de Colunas ---
            ws.set_column('A:A', 25) 
            ws.set_column('B:B', 18) 
            ws.set_column('C:C', 35) 
            ws.set_column('D:D', 25) 
            ws.set_column('E:E', 20) 
            ws.set_column('F:F', 20) 
            ws.set_column('G:G', 40) 
            ws.set_column('H:H', 25) 

            row = 0

            # --- 2. Título Principal ---
            ws.set_row(row, 40)
            ws.merge_range(row, 0, row, 7, "RELATÓRIO DE CONTAS A RECEBER 2025", fmt['main_title'])
            row += 2

            # ==============================================================================
            # NOVA FUNCIONALIDADE: RESUMO POR CATEGORIA (Substitui o SUMIF do Excel)
            # ==============================================================================
            
            # Passo A: Calcular os totais agrupados por categoria
            resumo_categorias = {}
            total_geral_resumo = Decimal('0.00')
            
            for item in dados_queryset:
                # Pega a categoria ou define como 'Sem Categoria' se estiver vazio
                cat_nome = item.categoria if item.categoria else "Outros"
                valor = item.valor if item.valor else Decimal('0.00')
                
                if cat_nome in resumo_categorias:
                    resumo_categorias[cat_nome] += valor
                else:
                    resumo_categorias[cat_nome] = valor
                
                total_geral_resumo += valor

            # Passo B: Desenhar a Tabela de Resumo no Excel
            ws.write(row, 0, "Resumo por Categoria", fmt['section_title'])
            row += 2

            # Cabeçalho da tabelinha de resumo
            ws.write(row, 0, "Categoria", fmt['summary_header'])
            ws.write(row, 1, "Total Recebido", fmt['summary_header'])
            row += 1

            # Linhas da tabelinha
            for cat, total in resumo_categorias.items():
                ws.write(row, 0, cat, fmt['summary_text'])
                ws.write(row, 1, total, fmt['summary_money'])
                row += 1
            
            # Total Geral do Resumo
            ws.write(row, 0, "TOTAL GERAL", fmt['total_label'])
            ws.write(row, 1, total_geral_resumo, fmt['total_money'])
            
            row += 4 # Espaço generoso antes de começar os meses

            # ==============================================================================
            # LISTAGEM MENSAL (Código Original Ajustado)
            # ==============================================================================

            headers = [
                "Forma de recebimento", "Data vencimento", "Cliente", "Categoria",
                "Valor a receber", "Valor em estoque", "Observações", "Data do pagamento"
            ]

            meses = [
                (1, 'JANEIRO'), (2, 'FEVEREIRO'), (3, 'MARÇO'), (4, 'ABRIL'),
                (5, 'MAIO'), (6, 'JUNHO'), (7, 'JULHO'), (8, 'AGOSTO'),
                (9, 'SETEMBRO'), (10, 'OUTUBRO'), (11, 'NOVEMBRO'), (12, 'DEZEMBRO')
            ]

            for mes_num, mes_nome in meses:
                itens_mes = [
                    d for d in dados_queryset 
                    if d.data_vencimento and d.data_vencimento.month == mes_num
                ]

                ws.set_row(row, 35) 
                ws.merge_range(row, 0, row, 7, mes_nome, fmt['title_month'])
                row += 1

                ws.set_row(row, 30) 
                for col_num, header in enumerate(headers):
                    ws.write(row, col_num, header, fmt['header_table'])
                row += 1

                if not itens_mes:
                    ws.set_row(row, 25)
                    ws.merge_range(row, 0, row, 7, "-", fmt['data_text'])
                    row += 3 
                    continue

                total_valor = Decimal('0.00')
                total_estoque = Decimal('0.00')

                for item in itens_mes:
                    ws.set_row(row, 25) 
                    
                    valor = item.valor if item.valor else Decimal('0.00')
                    estoque = item.valor_estoque if item.valor_estoque else Decimal('0.00')
                    
                    ws.write(row, 0, item.forma_de_recebimento or '-', fmt['data_text'])
                    ws.write(row, 1, item.data_vencimento, fmt['data_date'])
                    ws.write(row, 2, item.cliente or '-', fmt['data_text'])
                    ws.write(row, 3, item.categoria or '-', fmt['data_text'])
                    ws.write(row, 4, valor, fmt['data_money'])
                    ws.write(row, 5, estoque, fmt['data_money'])
                    ws.write(row, 6, item.observacoes or '', fmt['data_text'])
                    
                    if item.data_pagamento:
                        ws.write(row, 7, item.data_pagamento, fmt['data_date'])
                    else:
                        ws.write(row, 7, '-', fmt['data_text'])

                    total_valor += valor
                    total_estoque += estoque
                    row += 1

                ws.set_row(row, 30) 
                ws.merge_range(row, 0, row, 3, "TOTAL " + mes_nome + ":", fmt['total_label'])
                ws.write(row, 4, total_valor, fmt['total_money'])
                ws.write(row, 5, total_estoque, fmt['total_money'])
                ws.write(row, 6, "", fmt['total_label'])
                ws.write(row, 7, "", fmt['total_label'])

                row += 2 

        except Exception as e:
            print(f"❌ Erro ao gerar relatório receber: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output