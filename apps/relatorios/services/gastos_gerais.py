import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class GastoGeralExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Formatos padrão com TÍTULO."""
        return {
            'title': workbook.add_format({
                'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
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
    def gerar_relatorio_geral(gastos, gastos_almoco=None, workbook=None):
        """
        Gera relatório contendo:
        1. Tabela de Gastos Gerais
        2. Tabela de Gastos com Almoço (separada logo abaixo)
        """
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("Gastos Gerais e Almoço")
            fmt = GastoGeralExcelService._define_formats(workbook)

            # =================================================================
            # BLOCO 1: GASTOS GERAIS
            # =================================================================

            headers_gerais = [
                "Data", 
                "Descrição", 
                "Motorista", 
                "Veículo", 
                "Cliente", 
                "Forma Pag.", 
                "Valor Pix/Din (R$)", 
                "Valor Cartão (R$)", 
                "TOTAL (R$)"
            ]

            # Larguras das colunas
            ws.set_column('A:A', 12) 
            ws.set_column('B:B', 30) 
            ws.set_column('C:C', 25) 
            ws.set_column('D:D', 25) 
            ws.set_column('E:E', 20) 
            ws.set_column('F:F', 15) 
            ws.set_column('G:G', 15) 
            ws.set_column('H:H', 15) 
            ws.set_column('I:I', 15) 

            row = 0

            # Título Gastos Gerais
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 8, "RELATÓRIO DE GASTOS GERAIS (MATERIAL, ETC)", fmt['title'])
            row += 2 

            for col_num, header in enumerate(headers_gerais):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            total_pix = Decimal('0.00')
            total_cartao = Decimal('0.00')
            total_geral = Decimal('0.00')

            if gastos:
                for item in gastos:
                    dt_gasto = getattr(item, 'data_gasto', None)
                    desc = getattr(item, 'descricao', '') or ''
                    motorista = getattr(item, 'motorista', '') or ''
                    carro = getattr(item, 'carro', '') or ''
                    cliente = getattr(item, 'cliente', '') or ''
                    
                    # Lógica robusta para Forma de Pagamento (tenta display, depois atributo, depois campo secundário)
                    forma = ''
                    if hasattr(item, 'get_forma_principal_pagamento_display'):
                        forma = item.get_forma_principal_pagamento_display() or ''
                    
                    if not forma:
                         # Tenta o campo raw ou o campo alternativo 'forma_pagamento'
                         forma = getattr(item, 'forma_principal_pagamento', '') or \
                                 getattr(item, 'get_forma_pagamento_display', lambda: getattr(item, 'forma_pagamento', ''))()

                    v_pix = getattr(item, 'valor_dinheiro_pix', Decimal('0.00')) or Decimal('0.00')
                    v_cartao = getattr(item, 'valor_cartao', Decimal('0.00')) or Decimal('0.00')
                    v_total = getattr(item, 'valor_total', Decimal('0.00')) or Decimal('0.00')

                    if dt_gasto:
                        ws.write(row, 0, dt_gasto, fmt['data_date'])
                    else:
                        ws.write(row, 0, '-', fmt['data_center'])

                    ws.write(row, 1, desc, fmt['data_text'])
                    ws.write(row, 2, motorista, fmt['data_text'])
                    ws.write(row, 3, carro, fmt['data_text'])
                    ws.write(row, 4, cliente, fmt['data_text'])
                    ws.write(row, 5, forma, fmt['data_center'])
                    ws.write(row, 6, v_pix, fmt['data_money'])
                    ws.write(row, 7, v_cartao, fmt['data_money'])
                    ws.write(row, 8, v_total, fmt['data_money'])

                    total_pix += v_pix
                    total_cartao += v_cartao
                    total_geral += v_total
                    row += 1
            else:
                ws.write(row, 1, "Nenhum gasto geral no período.", fmt['data_text'])
                row += 1

            row += 1
            ws.merge_range(row, 0, row, 5, "TOTAIS GERAIS:", fmt['total_label'])
            ws.write(row, 6, total_pix, fmt['total_money'])
            ws.write(row, 7, total_cartao, fmt['total_money'])
            ws.write(row, 8, total_geral, fmt['total_money'])

            # =================================================================
            # BLOCO 2: GASTOS COM ALMOÇO
            # =================================================================
            
            if gastos_almoco:
                row += 3 

                headers_almoco = [
                    "Data", 
                    "Funcionário", 
                    "Descrição", 
                    "Observações", 
                    "Origem", 
                    "Valor (R$)"
                ]

                # Título Almoço
                ws.set_row(row, 25)
                ws.merge_range(row, 0, row, 5, "RELATÓRIO DE GASTOS COM ALMOÇO", fmt['title'])
                row += 2

                for col_num, header in enumerate(headers_almoco):
                    ws.write(row, col_num, header, fmt['header_table'])
                
                row += 1
                total_almoco = Decimal('0.00')

                for item in gastos_almoco:
                    dt_almoco = getattr(item, 'data_gasto', None)
                    
                    # Nome do Funcionário (Tratamento seguro)
                    func_obj = getattr(item, 'funcionario', None)
                    nome_func = ''
                    if func_obj:
                        # Tenta pegar atributo 'nome', se falhar usa string representation
                        nome_func = getattr(func_obj, 'nome', str(func_obj))

                    obs_almoco = getattr(item, 'observacoes', '') or ''
                    
                    # DESCRIÇÃO: Se estiver vazia, usa Observações como fallback para não ficar em branco
                    raw_desc = getattr(item, 'descricao', '') or ''
                    desc_almoco = raw_desc if raw_desc else obs_almoco
                    
                    origem = item.get_origem_pagamento_display() if hasattr(item, 'get_origem_pagamento_display') else getattr(item, 'origem_pagamento', '')

                    val_almoco = getattr(item, 'valor_total', Decimal('0.00')) or Decimal('0.00')

                    if dt_almoco:
                        ws.write(row, 0, dt_almoco, fmt['data_date'])
                    else:
                        ws.write(row, 0, '-', fmt['data_center'])
                    
                    ws.write(row, 1, nome_func, fmt['data_text'])
                    ws.write(row, 2, desc_almoco, fmt['data_text'])
                    ws.write(row, 3, obs_almoco, fmt['data_text'])
                    ws.write(row, 4, origem, fmt['data_center'])
                    ws.write(row, 5, val_almoco, fmt['data_money'])

                    total_almoco += val_almoco
                    row += 1

                row += 1
                ws.merge_range(row, 0, row, 4, "TOTAL ALMOÇO:", fmt['total_label'])
                ws.write(row, 5, total_almoco, fmt['total_money'])
            
            print(f"✅ Relatório de Gastos Gerais (com seção de Almoço) gerado.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de gastos: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output