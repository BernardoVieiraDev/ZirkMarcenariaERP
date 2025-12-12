import xlsxwriter
from decimal import Decimal
from datetime import date

class GastoGasolinaExcelService:
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
    def gerar_relatorio_gasolina(gastos, caminho_arquivo="RELATORIO_GASOLINA.xlsx"):
        try:
            wb = xlsxwriter.Workbook(caminho_arquivo)
            ws = wb.add_worksheet("Gasolina")
            fmt = GastoGasolinaExcelService._define_formats(wb)

            # Cabeçalhos solicitados
            headers = [
                "Carro / Veículo", 
                "Data do Gasto", 
                "Valor Total (R$)", 
                "Descrição"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 25) # Carro
            ws.set_column('B:B', 15) # Data
            ws.set_column('C:C', 18) # Valor
            ws.set_column('D:D', 40) # Descrição (mais larga)

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25)
            # Mescla de A (0) até D (3)
            ws.merge_range(row, 0, row, 3, "RELATÓRIO DE GASTOS COM GASOLINA", fmt['title'])
            row += 2 

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            total_valor = Decimal('0.00')

            # Iterar sobre os gastos
            for item in gastos:
                # 1. Extração de dados
                carro = getattr(item, 'carro', '') or ''
                dt_gasto = getattr(item, 'data_gasto', None)
                # Nota: Modelo usa 'valor_total'
                valor = getattr(item, 'valor_total', Decimal('0.00')) or Decimal('0.00')
                desc = getattr(item, 'descricao', '') or ''

                # 2. Escrever na planilha
                ws.write(row, 0, carro, fmt['data_text'])
                
                if dt_gasto:
                    ws.write(row, 1, dt_gasto, fmt['data_date'])
                else:
                    ws.write(row, 1, '-', fmt['data_text'])

                ws.write(row, 2, valor, fmt['data_money'])
                ws.write(row, 3, desc, fmt['data_text'])

                # Soma totais
                total_valor += valor
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 1, "TOTAL GERAL:", fmt['total_label'])
            ws.write(row, 2, total_valor, fmt['total_money'])
            ws.write(row, 3, "", fmt['total_label']) # Célula vazia para fechar a borda na descrição
            
            print(f"✅ Relatório de Gasolina gerado: {caminho_arquivo}")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de gasolina: {e}")
            raise e
        finally:
            if 'wb' in locals():
                wb.close()