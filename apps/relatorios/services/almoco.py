import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class GastoAlmocoExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Formatos padrão para manter a identidade visual dos relatórios."""
        return {
            'title': workbook.add_format({
                'bold': True, 
                'font_size': 14, 
                'align': 'center', 
                'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 
                'font_color': '#FFFFFF',
                'font_name': 'Calibri'
            }),
            'header_table': workbook.add_format({
                'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
                'font_name': 'Calibri', 'border': 1
            }),
            'data_text': workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10
            }),
            'data_center': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10
            }),
            'data_date': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': 'dd/mm/yyyy'
            }),
            'data_money': workbook.add_format({
                'align': 'right', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': 'R$ #,##0.00'
            }),
            'total_label': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter',
                'font_name': 'Calibri', 'font_size': 11, 'bg_color': cls.COR_FUNDO_SECAO,
                'border': 1
            }),
            'total_money': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter',
                'font_name': 'Calibri', 'font_size': 11, 'bg_color': cls.COR_FUNDO_SECAO,
                'num_format': 'R$ #,##0.00', 'border': 1
            })
        }

    @staticmethod
    def gerar_relatorio_almoco(gastos, workbook=None):
        """
        Gera relatório específico de Gastos com Almoço.
        Pode ser usado individualmente ou recebendo um workbook pai (ex: Relatório Anual).
        """
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("Gastos com Almoço")
            fmt = GastoAlmocoExcelService._define_formats(workbook)

            # Cabeçalhos baseados nos campos do model GastoAlmoco
            headers = [
                "Data", 
                "Funcionário", 
                "Descrição", 
                "Observações", 
                "Origem Pagamento", 
                "Forma Pagamento",
                "Valor (R$)"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 12)  # Data
            ws.set_column('B:B', 30)  # Funcionário
            ws.set_column('C:C', 25)  # Descrição
            ws.set_column('D:D', 30)  # Observações
            ws.set_column('E:E', 18)  # Origem
            ws.set_column('F:F', 18)  # Forma Pag.
            ws.set_column('G:G', 15)  # Valor

            row = 0

            # --- TÍTULO ---
            ws.set_row(row, 25)
            # Mescla da coluna 0 (A) até a 6 (G)
            ws.merge_range(row, 0, row, 6, "RELATÓRIO DE GASTOS COM ALMOÇO", fmt['title'])
            row += 2 

            # Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            total_valor = Decimal('0.00')

            if gastos:
                for item in gastos:
                    # 1. Dados Básicos
                    dt_gasto = getattr(item, 'data_gasto', None)
                    valor = getattr(item, 'valor_total', Decimal('0.00')) or Decimal('0.00')
                    
                    # 2. Funcionário (Tratamento seguro)
                    func_obj = getattr(item, 'funcionario', None)
                    nome_func = getattr(func_obj, 'nome', str(func_obj)) if func_obj else 'Não Identificado'

                    # 3. Descrição e Observações
                    descricao = getattr(item, 'descricao', '') or ''
                    observacoes = getattr(item, 'observacoes', '') or ''

                    # 4. Choices (Origem e Forma)
                    # Tenta pegar o display (ex: 'Banco'), se não der, pega o raw (ex: 'BANCO')
                    origem = item.get_origem_pagamento_display() if hasattr(item, 'get_origem_pagamento_display') else getattr(item, 'origem_pagamento', '')
                    forma = item.get_forma_pagamento_display() if hasattr(item, 'get_forma_pagamento_display') else getattr(item, 'forma_pagamento', '')

                    # --- ESCRITA NA PLANILHA ---
                    
                    # Coluna A: Data
                    if dt_gasto:
                        ws.write(row, 0, dt_gasto, fmt['data_date'])
                    else:
                        ws.write(row, 0, '-', fmt['data_center'])

                    # Coluna B: Funcionário
                    ws.write(row, 1, nome_func, fmt['data_text'])
                    
                    # Coluna C: Descrição
                    ws.write(row, 2, descricao, fmt['data_text'])
                    
                    # Coluna D: Observações
                    ws.write(row, 3, observacoes, fmt['data_text'])
                    
                    # Coluna E: Origem
                    ws.write(row, 4, origem, fmt['data_center'])
                    
                    # Coluna F: Forma Pagamento
                    ws.write(row, 5, forma, fmt['data_center'])

                    # Coluna G: Valor
                    ws.write(row, 6, valor, fmt['data_money'])

                    total_valor += valor
                    row += 1
            else:
                ws.merge_range(row, 0, row, 6, "Nenhum registro de almoço encontrado para o período.", fmt['data_center'])
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 5, "TOTAL GERAL:", fmt['total_label'])
            ws.write(row, 6, total_valor, fmt['total_money'])
            
            print(f"✅ Relatório de Almoço gerado com sucesso.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de almoço: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output