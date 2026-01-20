import io
import xlsxwriter
from decimal import Decimal
from apps.financeiro.receber.models import Receber

class RelatorioReceberMensalService:
    # --- PALETA DE CORES (Azul Profissional & Clean) ---
    COR_PRIMARIA = '#1E3A8A'      # Azul Escuro Profundo (Header)
    COR_SECUNDARIA = '#2563EB'    # Azul Royal (Subtítulos)
    COR_TERCIARIA = '#BFDBFE'     # Azul Bebê (Bordas de destaque)
    
    COR_TEXTO_HEADER = '#FFFFFF'  
    
    COR_LINHA_PAR = '#FFFFFF'     
    COR_LINHA_IMPAR = '#F8FAFC'   # Azul/Cinza muito pálido (Zebra)
    
    COR_FUNDO_TOTAL = '#DBEAFE'   # Azul claro para o rodapé
    COR_TEXTO_TOTAL = '#1E3A8A'   # Texto do total
    
    # Bordas Modernas
    COR_BORDA_SUAVE = '#E2E8F0'   # Cinza azulado claro (interno)
    COR_BORDA_FORTE = '#1E3A8A'   # Azul escuro (externo)

    @classmethod
    def _define_formats(cls, workbook):
        base = {'font_name': 'Calibri', 'font_size': 10, 'valign': 'vcenter'}
        
        # Borda Suave (interno)
        border_inner = {'border': 1, 'border_color': cls.COR_BORDA_SUAVE}
        
        # Formato Contábil (R$ à esquerda, números à direita)
        fmt_money_str = '_("R$"* #,##0.00_);_("R$"* (#,##0.00);_("R$"* "-"??_);_(@_)'

        def create_fmt(updates):
            f = base.copy()
            f.update(updates)
            return workbook.add_format(f)

        return {
            # Título
            'title': create_fmt({
                'bold': True, 'font_size': 16, 'align': 'center', 
                'fg_color': cls.COR_PRIMARIA, 'font_color': cls.COR_TEXTO_HEADER,
                'top': 1, 'top_color': cls.COR_PRIMARIA,
            }),
            
            # Barra de Subtítulo (Design Strip)
            'subtitle_bar': create_fmt({
                'fg_color': cls.COR_PRIMARIA, 
                'bottom': 1, 'bottom_color': cls.COR_PRIMARIA
            }),
            
            # Cabeçalhos
            'header': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center', 
                'fg_color': cls.COR_SECUNDARIA, 'font_color': cls.COR_TEXTO_HEADER,
                'bottom': 2, 'bottom_color': cls.COR_BORDA_FORTE,
                'top': 1, 'top_color': cls.COR_BORDA_FORTE,
            }),

            # --- DADOS (Zebra Striping) ---
            # Texto
            'text_even': create_fmt({'align': 'left', 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'text_odd':  create_fmt({'align': 'left', 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),
            
            # Data
            'date_even': create_fmt({'align': 'center', 'num_format': 'dd/mm/yyyy', 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'date_odd':  create_fmt({'align': 'center', 'num_format': 'dd/mm/yyyy', 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),
            
            # Dinheiro
            'money_even': create_fmt({'align': 'right', 'num_format': fmt_money_str, 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'money_odd':  create_fmt({'align': 'right', 'num_format': fmt_money_str, 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),

            # --- TOTAIS (Rodapé) ---
            'total_label': create_fmt({
                'bold': True, 'align': 'right', 'font_size': 11,
                'bg_color': cls.COR_FUNDO_TOTAL, 'font_color': cls.COR_TEXTO_TOTAL,
                'top': 2, 'top_color': cls.COR_BORDA_FORTE,
                'bottom': 1, 'bottom_color': cls.COR_BORDA_FORTE
            }),
            'total_money': create_fmt({
                'bold': True, 'align': 'right', 'font_size': 11,
                'num_format': fmt_money_str, 
                'bg_color': cls.COR_FUNDO_TOTAL, 'font_color': cls.COR_TEXTO_TOTAL,
                'top': 2, 'top_color': cls.COR_BORDA_FORTE,
                'bottom': 1, 'bottom_color': cls.COR_BORDA_FORTE
            }),
            'total_empty': create_fmt({
                'bg_color': cls.COR_FUNDO_TOTAL,
                'top': 2, 'top_color': cls.COR_BORDA_FORTE,
                'bottom': 1, 'bottom_color': cls.COR_BORDA_FORTE
            }),
        }

    @staticmethod
    def gerar_arquivo(mes=None, ano=None, inicio=None, fim=None, workbook=None):
        output = None
        should_close = False

        # --- CORREÇÃO: Lógica para aceitar Workbook Externo ---
        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
            
        ws = workbook.add_worksheet("Contas a Receber")
        ws.hide_gridlines(2) 
        
        # Define os formatos no workbook atual
        fmt = RelatorioReceberMensalService._define_formats(workbook)

        # Filtro Híbrido
        if inicio and fim:
            qs = Receber.objects.filter(
                data_vencimento__range=[inicio, fim]
            ).order_by('data_vencimento')
            titulo = f"RELATÓRIO DE CONTAS A RECEBER - {inicio.strftime('%d/%m/%Y')} A {fim.strftime('%d/%m/%Y')}"
        else:
            qs = Receber.objects.filter(
                data_vencimento__year=ano, 
                data_vencimento__month=mes
            ).order_by('data_vencimento')
            titulo = f"RELATÓRIO DE CONTAS A RECEBER - {mes:02d}/{ano}"

        ws.set_column('A:A', 32); ws.set_column('B:B', 30); ws.set_column('C:C', 14)
        ws.set_column('D:D', 20); ws.set_column('E:E', 14); ws.set_column('F:F', 20)

        # Cabeçalho
        ws.set_row(0, 45) 
        ws.merge_range('A1:F1', titulo, fmt['title'])
        ws.set_row(1, 15)
        ws.merge_range('A2:F2', "", fmt['subtitle_bar'])

        ws.set_row(2, 30)
        headers = ["Cliente / Fonte", "Descrição", "Vencimento", "Valor Previsto", "Data Pagto", "Valor Real"]
        for col, h in enumerate(headers):
            ws.write(2, col, h, fmt['header'])

        # Dados
        row = 3
        total_prev = Decimal(0)
        total_rec = Decimal(0)

        for idx, item in enumerate(qs):
            suffix = '_odd' if idx % 2 else '_even'
            ws.set_row(row, 22)
            
            cliente = str(item.cliente) if item.cliente else '-'
            descricao = item.descricao if item.descricao else ''
            val_prev = item.valor if item.valor else Decimal(0)
            val_real = item.valor_recebido if item.valor_recebido else Decimal(0)
            
            ws.write(row, 0, cliente, fmt[f'text{suffix}'])
            ws.write(row, 1, descricao, fmt[f'text{suffix}'])
            ws.write(row, 2, item.data_vencimento, fmt[f'date{suffix}'])
            ws.write(row, 3, val_prev, fmt[f'money{suffix}'])
            ws.write(row, 4, item.data_recebimento if item.data_recebimento else '-', fmt[f'date{suffix}'])
            ws.write(row, 5, val_real, fmt[f'money{suffix}']) 
            
            total_prev += val_prev
            total_rec += val_real
            row += 1

        # Totais
        row += 1
        ws.set_row(row, 30)
        ws.merge_range(row, 0, row, 2, "TOTAIS DO PERÍODO:", fmt['total_label'])
        ws.write(row, 3, total_prev, fmt['total_money'])
        ws.write(row, 4, "", fmt['total_empty'])
        ws.write(row, 5, total_rec, fmt['total_money'])

        # --- CORREÇÃO FINAL: Fechamento Condicional ---
        if should_close:
            workbook.close()
            assert output is not None
            output.seek(0)
            return output
        
        return None