import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class BoletoExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'
    COR_BORDA = '#A9A9A9'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Define os formatos com a adição do TÍTULO."""
        return {
            # ADICIONADO: Formato do Título Principal
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
                'bold': True,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL,
                'font_color': '#FFFFFF',
                'font_name': 'Calibri',
                'border': 1
            }),
            'data_text': workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'border': 1,
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
    def gerar_relatorio_geral(boletos, workbook=None):
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
            ws = workbook.add_worksheet("Boletos")
            fmt = BoletoExcelService._define_formats(workbook)

            # Cabeçalhos das colunas
            headers = [
                "Descrição", 
                "Nota Fiscal / Nº", 
                "Valor (R$)", 
                "Vencimento", 
                "Valor Pago (R$)", 
                "Juros (R$)", 
                "Data Pagamento"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 30) #type: ignore
            ws.set_column('B:B', 20) #type: ignore
            ws.set_column('C:C', 15) #type: ignore
            ws.set_column('D:D', 15) #type: ignore
            ws.set_column('E:E', 15) #type: ignore
            ws.set_column('F:F', 12) #type: ignore
            ws.set_column('G:G', 15) #type: ignore

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25) # Altura da linha maior
            # Mescla da coluna 0 (A) até a 6 (G)
            ws.merge_range(row, 0, row, 6, "RELATÓRIO DE BOLETOS", fmt['title'])
            row += 2 # Pula uma linha para dar espaço

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 # Avança para dados
            total_valor = Decimal('0.00')
            total_pago = Decimal('0.00')

            # Iterar sobre os boletos
            for boleto in boletos:
                # Dados
                desc = getattr(boleto, 'descricao', '') or ''
                nf = getattr(boleto, 'nota_fiscal', '') or ''
                valor = getattr(boleto, 'valor', Decimal('0.00')) or Decimal('0.00')
                dt_venc = getattr(boleto, 'data_vencimento', None)
                val_pago = getattr(boleto, 'valor_pago', None)
                juros = getattr(boleto, 'juros', Decimal('0.00')) or Decimal('0.00')
                dt_pag = getattr(boleto, 'data_pagamento', None)

                # Escrever na linha
                ws.write(row, 0, desc, fmt['data_text'])
                ws.write(row, 1, nf, fmt['data_text'])
                ws.write(row, 2, valor, fmt['data_money'])
                
                if dt_venc:
                    ws.write(row, 3, dt_venc, fmt['data_date'])
                else:
                    ws.write(row, 3, '-', fmt['data_text'])

                if val_pago is not None:
                    ws.write(row, 4, val_pago, fmt['data_money'])
                    total_pago += val_pago
                else:
                    ws.write(row, 4, '-', fmt['data_text'])

                ws.write(row, 5, juros, fmt['data_money'])

                if dt_pag:
                    ws.write(row, 6, dt_pag, fmt['data_date'])
                else:
                    ws.write(row, 6, '-', fmt['data_text'])

                # Soma totais
                total_valor += valor
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1 # Pula uma linha para dar espaço
            ws.merge_range(row, 0, row, 1, "TOTAIS:", fmt['total_label'])
            ws.write(row, 2, total_valor, fmt['total_money']) # Total Valor
            ws.write(row, 3, "", fmt['total_label']) 
            ws.write(row, 4, total_pago, fmt['total_money'])  # Total Pago
            
            print(f"✅ Relatório de Boletos gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")
            raise e
        finally:
            # Só fecha e retorna se foi criado dentro deste método (Modo Individual)
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output