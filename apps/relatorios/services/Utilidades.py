import xlsxwriter
from decimal import Decimal
from datetime import date

class GastoUtilidadeExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Formatos idênticos aos do Boleto + TÍTULO."""
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
                'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
                'font_name': 'Calibri', 'border': 1
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
    def gerar_relatorio_utilidades(gastos, caminho_arquivo="RELATORIO_UTILIDADES.xlsx"):
        try:
            wb = xlsxwriter.Workbook(caminho_arquivo)
            ws = wb.add_worksheet("Utilidades")
            fmt = GastoUtilidadeExcelService._define_formats(wb)

            # Cabeçalhos solicitados
            headers = [
                "Cliente / Tipo", 
                "Vencimento", 
                "Data Pagamento",
                "Valor (R$)"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 35) 
            ws.set_column('B:B', 15) 
            ws.set_column('C:C', 15) 
            ws.set_column('D:D', 18) 

            row = 0

            # --- ADICIONADO: TÍTULO NO TOPO ---
            ws.set_row(row, 25) # Aumenta altura da linha
            # Mescla da coluna 0 (A) até a 3 (D)
            ws.merge_range(row, 0, row, 3, "RELATÓRIO DE UTILIDADES (ÁGUA, LUZ, TELEFONE)", fmt['title'])
            row += 2 # Pula linha para espaçamento

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 # Avança para os dados
            total_valor = Decimal('0.00')

            # Iterar sobre os gastos
            for item in gastos:
                # 1. Cliente
                cliente_nome = item.get_tipo_cliente_display() if hasattr(item, 'get_tipo_cliente_display') else str(item.tipo_cliente)
                
                # 2. Datas
                dt_venc = getattr(item, 'data_vencimento', None)
                dt_pag = getattr(item, 'data_pagamento', None)

                # 3. Valor
                valor = getattr(item, 'valor', Decimal('0.00')) or Decimal('0.00')

                # Escrever na planilha
                ws.write(row, 0, cliente_nome, fmt['data_text'])
                
                if dt_venc:
                    ws.write(row, 1, dt_venc, fmt['data_date'])
                else:
                    ws.write(row, 1, '-', fmt['data_text'])

                if dt_pag:
                    ws.write(row, 2, dt_pag, fmt['data_date'])
                else:
                    ws.write(row, 2, '-', fmt['data_text'])

                ws.write(row, 3, valor, fmt['data_money'])

                # Soma total
                total_valor += valor
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 2, "TOTAL GERAL:", fmt['total_label'])
            ws.write(row, 3, total_valor, fmt['total_money'])
            
            print(f"✅ Relatório de Utilidades gerado: {caminho_arquivo}")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório utilidades: {e}")
            raise e
        finally:
            if 'wb' in locals():
                wb.close()