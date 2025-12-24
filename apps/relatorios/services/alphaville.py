import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class GastoImovelExcelService:
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
    def gerar_relatorio_condominio(gastos, workbook=None):
        # Lógica para suportar Múltiplas Abas ou Individual
        output = None
        should_close = False

        if workbook is None:
            # Modo Individual: Cria novo arquivo em memória
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = wb = workbook.add_worksheet("Condomínios")
            fmt = GastoImovelExcelService._define_formats(workbook)

            # Cabeçalhos
            headers = [
                "Local / Lote", 
                "Tipo", 
                "Descrição", 
                "Vencimento", 
                "Data Pagamento", 
                "Valor (R$)", 
                "Valor Pago (R$)", 
                "Juros (R$)",
                "Observações"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 25) #  type: ignore
            ws.set_column('B:B', 20) #  type: ignore
            ws.set_column('C:C', 30) #  type: ignore
            ws.set_column('D:D', 15) #  type: ignore
            ws.set_column('E:E', 15) #  type: ignore
            ws.set_column('F:F', 15) #  type: ignore
            ws.set_column('G:G', 15) #  type: ignore
            ws.set_column('H:H', 12) #  type: ignore
            ws.set_column('I:I', 35) #  type: ignore

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25)
            # Mescla de A (0) até I (8)
            ws.merge_range(row, 0, row, 8, "RELATÓRIO DE GASTOS IMOBILIÁRIOS (CONDOMÍNIO/TAXAS)", fmt['title'])
            row += 2 

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            total_valor = Decimal('0.00')
            total_pago = Decimal('0.00')

            # Iterar sobre os gastos
            for item in gastos:
                # 1. Identificação
                local = getattr(item, 'local_lote', '') or ''
                # Assume-se que o campo no model seja 'tipo_gasto', baseado no padrão
                tipo = item.get_tipo_gasto_display() if hasattr(item, 'get_tipo_gasto_display') else getattr(item, 'tipo_gasto', '')
                desc = getattr(item, 'descricao', '') or ''
                obs = getattr(item, 'observacoes', '') or ''
                
                # 2. Datas
                dt_venc = getattr(item, 'data_vencimento', None)
                dt_pag = getattr(item, 'data_pagamento', None)

                # 3. Valores
                valor = getattr(item, 'valor', Decimal('0.00')) or Decimal('0.00')
                val_pago = getattr(item, 'valor_pago', None)
                juros = getattr(item, 'juros', Decimal('0.00')) or Decimal('0.00')

                # Escrever na planilha
                ws.write(row, 0, local, fmt['data_text'])
                ws.write(row, 1, tipo, fmt['data_text'])
                ws.write(row, 2, desc, fmt['data_text'])
                
                # Datas
                if dt_venc:
                    ws.write(row, 3, dt_venc, fmt['data_date'])
                else:
                    ws.write(row, 3, '-', fmt['data_text'])

                if dt_pag:
                    ws.write(row, 4, dt_pag, fmt['data_date'])
                else:
                    ws.write(row, 4, '-', fmt['data_text'])

                # Valores
                ws.write(row, 5, valor, fmt['data_money'])
                
                if val_pago is not None:
                    ws.write(row, 6, val_pago, fmt['data_money'])
                    total_pago += val_pago
                else:
                    ws.write(row, 6, '-', fmt['data_text'])

                ws.write(row, 7, juros, fmt['data_money'])
                ws.write(row, 8, obs, fmt['data_text'])

                # Soma totais
                total_valor += valor
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 4, "TOTAIS:", fmt['total_label'])
            ws.write(row, 5, total_valor, fmt['total_money'])
            ws.write(row, 6, total_pago, fmt['total_money'])
            
            print(f"✅ Relatório de Condomínios gerado.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de condomínios: {e}")
            raise e
        finally:
            # Se foi criado aqui (Modo Individual), fecha e retorna
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output