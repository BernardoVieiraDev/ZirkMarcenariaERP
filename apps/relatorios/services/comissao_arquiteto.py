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
            ws = workbook.add_worksheet("Comissões RT")
            fmt = ComissaoExcelService._define_formats(workbook)

            # Cabeçalhos
            headers = [
                "Arquiteta(o)", 
                "Cliente / Projeto", 
                "Data Pagamento", 
                "Valor Comissão (R$)", 
                "Observações"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 30) # Arquiteta#type: ignore
            ws.set_column('B:B', 30) # Cliente#type: ignore
            ws.set_column('C:C', 15) # Data#type: ignore
            ws.set_column('D:D', 20) # Valor#type: ignore
            ws.set_column('E:E', 40) # Obs#type: ignore

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25)
            # Mescla de A (0) até E (4)
            ws.merge_range(row, 0, row, 4, "RELATÓRIO DE PAGAMENTOS - COMISSÕES (RT)", fmt['title'])
            row += 2 

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            total_valor = Decimal('0.00')

            # Iterar sobre os pagamentos (PagamentoRT)
            for item in pagamentos:
                # 1. Dados Relacionados (Acessando através do Contrato)
                arquiteta_nome = item.contrato.arquiteta.nome if item.contrato and item.contrato.arquiteta else "N/A"
                cliente_nome = item.contrato.cliente if item.contrato else "N/A"
                
                # 2. Dados do Pagamento
                dt_pag = getattr(item, 'data_pagamento', None)
                valor = getattr(item, 'valor_pago', Decimal('0.00')) or Decimal('0.00')
                obs = getattr(item, 'observacoes', '') or ''

                # Escrever na planilha
                ws.write(row, 0, arquiteta_nome, fmt['data_text'])
                ws.write(row, 1, cliente_nome, fmt['data_text'])
                
                if dt_pag:
                    ws.write(row, 2, dt_pag, fmt['data_date'])
                else:
                    ws.write(row, 2, '-', fmt['data_text'])

                ws.write(row, 3, valor, fmt['data_money'])
                ws.write(row, 4, obs, fmt['data_text'])

                # Soma totais
                total_valor += valor
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 2, "TOTAL PAGO:", fmt['total_label'])
            ws.write(row, 3, total_valor, fmt['total_money'])
            
            print(f"✅ Relatório de Comissões gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de comissões: {e}")
            raise e
        finally:
            # Só fecha e retorna se foi criado dentro deste método (Modo Individual)
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output