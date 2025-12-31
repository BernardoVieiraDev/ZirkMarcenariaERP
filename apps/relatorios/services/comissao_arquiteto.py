import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class ComissaoExcelService:
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
    def gerar_relatorio_comissoes(pagamentos, workbook=None):
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("Comissões RT")
            fmt = ComissaoExcelService._define_formats(workbook)

            headers = [
                "Arquiteta(o)", 
                "Cliente / Projeto", 
                "Data Pagamento", 
                "Valor Comissão (R$)", 
                "Observações"
            ]

            ws.set_column('A:A', 30)
            ws.set_column('B:B', 30)
            ws.set_column('C:C', 15)
            ws.set_column('D:D', 20)
            ws.set_column('E:E', 40)

            row = 0
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 4, "RELATÓRIO DE PAGAMENTOS - COMISSÕES (RT)", fmt['title'])
            row += 2 

            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            total_valor = Decimal('0.00')

            # --- CORREÇÃO AQUI ---
            # Agora 'item' é uma instância de ContratoRT
            for item in pagamentos:
                # Acesso direto à Arquiteta (ForeignKey) e Cliente (Campo Char)
                arquiteta_nome = item.arquiteta.nome if item.arquiteta else "N/A"
                cliente_nome = item.cliente if item.cliente else "N/A"
                
                # Acesso direto aos dados de pagamento no próprio contrato
                dt_pag = item.data_pagamento
                valor = item.valor_pago if item.valor_pago else Decimal('0.00')
                obs = item.observacoes if item.observacoes else ''

                ws.write(row, 0, arquiteta_nome, fmt['data_text'])
                ws.write(row, 1, cliente_nome, fmt['data_text'])
                
                if dt_pag:
                    ws.write(row, 2, dt_pag, fmt['data_date'])
                else:
                    ws.write(row, 2, '-', fmt['data_text'])

                ws.write(row, 3, valor, fmt['data_money'])
                ws.write(row, 4, obs, fmt['data_text'])

                total_valor += valor
                row += 1
            # ---------------------

            row += 1
            ws.merge_range(row, 0, row, 2, "TOTAL PAGO:", fmt['total_label'])
            ws.write(row, 3, total_valor, fmt['total_money'])
            
            print(f"✅ Relatório de Comissões gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de comissões: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output