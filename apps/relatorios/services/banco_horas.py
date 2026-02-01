import io
import xlsxwriter
from decimal import Decimal
from django.utils import timezone

class BancoHorasExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Define os formatos padrão seguindo o estilo do sistema."""
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
            'data_number': workbook.add_format({
                'align': 'right', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': '#,##0.00'
            }),
            'data_money': workbook.add_format({
                'align': 'right', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': 'R$ #,##0.00'
            }),
            # Formatação condicional simples para saldos positivos/negativos
            'data_number_bold': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': '#,##0.00'
            }),
        }

    @staticmethod
    def gerar_relatorio(bancos_horas, lancamentos):
        """
        Gera relatório contendo:
        1. Tabela de Saldos Atuais (BancoHoras)
        2. Tabela de Histórico de Lançamentos (LancamentoHoras)
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        try:
            ws = workbook.add_worksheet("Relatório Banco de Horas")
            fmt = BancoHorasExcelService._define_formats(workbook)

            # =================================================================
            # SEÇÃO 1: SALDOS ATUAIS (RESUMO)
            # =================================================================
            row = 0
            
            # Cabeçalhos Saldos
            headers_resumo = ["Funcionário", "Atualizado Em", "Saldo Atual (Horas)"]
            
            # Larguras das colunas
            ws.set_column('A:A', 35)  # Funcionário
            ws.set_column('B:B', 20)  # Data
            ws.set_column('C:C', 20)  # Saldo / Horas
            ws.set_column('D:D', 40)  # Descrição
            ws.set_column('E:E', 15)  # Valor Hora
            ws.set_column('F:F', 15)  # Total Monetário

            # Título Resumo
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 2, "RESUMO DE SALDOS ATUAIS", fmt['title'])
            row += 2

            for col_num, header in enumerate(headers_resumo):
                ws.write(row, col_num, header, fmt['header_table'])
            
            row += 1

            if bancos_horas:
                for banco in bancos_horas:
                    ws.write(row, 0, banco.funcionario.nome, fmt['data_text'])
                    ws.write(row, 1, banco.atualizado_em.strftime('%d/%m/%Y %H:%M'), fmt['data_center'])
                    ws.write(row, 2, banco.saldo, fmt['data_number_bold'])
                    row += 1
            else:
                ws.merge_range(row, 0, row, 2, "Nenhum banco de horas ativo.", fmt['data_center'])
                row += 1

            # =================================================================
            # SEÇÃO 2: EXTRATO DE LANÇAMENTOS
            # =================================================================
            row += 3  # Espaçamento entre tabelas

            headers_detalhe = [
                "Data Evento", 
                "Funcionário", 
                "Horas Lançadas", 
                "Descrição", 
                "Valor Hora (R$)", 
                "Total (R$)"
            ]

            # Título Detalhes
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 5, "EXTRATO DETALHADO DE LANÇAMENTOS", fmt['title'])
            row += 2

            for col_num, header in enumerate(headers_detalhe):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1

            if lancamentos:
                for lanc in lancamentos:
                    # Garantir dados seguros
                    data_evento = lanc.data
                    nome_func = lanc.funcionario.nome
                    horas = lanc.horas
                    desc = lanc.descricao or '-'
                    valor_hora = lanc.valor_hora
                    total = lanc.total_monetario

                    ws.write(row, 0, data_evento, fmt['data_date'])
                    ws.write(row, 1, nome_func, fmt['data_text'])
                    ws.write(row, 2, horas, fmt['data_number'])
                    ws.write(row, 3, desc, fmt['data_text'])
                    ws.write(row, 4, valor_hora, fmt['data_money'])
                    ws.write(row, 5, total, fmt['data_money'])
                    row += 1
            else:
                ws.merge_range(row, 0, row, 5, "Nenhum lançamento registrado.", fmt['data_center'])

        except Exception as e:
            # Em produção, ideal logar o erro
            print(f"Erro ao gerar Excel Banco Horas: {e}")
            raise e
        finally:
            workbook.close()
            output.seek(0)
            return output