import io
import xlsxwriter
from decimal import Decimal
from datetime import date
from apps.financeiro.pagar.models import (
    Boleto, Cheque, ComissaoArquiteto, FaturaCartao, FolhaPagamento,
    GastoContabilidade, GastoGasolina, GastoGeral, GastoImovel,
    GastoUtilidade, GastoVeiculoConsorcio, PrestacaoEmprestimo
)

class RelatorioPagarMensalService:
    # --- PALETA DE CORES (Refinada) ---
    COR_PRIMARIA = '#991B1B'      # Vermelho Profundo
    COR_SECUNDARIA = '#B91C1C'    # Vermelho Médio
    COR_TERCIARIA = '#FCA5A5'     # Vermelho Salmão
    
    COR_TEXTO_HEADER = '#FFFFFF'  
    
    COR_LINHA_PAR = '#FFFFFF'     
    COR_LINHA_IMPAR = '#FEF2F2'   # Rosa muito suave
    
    COR_FUNDO_TOTAL = '#FEE2E2'   
    COR_TEXTO_TOTAL = '#7F1D1D'   
    
    COR_BORDA_SUAVE = '#E5E7EB'   
    COR_BORDA_FORTE = '#7F1D1D'   

    @classmethod
    def _define_formats(cls, workbook):
        base = {'font_name': 'Calibri', 'font_size': 10, 'valign': 'vcenter'}
        
        border_inner = {'border': 1, 'border_color': cls.COR_BORDA_SUAVE}
        border_outer = {'bottom': 2, 'bottom_color': cls.COR_PRIMARIA}

        fmt_money_str = '_("R$"* #,##0.00_);_("R$"* (#,##0.00);_("R$"* "-"??_);_(@_)'

        def create_fmt(updates):
            f = base.copy()
            f.update(updates)
            return workbook.add_format(f)

        return {
            'title': create_fmt({
                'bold': True, 'font_size': 16, 'align': 'center', 
                'fg_color': cls.COR_PRIMARIA, 'font_color': cls.COR_TEXTO_HEADER,
                'top': 1, 'top_color': cls.COR_PRIMARIA,
            }),
            'subtitle_bar': create_fmt({
                'fg_color': cls.COR_PRIMARIA, 
                'bottom': 1, 'bottom_color': cls.COR_PRIMARIA
            }),
            'header': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center', 
                'fg_color': cls.COR_SECUNDARIA, 'font_color': cls.COR_TEXTO_HEADER,
                'bottom': 2, 'bottom_color': '#7F1D1D', 
                'top': 1, 'top_color': '#7F1D1D',
            }),
            'text_even': create_fmt({'align': 'left', 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'text_odd':  create_fmt({'align': 'left', 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),
            'date_even': create_fmt({'align': 'center', 'num_format': 'dd/mm/yyyy', 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'date_odd':  create_fmt({'align': 'center', 'num_format': 'dd/mm/yyyy', 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),
            'money_even': create_fmt({'align': 'right', 'num_format': fmt_money_str, 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'money_odd':  create_fmt({'align': 'right', 'num_format': fmt_money_str, 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),
            'center_even': create_fmt({'align': 'center', 'fg_color': cls.COR_LINHA_PAR, **border_inner}),
            'center_odd':  create_fmt({'align': 'center', 'fg_color': cls.COR_LINHA_IMPAR, **border_inner}),
            'total_label': create_fmt({
                'bold': True, 'align': 'right', 'font_size': 11,
                'bg_color': cls.COR_FUNDO_TOTAL, 'font_color': cls.COR_TEXTO_TOTAL,
                'top': 2, 'top_color': cls.COR_PRIMARIA, 
                'bottom': 1, 'bottom_color': cls.COR_PRIMARIA
            }),
            'total_money': create_fmt({
                'bold': True, 'align': 'right', 'font_size': 11,
                'num_format': fmt_money_str, 
                'bg_color': cls.COR_FUNDO_TOTAL, 'font_color': cls.COR_TEXTO_TOTAL,
                'top': 2, 'top_color': cls.COR_PRIMARIA,
                'bottom': 1, 'bottom_color': cls.COR_PRIMARIA
            }),
            'total_empty': create_fmt({
                'bg_color': cls.COR_FUNDO_TOTAL,
                'top': 2, 'top_color': cls.COR_PRIMARIA,
                'bottom': 1, 'bottom_color': cls.COR_PRIMARIA
            }),
        }

    @staticmethod
    def _buscar_dados(mes=None, ano=None, inicio=None, fim=None):
        lista = []
        models_config = [
            (Boleto, 'data_vencimento'), (GastoUtilidade, 'data_vencimento'),
            (FaturaCartao, 'data_vencimento'), (Cheque, 'data_emissao'),
            (PrestacaoEmprestimo, 'data_vencimento'), (GastoVeiculoConsorcio, 'data_vencimento'),
            (GastoContabilidade, 'data_vencimento'), (GastoImovel, 'data_vencimento'),
            (GastoGeral, 'data_gasto'), (GastoGasolina, 'data_gasto'),
            (FolhaPagamento, 'data_referencia'), (ComissaoArquiteto, 'data_pagamento')
        ]

        for Model, date_field in models_config:
            # Lógica Híbrida: Ou filtra por Mês/Ano ou por Range
            if inicio and fim:
                filtro = {f"{date_field}__range": [inicio, fim]}
            else:
                filtro = {f"{date_field}__year": ano, f"{date_field}__month": mes}
                
            qs = Model.objects.filter(**filtro)
            
            for item in qs:
                valor = getattr(item, 'valor', 0)
                if hasattr(item, 'get_valor_consolidado'): valor = item.get_valor_consolidado()
                elif hasattr(item, 'valor_total'): valor = item.valor_total
                
                credor = getattr(item, 'credor', 'Diversos')
                descricao = getattr(item, 'descricao', getattr(item, 'observacoes', '')) or ''
                data_pagamento = getattr(item, 'data_pagamento', None)

                lista.append({
                    'data': getattr(item, date_field),
                    'categoria': item._meta.verbose_name,
                    'credor': str(credor),
                    'descricao': str(descricao),
                    'valor': valor or Decimal(0),
                    'data_pagamento': data_pagamento
                })
        
        return sorted(lista, key=lambda x: x['data'])

    @staticmethod
    def gerar_arquivo(mes=None, ano=None, inicio=None, fim=None, workbook=None):
        output = None
        should_close = False

        # --- CORREÇÃO: Lógica para aceitar Workbook Externo (Pacote) ---
        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
            
        ws = workbook.add_worksheet("Contas a Pagar")
        ws.hide_gridlines(2)
        
        # Define os formatos no workbook atual
        fmt = RelatorioPagarMensalService._define_formats(workbook)

        # Configurações de coluna
        ws.set_column('A:A', 14); ws.set_column('B:B', 20); ws.set_column('C:C', 28) # type: ignore
        ws.set_column('D:D', 40); ws.set_column('E:E', 20); ws.set_column('F:F', 16)  # type: ignore

        # Cabeçalho Dinâmico
        ws.set_row(0, 45)
        if inicio and fim:
            titulo = f"RELATÓRIO DE CONTAS A PAGAR - {inicio.strftime('%d/%m/%Y')} A {fim.strftime('%d/%m/%Y')}"
            dados = RelatorioPagarMensalService._buscar_dados(inicio=inicio, fim=fim)
        else:
            titulo = f"RELATÓRIO DE CONTAS A PAGAR - {mes:02d}/{ano}"
            dados = RelatorioPagarMensalService._buscar_dados(mes=mes, ano=ano)
            
        ws.merge_range('A1:F1', titulo, fmt['title']) # type: ignore
        ws.set_row(1, 15)
        ws.merge_range('A2:F2', "", fmt['subtitle_bar']) # type: ignore

        # Cabeçalhos
        ws.set_row(2, 30)
        headers = ["Data Venc.", "Categoria", "Credor", "Descrição / Histórico", "Valor Previsto", "Data Pagto"]
        for col, h in enumerate(headers):
            ws.write(2, col, h, fmt['header'])

        # Dados
        row = 3
        total = Decimal(0)

        for idx, item in enumerate(dados):
            suffix = '_odd' if idx % 2 else '_even'
            ws.set_row(row, 22)
            ws.write(row, 0, item['data'], fmt[f'date{suffix}'])
            ws.write(row, 1, item['categoria'], fmt[f'text{suffix}'])
            ws.write(row, 2, item['credor'], fmt[f'text{suffix}'])
            ws.write(row, 3, item['descricao'], fmt[f'text{suffix}'])
            ws.write(row, 4, item['valor'], fmt[f'money{suffix}'])
            
            dt_pgto = item.get('data_pagamento')
            if dt_pgto: ws.write(row, 5, dt_pgto, fmt[f'date{suffix}'])
            else: ws.write(row, 5, '-', fmt[f'center{suffix}'])
            
            total += item['valor']
            row += 1

        # Totais
        row += 1
        ws.set_row(row, 30)
        ws.merge_range(row, 0, row, 3, "TOTAL GERAL DO PERÍODO:", fmt['total_label'])
        ws.write(row, 4, total, fmt['total_money'])
        ws.write(row, 5, "", fmt['total_empty'])

        # --- CORREÇÃO FINAL: Fechamento Condicional ---
        if should_close:
            workbook.close()
            assert output is not None
            output.seek(0)
            return output
        
        return None