import io
import xlsxwriter
from decimal import Decimal
from datetime import datetime

class ReceberExcelService:
    # --- Paleta de Cores Profissional (Clean & Corporate) ---
    COR_TITULO_BG = '#2C3E50'
    COR_TITULO_TEXTO = '#FFFFFF'
    COR_HEADER_BG = '#34495E'
    COR_HEADER_TEXT = '#FFFFFF'
    COR_MES_BG = '#95A5A6'
    COR_MES_TEXT = '#FFFFFF'
    COR_TOTAL_BG = '#F4F6F7'
    COR_TOTAL_TEXT = '#2C3E50'
    COR_LINHA_DIVISORIA = '#BDC3C7'
    COR_LINHA_SUAVE = '#E0E0E0'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        font_base = {'font_name': 'Calibri', 'valign': 'vcenter', 'font_size': 10}
        bottom_line = {'bottom': 1, 'bottom_color': cls.COR_LINHA_SUAVE}
        
        return {
            'main_title': workbook.add_format({
                **font_base, 'bold': True, 'font_size': 18, 'align': 'center',
                'font_color': cls.COR_TITULO_TEXTO, 'bg_color': cls.COR_TITULO_BG,
                'top': 1, 'top_color': cls.COR_TITULO_BG,
                'left': 1, 'left_color': cls.COR_TITULO_BG,
                'right': 1, 'right_color': cls.COR_TITULO_BG,
            }),
            'main_title_bar': workbook.add_format({
                'bg_color': cls.COR_TITULO_BG,
                'bottom': 2, 'bottom_color': cls.COR_TITULO_BG,
                'left': 1, 'left_color': cls.COR_TITULO_BG,
                'right': 1, 'right_color': cls.COR_TITULO_BG,
            }),
            'section_title': workbook.add_format({
                **font_base, 'bold': True, 'font_size': 14, 'align': 'left',
                'font_color': cls.COR_TITULO_BG,
                'bottom': 1, 'bottom_color': cls.COR_LINHA_DIVISORIA
            }),
            'header_table': workbook.add_format({
                **font_base, 'bold': True, 'font_size': 11, 'align': 'center',
                'fg_color': cls.COR_HEADER_BG, 'font_color': cls.COR_HEADER_TEXT,
                'border': 1, 'border_color': cls.COR_HEADER_BG
            }),
            'header_table_left': workbook.add_format({
                **font_base, 'bold': True, 'font_size': 11, 'align': 'left', 'indent': 1,
                'fg_color': cls.COR_HEADER_BG, 'font_color': cls.COR_HEADER_TEXT,
                'border': 1, 'border_color': cls.COR_HEADER_BG
            }),
            'month_title': workbook.add_format({
                **font_base, 'bold': True, 'font_size': 16, 'align': 'left', 'indent': 1,
                'fg_color': cls.COR_MES_BG, 'font_color': cls.COR_MES_TEXT,
                'border': 1, 'border_color': cls.COR_MES_BG
            }),
            'data_text': workbook.add_format({
                **font_base, 'align': 'left', 'indent': 1, 
                'font_color': '#333333', **bottom_line
            }),
            'data_date': workbook.add_format({
                **font_base, 'align': 'center', 
                'num_format': 'dd/mm/yyyy', 'font_color': '#333333', **bottom_line
            }),
            'data_money': workbook.add_format({
                **font_base, 'align': 'right', 
                'num_format': '#,##0.00', 'font_color': '#333333', **bottom_line
            }),
            'total_label': workbook.add_format({
                **font_base, 'bold': True, 'align': 'right', 
                'bg_color': cls.COR_TOTAL_BG, 'font_color': cls.COR_TOTAL_TEXT,
                'top': 1, 'top_color': cls.COR_LINHA_DIVISORIA, 
                'bottom': 1, 'bottom_color': cls.COR_LINHA_DIVISORIA
            }),
            'total_money': workbook.add_format({
                **font_base, 'bold': True, 'align': 'right', 
                'num_format': 'R$ #,##0.00', 
                'bg_color': cls.COR_TOTAL_BG, 'font_color': cls.COR_TOTAL_TEXT,
                'top': 1, 'top_color': cls.COR_LINHA_DIVISORIA,
                'bottom': 1, 'bottom_color': cls.COR_LINHA_DIVISORIA
            }),
            'summary_text': workbook.add_format({
                **font_base, 'align': 'left', 'indent': 1, 
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            'summary_money': workbook.add_format({
                **font_base, 'align': 'right', 'bold': True,
                'num_format': 'R$ #,##0.00', 
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
        }

    @staticmethod
    def gerar_relatorio_receber(dados_queryset, workbook=None, ano=None):
        output = None
        should_close = False

        if ano is None:
            ano = datetime.now().year

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True

        try:
            dados_lista = [
                item for item in dados_queryset 
                if item.data_vencimento and item.data_vencimento.year == ano
            ]

            ws = workbook.add_worksheet("Contas a Receber")
            ws.hide_gridlines(2)
            
            fmt = ReceberExcelService._define_formats(workbook)

            # --- 1. Espaçamento de Colunas ---
            ws.set_column('A:A', 25) # Forma/Categoria
            ws.set_column('B:B', 15) # Data
            ws.set_column('C:C', 30) # Cliente
            ws.set_column('D:D', 20) # Categoria
            ws.set_column('E:E', 18) # Valor Receber
            ws.set_column('F:F', 18) # Valor Recebido (Alterado)
            ws.set_column('G:G', 35) # Obs
            ws.set_column('H:H', 18) # Data Pagto

            row = 1

            # --- 2. Título Principal ---
            ws.set_row(row, 35)
            ws.merge_range(row, 0, row, 7, f"RELATÓRIO DE CONTAS A RECEBER {ano}", fmt['main_title'])
            
            ws.set_row(row + 1, 5) 
            ws.merge_range(row + 1, 0, row + 1, 7, "", fmt['main_title_bar'])
            row += 3

            # ==============================================================================
            # RESUMO POR CATEGORIA
            # ==============================================================================
            
            resumo_categorias = {}
            total_geral_resumo = Decimal('0.00')
            
            for item in dados_lista:
                cat_nome = item.categoria if item.categoria else "Outros"
                valor = item.valor if item.valor else Decimal('0.00')
                
                if cat_nome in resumo_categorias:
                    resumo_categorias[cat_nome] += valor
                else:
                    resumo_categorias[cat_nome] = valor
                
                total_geral_resumo += valor

            ws.write(row, 0, "Resumo Financeiro por Categoria", fmt['section_title'])
            row += 2

            ws.write(row, 0, "Categoria", fmt['header_table_left'])
            ws.write(row, 1, "Total Previsto", fmt['header_table']) # Ajustado label para coerência
            row += 1

            for cat, total in resumo_categorias.items():
                ws.write(row, 0, cat, fmt['summary_text'])
                ws.write(row, 1, total, fmt['summary_money'])
                row += 1
            
            ws.write(row, 0, "TOTAL GERAL PREVISTO", fmt['total_label'])
            ws.write(row, 1, total_geral_resumo, fmt['total_money'])
            
            row += 4 

            # ==============================================================================
            # LISTAGEM MENSAL
            # ==============================================================================

            # ALTERAÇÃO 1: Nome do cabeçalho atualizado
            headers = [
                "Forma de recebimento", "Data vencimento", "Cliente", "Categoria",
                "Valor a receber", "Valor recebido", "Observações", "Data do recebimento"
            ]

            meses = [
                (1, 'JANEIRO'), (2, 'FEVEREIRO'), (3, 'MARÇO'), (4, 'ABRIL'),
                (5, 'MAIO'), (6, 'JUNHO'), (7, 'JULHO'), (8, 'AGOSTO'),
                (9, 'SETEMBRO'), (10, 'OUTUBRO'), (11, 'NOVEMBRO'), (12, 'DEZEMBRO')
            ]

            for mes_num, mes_nome in meses:
                itens_mes = [
                    d for d in dados_lista 
                    if d.data_vencimento and d.data_vencimento.month == mes_num
                ]

                ws.set_row(row, 35) 
                ws.merge_range(row, 0, row, 7, mes_nome, fmt['month_title'])
                row += 1

                ws.set_row(row, 25) 
                for col_num, header in enumerate(headers):
                    ws.write(row, col_num, header, fmt['header_table'])
                row += 1

                if not itens_mes:
                    ws.set_row(row, 20)
                    ws.merge_range(row, 0, row, 7, "- Sem lançamentos neste mês -", fmt['data_text'])
                    row += 2 
                    continue

                total_valor_previsto = Decimal('0.00')
                total_valor_recebido = Decimal('0.00') # ALTERAÇÃO 2: Variável para acumular recebido

                for item in itens_mes:
                    ws.set_row(row, 20) 
                    
                    valor = item.valor if item.valor else Decimal('0.00')
                    # ALTERAÇÃO 3: Pega o valor recebido do objeto
                    recebido = item.valor_recebido if item.valor_recebido else Decimal('0.00')
                    
                    ws.write(row, 0, item.forma_recebimento or '-', fmt['data_text'])
                    ws.write(row, 1, item.data_vencimento, fmt['data_date'])
                    
                    # Correção do Cliente mantida
                    cliente_texto = item.cliente.nome_completo if item.cliente else '-'
                    ws.write(row, 2, cliente_texto, fmt['data_text'])
                    
                    ws.write(row, 3, item.categoria or '-', fmt['data_text'])
                    ws.write(row, 4, valor, fmt['data_money'])
                    
                    # ALTERAÇÃO 4: Escreve o valor recebido na coluna F (índice 5)
                    ws.write(row, 5, recebido, fmt['data_money'])
                    
                    ws.write(row, 6, item.observacoes or '', fmt['data_text'])
                    
                    if item.data_recebimento:
                        ws.write(row, 7, item.data_recebimento, fmt['data_date'])
                    else:
                        ws.write(row, 7, '-', fmt['data_text'])

                    total_valor_previsto += valor
                    total_valor_recebido += recebido
                    row += 1

                # Totais do Mês
                ws.set_row(row, 25) 
                ws.merge_range(row, 0, row, 3, f"TOTAL {mes_nome}", fmt['total_label'])
                ws.write(row, 4, total_valor_previsto, fmt['total_money'])
                # ALTERAÇÃO 5: Escreve o total recebido
                ws.write(row, 5, total_valor_recebido, fmt['total_money'])
                ws.write(row, 6, "", fmt['total_label'])
                ws.write(row, 7, "", fmt['total_label'])

                row += 4 

            ws.set_row(row, 5)
            border_top = workbook.add_format({'top': 1, 'top_color': '#BDC3C7'})
            for col in range(8):
                ws.write_blank(row, col, '', border_top)

        except Exception as e:
            print(f"❌ Erro ao gerar relatório receber: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output