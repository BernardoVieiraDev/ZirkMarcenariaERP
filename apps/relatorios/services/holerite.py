from datetime import date
import xlsxwriter
import io

class HoleriteExcelService:
    def __init__(self, buffer):
        self.workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        self._criar_estilos()

    def _criar_estilos(self):
        """Cria estilos globais."""
        font_main = 'Arial'
        bg_header = '#F0F0F0'
        border_thin = 1
        border_thick = 1

        self.styles = {}
        
        # --- Estilos Gerais ---
        self.styles['company_box'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'bold': True,
            'align': 'left', 'valign': 'top',
            'top': border_thick, 'left': border_thick, 'bottom': border_thin, 'text_wrap': True
        })
        self.styles['title_box'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 12, 'bold': True,
            'align': 'right', 'valign': 'vcenter', 'bg_color': bg_header,
            'top': border_thick, 'right': border_thick, 'left': border_thin, 'bottom': border_thin
        })
        
        self.styles['salario_box'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 10, 'bold': True,
            'align': 'center', 'valign': 'vcenter',
            'border': border_thin  
        })

        self.styles['ref_box'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 10, 'bold': True,
            'align': 'center', 'valign': 'vcenter',
            'bottom': border_thin, 'top': border_thin, 'right': border_thick, 'left': border_thin
        })

        # --- Labels e Valores ---
        self.styles['label'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 7, 'color': '#555555', 
            'align': 'left', 'valign': 'top', 
            'left': border_thick, 'right': border_thin,
            'top': border_thin  
        })
        
        self.styles['label_end'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 7, 'color': '#555555', 
            'align': 'left', 'valign': 'top', 
            'right': border_thick,
            'top': border_thin  
        })
        
        self.styles['value'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 9, 'bold': True, 
            'align': 'left', 'valign': 'bottom', 'left': border_thick, 
            'right': border_thin, 'bottom': border_thin, 'indent': 1
        })
        self.styles['value_end'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 9, 'bold': True, 
            'align': 'left', 'valign': 'bottom', 'right': border_thick, 
            'bottom': border_thin, 'indent': 1
        })

        # --- Tabela ---
        self.styles['th'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'bold': True, 'bg_color': bg_header, 
            'align': 'center', 'valign': 'vcenter', 'border': border_thin, 'top': border_thick
        })
        self.styles['th_first'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'bold': True, 'bg_color': bg_header, 
            'align': 'center', 'valign': 'vcenter', 'border': border_thin, 'top': border_thick, 'left': border_thick
        })
        self.styles['th_last'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'bold': True, 'bg_color': bg_header, 
            'align': 'center', 'valign': 'vcenter', 'border': border_thin, 'top': border_thick, 'right': border_thick
        })

        self.styles['item_center'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'align': 'center', 
            'left': border_thick, 'right': border_thin
        })
        self.styles['item_left'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'align': 'left', 
            'left': border_thin, 'right': border_thin
        })
        self.styles['item_money'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'align': 'right', 
            'num_format': '#,##0.00', 'left': border_thin, 'right': border_thin
        })
        self.styles['item_money_end'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 8, 'align': 'right', 
            'num_format': '#,##0.00', 'left': border_thin, 'right': border_thick
        })

        # --- Totais ---
        self.styles['total_void_left'] = self.workbook.add_format({
            'bg_color': bg_header, 'top': border_thin, 'bottom': border_thin, 'left': border_thick
        })
        self.styles['total_void_middle'] = self.workbook.add_format({
            'bg_color': bg_header, 'top': border_thin, 'bottom': border_thin
        })

        self.styles['total_lbl'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 9, 'bold': True, 'align': 'right', 
            'bg_color': bg_header, 'top': border_thin, 'bottom': border_thin
        })
        self.styles['total_val'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 9, 'bold': True, 'align': 'right', 
            'num_format': '#,##0.00', 'top': border_thin, 'bottom': border_thin, 'right': border_thick
        })
        self.styles['net_lbl'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 10, 'bold': True, 'align': 'right', 
            'bg_color': '#E8E8E8', 'top': border_thick, 'bottom': border_thick, 'left': border_thick
        })
        self.styles['net_box'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 11, 'bold': True, 'align': 'right', 
            'num_format': 'R$ #,##0.00', 'bg_color': '#E8E8E8', 
            'top': border_thick, 'bottom': border_thick, 'right': border_thick
        })

        # --- Rodapé e Assinatura ---
        self.styles['footer_txt'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 9, 'valign': 'top', 'text_wrap': True
        })
        
        self.styles['sig_line'] = self.workbook.add_format({
            'bottom': 1, 'align': 'center', 'valign': 'bottom'
        }) 
        self.styles['sig_text'] = self.workbook.add_format({
            'font_name': font_main, 'font_size': 10, 'align': 'center', 'valign': 'top'
        })
        
        self.styles['cut_line'] = self.workbook.add_format({
            'bottom': 1, 'bottom_color': '#999999', 'align': 'center', 
            'valign': 'center', 'font_size': 8, 'color': '#999999', 'font_script': 1
        })

    def adicionar_holerite(self, dados, nome_aba="Holerite"):
        safe_name = nome_aba[:30].replace(':', '').replace('/', '')
        ws = self.workbook.add_worksheet(safe_name)
        self._configurar_layout(ws)
        last_row = self._desenhar_holerite_compacto(ws, dados, start_row=0)
        ws.print_area(0, 0, last_row, 4)

    def adicionar_holerite_duplo(self, dados1, dados2, nome_aba="Holerites"):
        safe_name = nome_aba[:30].replace(':', '').replace('/', '')
        ws = self.workbook.add_worksheet(safe_name)
        
        self._configurar_layout(ws)

        last_row = self._desenhar_holerite_compacto(ws, dados1, start_row=0)

        if dados2:
            cut_row = last_row + 1  
            ws.merge_range(cut_row, 0, cut_row, 4, "- - - - - - - - - - - - CORTE AQUI - - - - - - - - - - - -", self.styles['cut_line'])
            last_row = self._desenhar_holerite_compacto(ws, dados2, start_row=cut_row + 2)
            
        ws.print_area(0, 0, last_row, 4)

    def _configurar_layout(self, ws):
        """Configuração otimizada para A4 Paisagem."""
        ws.hide_gridlines(2)
        ws.set_paper(9)      # A4
        ws.set_landscape()   # Paisagem
        ws.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 1)
        ws.center_horizontally()
        
        ws.set_column('A:A', 8)   # Cód
        ws.set_column('B:B', 51)  # Descrição
        ws.set_column('C:C', 10)  # Ref
        ws.set_column('D:D', 18)  # Venc
        ws.set_column('E:E', 18)  # Desc

    def _desenhar_holerite_compacto(self, ws, dados, start_row=0):
        s = self.styles
        r = start_row

        ws.set_row(r, 15)
        ws.set_row(r+1, 15)
        ws.set_row(r+2, 20)

        # 1. Cabeçalho
        empresa_text = f"{dados['empregador']['nome'].upper()}\nCNPJ: {dados['empregador']['cnpj']}"
        ws.merge_range(r, 0, r+2, 1, empresa_text, s['company_box'])
        
        ws.merge_range(r, 2, r+1, 4, dados['cabecalho']['titulo'].upper(), s['title_box'])
        
        salario_val = dados.get('bases', {}).get('salario_base', 0.0)
        salario_str = f"{salario_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # O campo Salário usa o novo estilo com borda grossa
        ws.merge_range(r+2, 2, r+2, 3, f"SALÁRIO: {salario_str}", s['salario_box'])
        ws.write(r+2, 4, f"REF: {dados['cabecalho']['referencia']}", s['ref_box'])

        # 2. Funcionário
        r += 3
        ws.write(r, 0, 'CÓD.', s['label'])
        ws.write(r, 1, 'NOME DO COLABORADOR', s['label'])
        ws.write(r, 2, 'ADMISSÃO', s['label'])
        ws.merge_range(r, 3, r, 4, 'CARGO', s['label_end'])
        
        r += 1
        ws.write(r, 0, dados['funcionario'].get('codigo', ''), s['value'])
        ws.write(r, 1, dados['funcionario']['nome'], s['value'])
        ws.write(r, 2, dados['funcionario'].get('admissao', ''), s['value'])
        ws.merge_range(r, 3, r, 4, dados['funcionario']['cargo'], s['value_end'])

        # 3. Tabela de Eventos
        r += 1
        ws.set_row(r, 18)
        ws.write(r, 0, 'CÓD.', s['th_first'])
        ws.write(r, 1, 'DESCRIÇÃO', s['th'])
        ws.write(r, 2, 'REF.', s['th'])
        ws.write(r, 3, 'PROVENTOS', s['th']) 
        ws.write(r, 4, 'DESCONTOS', s['th_last'])

        num_rows_items = 10
        eventos = dados['eventos']
        
        for i in range(num_rows_items):
            r += 1
            ws.write(r, 0, '', s['item_center'])
            ws.write(r, 1, '', s['item_left'])
            ws.write(r, 2, '', s['item_center'])
            ws.write(r, 3, '', s['item_money'])
            ws.write(r, 4, '', s['item_money_end'])

            if i < len(eventos):
                evt = eventos[i]
                ws.write(r, 0, evt.get('codigo', ''), s['item_center'])
                ws.write(r, 1, evt['descricao'], s['item_left'])
                ws.write(r, 2, evt.get('ref', ''), s['item_center'])
                
                if evt.get('vencimento'): ws.write(r, 3, evt['vencimento'], s['item_money'])
                if evt.get('desconto'): ws.write(r, 4, evt['desconto'], s['item_money_end'])

        # 4. Totais
        r += 1
        ws.write(r, 0, '', s['total_void_left']) 
        ws.write(r, 1, '', s['total_void_middle'])
        
        ws.write(r, 2, 'TOTAIS:', s['total_lbl'])
        ws.write(r, 3, dados['totais']['bruto'], s['total_val'])
        ws.write(r, 4, dados['totais']['descontos'], s['total_val'])

        # 5. Líquido
        r += 1
        ws.set_row(r, 22)
        ws.merge_range(r, 0, r, 2, 'LÍQUIDO A RECEBER ➔ ', s['net_lbl'])
        ws.merge_range(r, 3, r, 4, dados['totais']['liquido'], s['net_box'])

        # 6. Assinatura e Rodapé
        r += 1
        ws.merge_range(r, 0, r, 2, 
            "Declaro ter recebido a importância líquida discriminada neste recibo.", 
            s['footer_txt'])
        
        data_pag = dados.get('data_pagamento', date.today())
        ws.write_string(r, 3, f"Data: {data_pag.strftime('%d/%m/%Y')}", s['footer_txt'])
        
        r += 1
        ws.set_row(r, 45) 
        ws.merge_range(r, 2, r, 4, "", s['sig_line'])
        
        r += 1
        ws.merge_range(r, 2, r, 4, "Assinatura do Funcionário", s['sig_text'])

        return r + 2

    def gerar_recibo(self, dados, nome_aba="Holerite"):
        """ Função espelho para manter compatibilidade caso algum fluxo chame assim """
        self.adicionar_holerite(dados, nome_aba)

    def close(self):
        self.workbook.close()