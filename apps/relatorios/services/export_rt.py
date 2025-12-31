import io
import xlsxwriter
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from apps.comissionamento.models import ContratoRT

class ExportRTService:
    def __init__(self):
        self.output = io.BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output, {'in_memory': True})
        self.formats = self._define_formats()

    def _define_formats(self):
        base_font = 'Segoe UI'
        
        # Paleta de cores
        primary_color = '#154c79'  # Azul Escuro Profundo
        secondary_color = '#eef2f5' # Cinza muito claro
        accent_color = '#ffffff'    # Branco
        border_color = '#d0d7de'
        danger_bg = '#ffebee'       # Fundo vermelho claro
        danger_text = '#c62828'     # Texto vermelho escuro
        success_text = '#166534'    # Texto verde
        
        base_format = {'font_name': base_font, 'font_size': 10, 'valign': 'vcenter'}

        return {
            # --- Cabeçalho Arquiteta ---
            'arq_title': self.workbook.add_format({
                **base_format, 'bold': True, 'font_size': 14,
                'bg_color': primary_color, 'font_color': accent_color,
                'align': 'left', 'indent': 1
            }),
            'arq_label': self.workbook.add_format({
                **base_format, 'bold': True,
                'bg_color': secondary_color, 'font_color': '#555555',
                'align': 'right', 'border': 1, 'border_color': border_color
            }),
            'arq_value': self.workbook.add_format({
                **base_format,
                'bg_color': accent_color, 'font_color': '#000000',
                'align': 'left', 'indent': 1, 'border': 1, 'border_color': border_color
            }),

            # --- Tabelas ---
            'table_header': self.workbook.add_format({
                **base_format, 'bold': True,
                'bg_color': primary_color, 'font_color': accent_color,
                'align': 'center', 'border': 1, 'border_color': primary_color
            }),
            'cell_center': self.workbook.add_format({
                **base_format, 'align': 'center', 'border': 1, 'border_color': border_color
            }),
            'cell_text': self.workbook.add_format({
                **base_format, 'align': 'left', 'border': 1, 'border_color': border_color
            }),
            'cell_text_wrap': self.workbook.add_format({
                **base_format, 'font_size': 9, 'align': 'left',
                'border': 1, 'border_color': border_color, 'text_wrap': True
            }),
            'cell_date': self.workbook.add_format({
                **base_format, 'align': 'center', 'num_format': 'dd/mm/yyyy',
                'border': 1, 'border_color': border_color
            }),
            'cell_money': self.workbook.add_format({
                **base_format, 'align': 'right', 'num_format': 'R$ #,##0.00',
                'border': 1, 'border_color': border_color
            }),
            
            # --- Totais e Saldos ---
            'summary_label': self.workbook.add_format({
                **base_format, 'bold': True, 'font_size': 11,
                'bg_color': secondary_color, 
                'align': 'center', 
                'border': 1, 'border_color': border_color
            }),
            'summary_value': self.workbook.add_format({
                **base_format, 'bold': True, 'font_size': 11,
                'bg_color': secondary_color, # Fundo cinza para destacar a linha inteira
                'align': 'right', 'num_format': 'R$ #,##0.00',
                'border': 1, 'border_color': border_color
            }),
            
            'highlight_debt': self.workbook.add_format({
                **base_format, 'bold': True, 'font_size': 11,
                'bg_color': danger_bg, 'font_color': danger_text,
                'align': 'right', 'num_format': 'R$ #,##0.00',
                'border': 1, 'border_color': border_color
            }),
            'highlight_ok': self.workbook.add_format({
                **base_format, 'bold': True, 'font_size': 11,
                'bg_color': '#dcfce7', 'font_color': success_text,
                'align': 'right', 'num_format': 'R$ #,##0.00',
                'border': 1, 'border_color': border_color
            })
        }

    def generate_relatorio_individual(self, arquiteta):
        self._generate_aba_extrato(arquiteta)
        self._generate_aba_resumo_por_cliente(arquiteta)

    def _write_arquiteta_header(self, ws, arquiteta, title_text, width_cols=8):
        fmt_title = self.formats['arq_title']
        fmt_lbl = self.formats['arq_label']
        fmt_val = self.formats['arq_value']

        last_col_char = chr(64 + width_cols)
        ws.merge_range(f'A1:{last_col_char}2', f"  {title_text}", fmt_title)
        
        ws.write('A3', 'CPF:', fmt_lbl); ws.merge_range('B3:C3', arquiteta.cpf or '-', fmt_val)
        ws.write('D3', 'BANCO:', fmt_lbl); ws.merge_range(f'E3:{last_col_char}3', arquiteta.banco or '-', fmt_val)
        ws.write('A4', 'AGÊNCIA:', fmt_lbl); ws.merge_range('B4:C4', arquiteta.agencia or '-', fmt_val)
        ws.write('D4', 'CONTA:', fmt_lbl); ws.merge_range(f'E4:{last_col_char}4', arquiteta.conta or '-', fmt_val)

    def _generate_aba_extrato(self, arquiteta):
        """Aba 1: RT (Sem porcentagem, Detalhado)"""
        ws = self.workbook.add_worksheet("RT")
        ws.hide_gridlines(2)

        ws.set_column('A:A', 30) # Cliente
        ws.set_column('B:B', 15) # Data Contrato
        ws.set_column('C:C', 18) # Valor Serviço
        ws.set_column('D:D', 18) # Valor RT
        ws.set_column('E:E', 15) # Data Pag
        ws.set_column('F:F', 18) # Valor Pago
        ws.set_column('G:G', 50) # Obs

        self._write_arquiteta_header(ws, arquiteta, f"RELATÓRIO DE RT: {arquiteta.nome.upper()}", width_cols=7)

        headers = ["CLIENTE / OBRA", "DATA CONTRATO", "VALOR SERVIÇO", "VALOR DAS RT'S", "DATA PAGAMENTO", "VALOR PAGO", "OBSERVAÇÕES"]
        row = 6
        for col, h in enumerate(headers):
            ws.write(row, col, h, self.formats['table_header'])

        contratos = ContratoRT.objects.filter(arquiteta=arquiteta).order_by('data_contrato')

        row += 1
        total_rt = Decimal('0.00')
        total_pago = Decimal('0.00')

        for c in contratos:
            ws.write(row, 0, c.cliente, self.formats['cell_text'])
            ws.write(row, 1, c.data_contrato or "-", self.formats['cell_date'])
            ws.write(row, 2, c.valor_servico or 0, self.formats['cell_money'])
            ws.write(row, 3, c.valor_rt or 0, self.formats['cell_money'])
            ws.write(row, 4, c.data_pagamento or "-", self.formats['cell_date'])
            ws.write(row, 5, c.valor_pago or 0, self.formats['cell_money'])
            ws.write(row, 6, c.observacoes or "", self.formats['cell_text_wrap'])
            
            total_rt += (c.valor_rt or 0)
            total_pago += (c.valor_pago or 0)
            row += 1

        # --- TOTAIS ---
        row += 2 
        
        # 1. Total das RT's
        ws.merge_range(row, 3, row, 4, "TOTAL DAS RT'S:", self.formats['summary_label'])
        ws.write(row, 5, total_rt, self.formats['summary_value'])
        
        row += 1
        # 2. Total Pago
        ws.merge_range(row, 3, row, 4, "TOTAL PAGO:", self.formats['summary_label'])
        ws.write(row, 5, total_pago, self.formats['summary_value'])

        row += 1
        # 3. Valor a Pagar (Saldo)
        saldo_geral = total_rt - total_pago
        style_saldo = self.formats['highlight_debt'] if saldo_geral > 0 else self.formats['highlight_ok']
        
        ws.merge_range(row, 3, row, 4, "VALOR A PAGAR:", self.formats['summary_label'])
        ws.write(row, 5, saldo_geral, style_saldo)


    def _generate_aba_resumo_por_cliente(self, arquiteta):
        """Aba 2: Resumo por Cliente (Com Porcentagem, Saldo Explícito)"""
        ws = self.workbook.add_worksheet("Resumo por Cliente")
        ws.hide_gridlines(2)

        # Configura colunas
        ws.set_column('A:A', 30) # Cliente
        ws.set_column('B:B', 8)  # %
        ws.set_column('C:C', 18) # Valor Serviço
        ws.set_column('D:D', 18) # Valor RT
        ws.set_column('E:E', 15) # Data Pag
        ws.set_column('F:F', 18) # Valor Pago
        ws.set_column('G:G', 40) # Obs
        ws.set_column('H:H', 20) # SALDO

        self._write_arquiteta_header(ws, arquiteta, f"RT POR CLIENTE: {arquiteta.nome.upper()}", width_cols=8)

        headers = ["CLIENTE", "%", "VALOR SERVIÇO", "VALOR DA RT", "DATA PAGAMENTO", "VALOR PAGO", "OBSERVAÇÕES", "SALDO"]
        row = 6
        for col, h in enumerate(headers):
            ws.write(row, col, h, self.formats['table_header'])

        all_contratos = ContratoRT.objects.filter(arquiteta=arquiteta).order_by('cliente', 'data_contrato')
        
        # Agrupamento
        clientes_dict = {}
        for c in all_contratos:
            if c.cliente not in clientes_dict:
                clientes_dict[c.cliente] = []
            clientes_dict[c.cliente].append(c)

        row += 1
        
        for cliente_nome, contratos in clientes_dict.items():
            
            subtotal_rt = Decimal('0.00')
            subtotal_pago = Decimal('0.00')

            for c in contratos:
                ws.write(row, 0, c.cliente, self.formats['cell_text'])
                ws.write(row, 1, f"{c.percentual or 0}%", self.formats['cell_center'])
                ws.write(row, 2, c.valor_servico or 0, self.formats['cell_money'])
                ws.write(row, 3, c.valor_rt or 0, self.formats['cell_money'])
                ws.write(row, 4, c.data_pagamento or "-", self.formats['cell_date'])
                ws.write(row, 5, c.valor_pago or 0, self.formats['cell_money'])
                ws.write(row, 6, c.observacoes or "", self.formats['cell_text_wrap'])
                ws.write(row, 7, "-", self.formats['cell_center'])
                
                subtotal_rt += (c.valor_rt or 0)
                subtotal_pago += (c.valor_pago or 0)
                row += 1
            
            # --- LINHA DE TOTAL DO CLIENTE ---
            saldo_cliente = subtotal_rt - subtotal_pago
            style_saldo = self.formats['highlight_debt'] if saldo_cliente > 0 else self.formats['highlight_ok']
            
            # Label
            ws.write(row, 0, "TOTAL CLIENTE:", self.formats['summary_label'])
            
            # === CORREÇÃO: Preencher os subtotais para não ficar vazio ===
            ws.write(row, 3, subtotal_rt, self.formats['summary_value'])   # Total RT na coluna D
            ws.write(row, 5, subtotal_pago, self.formats['summary_value']) # Total Pago na coluna F
            
            # Saldo na Coluna H
            ws.write(row, 7, saldo_cliente, style_saldo)
            
            row += 2 

    def save(self, response):
        self.workbook.close()
        self.output.seek(0)
        response.write(self.output.getvalue())
        return response