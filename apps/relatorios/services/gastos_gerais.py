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
    def gerar_relatorio_geral(gastos, workbook=None):
        # Controle para saber se devemos fechar o arquivo ao final (Modo Individual)
        output = None
        should_close = False

        if workbook is None:
            # 1. Cria o buffer em memória se não receber um workbook existente
            output = io.BytesIO()
            # 2. Inicializa o Workbook
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("Gastos Gerais")
            fmt = GastoGeralExcelService._define_formats(workbook)

            # Cabeçalhos
            headers = [
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

            # Configurar largura das colunas
            ws.set_column('A:A', 12) # Data#type: ignore
            ws.set_column('B:B', 30) # Descrição#type: ignore
            ws.set_column('C:C', 15) # Motorista#type: ignore
            ws.set_column('D:D', 15) # Veículo#type: ignore
            ws.set_column('E:E', 20) # Cliente#type: ignore
            ws.set_column('F:F', 15) # Forma Pag#type: ignore
            ws.set_column('G:G', 15) # Valor Pix#type: ignore
            ws.set_column('H:H', 15) # Valor Cartão#type: ignore
            ws.set_column('I:I', 15) # Total#type: ignore

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25)
            # Mescla de A (0) até I (8)
            ws.merge_range(row, 0, row, 8, "RELATÓRIO DE GASTOS GERAIS (ALMOÇO, MATERIAL, ETC)", fmt['title'])
            row += 2 

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            # Totais Acumulados
            total_pix = Decimal('0.00')
            total_cartao = Decimal('0.00')
            total_geral = Decimal('0.00')

            # Iterar sobre os gastos
            for item in gastos:
                # 1. Dados Básicos
                dt_gasto = getattr(item, 'data_gasto', None)
                desc = getattr(item, 'descricao', '') or ''
                motorista = getattr(item, 'motorista', '') or ''
                carro = getattr(item, 'carro', '') or ''
                cliente = getattr(item, 'cliente', '') or ''
                
                forma = item.get_forma_principal_pagamento_display() if hasattr(item, 'get_forma_principal_pagamento_display') else item.forma_principal_pagamento

                # 2. Valores
                v_pix = getattr(item, 'valor_dinheiro_pix', Decimal('0.00')) or Decimal('0.00')
                v_cartao = getattr(item, 'valor_cartao', Decimal('0.00')) or Decimal('0.00')
                v_total = getattr(item, 'valor_total', Decimal('0.00')) or Decimal('0.00')

                # Escrever na planilha
                if dt_gasto:
                    ws.write(row, 0, dt_gasto, fmt['data_date'])
                else:
                    ws.write(row, 0, '-', fmt['data_center'])

                ws.write(row, 1, desc, fmt['data_text'])
                ws.write(row, 2, motorista, fmt['data_text'])
                ws.write(row, 3, carro, fmt['data_text'])
                ws.write(row, 4, cliente, fmt['data_text'])
                ws.write(row, 5, forma, fmt['data_center'])

                # Valores
                ws.write(row, 6, v_pix, fmt['data_money'])
                ws.write(row, 7, v_cartao, fmt['data_money'])
                # Destaque visual (opcional) ou normal para o total da linha
                ws.write(row, 8, v_total, fmt['data_money'])

                # Soma totais
                total_pix += v_pix
                total_cartao += v_cartao
                total_geral += v_total
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 5, "TOTAIS ACUMULADOS:", fmt['total_label'])
            ws.write(row, 6, total_pix, fmt['total_money'])
            ws.write(row, 7, total_cartao, fmt['total_money'])
            ws.write(row, 8, total_geral, fmt['total_money'])
            
            print(f"✅ Relatório de Gastos Gerais gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de gastos gerais: {e}")
            raise e
        finally:
            # Só fecha e retorna se foi criado dentro deste método (Modo Individual)
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output