import io
import xlsxwriter
from decimal import Decimal
from datetime import datetime

class ReceberExcelService:
    # ... (manter as constantes de cores e método _define_formats iguais) ...
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
        # ... (manter implementação original do _define_formats) ...
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

        # Define o ano atual se não for informado
        if ano is None:
            ano = datetime.now().year

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True

        try:
            # CORREÇÃO PRINCIPAL: 
            # 1. Converter QuerySet para lista para permitir múltiplas iterações
            # 2. Filtrar pelo ano selecionado para garantir integridade do relatório (evita misturar jan/2024 com jan/2025)
            dados_lista = [
                item for item in dados_queryset 
                if item.data_vencimento and item.data_vencimento.year == ano
            ]

            ws = workbook.add_worksheet("Contas a Receber")
            ws.hide_gridlines(2) # Visual limpo
            
            fmt = ReceberExcelService._define_formats(workbook)

            # --- 1. Espaçamento de Colunas ---
            ws.set_column('A:A', 25) # Forma/Categoria# type: ignore
            ws.set_column('B:B', 15) # Data# type: ignore
            ws.set_column('C:C', 30) # Cliente# type: ignore
            ws.set_column('D:D', 20) # Categoria# type: ignore
            ws.set_column('E:E', 18) # Valor Receber# type: ignore
            ws.set_column('F:F', 18) # Valor Estoque# type: ignore
            ws.set_column('G:G', 35) # Obs# type: ignore
            ws.set_column('H:H', 18) # Data Pagto# type: ignore

            row = 1

            # --- 2. Título Principal (AGORA DINÂMICO) ---
            ws.set_row(row, 35)
            # Usa o ano definido na variável
            ws.merge_range(row, 0, row, 7, f"RELATÓRIO DE CONTAS A RECEBER {ano}", fmt['main_title'])
            
            # Barra Sólida Abaixo do Título
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

            # Cabeçalho da tabela de resumo
            ws.write(row, 0, "Categoria", fmt['header_table_left'])
            ws.write(row, 1, "Total Recebido", fmt['header_table'])
            row += 1

            # Linhas de resumo
            for cat, total in resumo_categorias.items():
                ws.write(row, 0, cat, fmt['summary_text'])
                ws.write(row, 1, total, fmt['summary_money'])
                row += 1
            
            # Total Geral Resumo
            ws.write(row, 0, "TOTAL GERAL", fmt['total_label'])
            ws.write(row, 1, total_geral_resumo, fmt['total_money'])
            
            row += 4 

            # ==============================================================================
            # LISTAGEM MENSAL
            # ==============================================================================

            headers = [
                "Forma de recebimento", "Data vencimento", "Cliente", "Categoria",
                "Valor a receber", "Valor em estoque", "Observações", "Data do recebimento"
            ]

            meses = [
                (1, 'JANEIRO'), (2, 'FEVEREIRO'), (3, 'MARÇO'), (4, 'ABRIL'),
                (5, 'MAIO'), (6, 'JUNHO'), (7, 'JULHO'), (8, 'AGOSTO'),
                (9, 'SETEMBRO'), (10, 'OUTUBRO'), (11, 'NOVEMBRO'), (12, 'DEZEMBRO')
            ]

            for mes_num, mes_nome in meses:
                # Loop filtrando a lista já processada
                itens_mes = [
                    d for d in dados_lista 
                    if d.data_vencimento and d.data_vencimento.month == mes_num
                ]

                # Título do Mês
                ws.set_row(row, 35) 
                ws.merge_range(row, 0, row, 7, mes_nome, fmt['month_title'])
                row += 1

                # Cabeçalhos da Tabela
                ws.set_row(row, 25) 
                for col_num, header in enumerate(headers):
                    ws.write(row, col_num, header, fmt['header_table'])
                row += 1

                if not itens_mes:
                    ws.set_row(row, 20)
                    ws.merge_range(row, 0, row, 7, "- Sem lançamentos neste mês -", fmt['data_text'])
                    row += 2 
                    continue

                total_valor = Decimal('0.00')
                total_estoque = Decimal('0.00')

                for item in itens_mes:
                    ws.set_row(row, 20) 
                    
                    valor = item.valor if item.valor else Decimal('0.00')
                    estoque = Decimal('0.00')
                    
                    ws.write(row, 0, item.forma_recebimento or '-', fmt['data_text'])
                    ws.write(row, 1, item.data_vencimento, fmt['data_date'])
                    ws.write(row, 2, item.cliente or '-', fmt['data_text'])
                    ws.write(row, 3, item.categoria or '-', fmt['data_text'])
                    ws.write(row, 4, valor, fmt['data_money'])
                    ws.write(row, 5, estoque, fmt['data_money'])
                    ws.write(row, 6, item.observacoes or '', fmt['data_text'])
                    
                    if item.data_recebimento:
                        ws.write(row, 7, item.data_recebimento, fmt['data_date'])
                    else:
                        ws.write(row, 7, '-', fmt['data_text'])

                    total_valor += valor
                    total_estoque += estoque
                    row += 1

                # Totais do Mês
                ws.set_row(row, 25) 
                ws.merge_range(row, 0, row, 3, f"TOTAL {mes_nome}", fmt['total_label'])
                ws.write(row, 4, total_valor, fmt['total_money'])
                ws.write(row, 5, total_estoque, fmt['total_money'])
                ws.write(row, 6, "", fmt['total_label'])
                ws.write(row, 7, "", fmt['total_label'])

                row += 4 

            # Rodapé final
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