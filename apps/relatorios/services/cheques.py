import io
import xlsxwriter
from decimal import Decimal
from datetime import date

class ChequeExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    
    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Define os formatos padrão com adição do TÍTULO."""
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
    def gerar_relatorio_cheques(cheques, workbook=None):
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
            ws = workbook.add_worksheet("Cheques")
            fmt = ChequeExcelService._define_formats(workbook)

            # Cabeçalhos
            headers = [
                "Nº Cheque", 
                "Despesa / Descrição", 
                "Entidade", 
                "Data Emissão", 
                "Status", 
                "Valor (R$)"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 15) #type: ignore
            ws.set_column('B:B', 35) #type: ignore
            ws.set_column('C:C', 15) #type: ignore
            ws.set_column('D:D', 15) #type: ignore
            ws.set_column('E:E', 15) #type: ignore
            ws.set_column('F:F', 18) #type: ignore

            row = 0

            # --- ADICIONADO: TÍTULO NO TOPO ---
            ws.set_row(row, 25) # Altura da linha maior
            # Mescla da coluna 0 (A) até a 5 (F)
            ws.merge_range(row, 0, row, 5, "RELATÓRIO DE CHEQUES", fmt['title'])
            row += 2 # Pula linha para espaçamento

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 # Avança para dados
            total_valor = Decimal('0.00')

            # Iterar sobre os cheques
            for item in cheques:
                # Extração de dados
                num_cheque = getattr(item, 'numero_cheque', '')
                descricao = getattr(item, 'descricao', '')
                
                # Choices
                entidade = item.get_tipo_entidade_display() if hasattr(item, 'get_tipo_entidade_display') else item.tipo_entidade
                status = item.get_status_display() if hasattr(item, 'get_status_display') else item.status
                
                dt_emissao = getattr(item, 'data_emissao', None)
                valor = getattr(item, 'valor', Decimal('0.00')) or Decimal('0.00')

                # Escrever na planilha
                ws.write(row, 0, num_cheque, fmt['data_center']) 
                ws.write(row, 1, descricao, fmt['data_text'])
                ws.write(row, 2, entidade, fmt['data_center'])
                
                if dt_emissao:
                    ws.write(row, 3, dt_emissao, fmt['data_date'])
                else:
                    ws.write(row, 3, '-', fmt['data_center'])

                ws.write(row, 4, status, fmt['data_center'])
                ws.write(row, 5, valor, fmt['data_money'])

                # Soma total
                total_valor += valor
                row += 1

            # --- LINHA DE TOTAL ---
            row += 1
            ws.merge_range(row, 0, row, 4, "TOTAL EM CHEQUES:", fmt['total_label'])
            ws.write(row, 5, total_valor, fmt['total_money'])
            
            print(f"✅ Relatório de Cheques gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de cheques: {e}")
            raise e
        finally:
            # Só fecha e retorna se foi criado dentro deste método (Modo Individual)
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output