import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class GastoContabilidadeExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Formatos padrão incluindo o TÍTULO principal."""
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
    def gerar_relatorio_contabilidade(gastos, workbook=None):
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("Contabilidade")
            fmt = GastoContabilidadeExcelService._define_formats(workbook)

            # Cabeçalhos das colunas (Removido 'Valor Pago')
            headers = [
                "Tipo",
                "Descrição",
                "Observação",
                "Vencimento",
                "Data Pagamento",
                "Valor (R$)"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 20) # Tipo
            ws.set_column('B:B', 30) # Descrição
            ws.set_column('C:C', 30) # Observação
            ws.set_column('D:D', 12) # Vencimento
            ws.set_column('E:E', 15) # Dt Pagamento
            ws.set_column('F:F', 15) # Valor

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25)
            # Mescla da coluna A (0) até a F (5)
            ws.merge_range(row, 0, row, 5, "RELATÓRIO DE CONTABILIDADE", fmt['title'])
            row += 2 

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 # Avança para dados
            total_valor = Decimal('0.00')

            # Iterar sobre os gastos
            for item in gastos:
                tipo = item.get_tipo_gasto_display() if hasattr(item, 'get_tipo_gasto_display') else item.tipo_gasto
                desc = getattr(item, 'descricao', '') or ''
                obs = getattr(item, 'observacoes', '') or ''
                
                dt_venc = getattr(item, 'data_vencimento', None)
                dt_pag = getattr(item, 'data_pagamento', None)

                valor = getattr(item, 'valor', Decimal('0.00')) or Decimal('0.00')

                # Escrever na planilha
                ws.write(row, 0, tipo, fmt['data_text'])
                ws.write(row, 1, desc, fmt['data_text'])
                ws.write(row, 2, obs, fmt['data_text'])

                if dt_venc:
                    ws.write(row, 3, dt_venc, fmt['data_date'])
                else:
                    ws.write(row, 3, '-', fmt['data_text'])

                if dt_pag:
                    ws.write(row, 4, dt_pag, fmt['data_date'])
                else:
                    ws.write(row, 4, '-', fmt['data_text'])

                ws.write(row, 5, valor, fmt['data_money'])

                total_valor += valor
                row += 1

            # --- LINHA DE TOTAIS ---
            row += 1
            ws.merge_range(row, 0, row, 4, "TOTAL:", fmt['total_label'])
            ws.write(row, 5, total_valor, fmt['total_money'])
            
            print(f"✅ Relatório Contábil gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório contábil: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output