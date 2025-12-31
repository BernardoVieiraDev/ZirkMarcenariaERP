import io
import xlsxwriter
from decimal import Decimal
from datetime import datetime

class VendasExcelService:
    # --- Paleta de Cores ---
    COR_TITULO_BG = '#2C3E50'       
    COR_TITULO_TEXTO = '#FFFFFF'    
    COR_HEADER_BG = '#34495E'       
    COR_HEADER_TEXT = '#FFFFFF'     
    COR_SUBHEADER_BG = '#BDC3C7'    
    COR_SUBHEADER_TEXT = '#2C3E50'  
    
    # Cores Vendas (Verdes)
    COR_VISTA_BG = '#E8F6F3'        
    COR_VISTA_TEXT = '#16A085'      
    COR_PRAZO_BG = '#FEF9E7'        
    COR_PRAZO_TEXT = '#D35400'      
    
    # Cores Compras (Vermelhos/Laranjas - para diferenciar visualmente)
    COR_COMPRA_VISTA_BG = '#FADBD8' # Vermelho claro suave
    COR_COMPRA_VISTA_TEXT = '#C0392B'
    COR_COMPRA_PRAZO_BG = '#FDEBD0' # Laranja claro
    COR_COMPRA_PRAZO_TEXT = '#E67E22'

    COR_TOTAL_BG = '#F4F6F7'        
    COR_TOTAL_TEXT = '#2C3E50'      
    COR_LINHA_DIVISORIA = '#BDC3C7' 

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        font_base = {'font_name': 'Calibri', 'valign': 'vcenter', 'font_size': 10}
        bottom_line = {'bottom': 1, 'bottom_color': '#E0E0E0'} 
        right_border = {'right': 1, 'right_color': cls.COR_LINHA_DIVISORIA}

        # Format base creator helper
        def create_fmt(updates):
            f = font_base.copy()
            f.update(updates)
            return workbook.add_format(f)

        return {
            'main_title': create_fmt({
                'bold': True, 'font_size': 18, 'align': 'center',
                'font_color': cls.COR_TITULO_TEXTO, 'bg_color': cls.COR_TITULO_BG,
                'top': 1, 'top_color': cls.COR_TITULO_BG,
                'left': 1, 'left_color': cls.COR_TITULO_BG,
                'right': 1, 'right_color': cls.COR_TITULO_BG,
            }),
            'main_title_bar': workbook.add_format({
                'bg_color': cls.COR_TITULO_BG,
                'bottom': 2, 'bottom_color': cls.COR_TITULO_BG,
                'left': 1, 'left_color': cls.COR_TITULO_BG,
                'right': 1, 'right_color': cls.COR_TITULO_BG,
            }),
            'header_dark': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center',
                'fg_color': cls.COR_HEADER_BG, 'font_color': cls.COR_HEADER_TEXT,
                'border': 1, 'border_color': cls.COR_HEADER_BG
            }),
            'subheader': create_fmt({
                'font_size': 10, 'align': 'center', 'bold': True,
                'fg_color': cls.COR_SUBHEADER_BG, 'font_color': cls.COR_SUBHEADER_TEXT,
                'border': 1, 'border_color': '#95A5A6'
            }),
            # --- Vendas ---
            'header_vista': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center',
                'fg_color': cls.COR_VISTA_BG, 'font_color': cls.COR_VISTA_TEXT,
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            'header_prazo': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center',
                'fg_color': cls.COR_PRAZO_BG, 'font_color': cls.COR_PRAZO_TEXT,
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            # --- Compras (Novos Estilos) ---
            'header_compra_vista': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center',
                'fg_color': cls.COR_COMPRA_VISTA_BG, 'font_color': cls.COR_COMPRA_VISTA_TEXT,
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            'header_compra_prazo': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'center',
                'fg_color': cls.COR_COMPRA_PRAZO_BG, 'font_color': cls.COR_COMPRA_PRAZO_TEXT,
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            # --- Dados ---
            'month_label': create_fmt({
                'align': 'left', 'indent': 1, 'font_color': '#333333',
                **bottom_line, 'right': 1, 'right_color': '#BDC3C7'
            }),
            'money': create_fmt({
                'align': 'right', 'num_format': '#,##0.00',
                'font_color': '#333333', **bottom_line
            }),
            'percent': create_fmt({
                'align': 'center', 'num_format': '0.0%',
                'font_color': '#7F8C8D', **bottom_line, **right_border
            }),
            'total_money': create_fmt({
                'bold': True, 'align': 'right', 
                'num_format': '#,##0.00', 'bg_color': cls.COR_TOTAL_BG,
                'font_color': cls.COR_TOTAL_TEXT, **bottom_line
            }),
            # --- Médias ---
            'media_label': create_fmt({
                'bold': True, 'align': 'left', 'indent': 1,
                'bg_color': '#E5E8E8', 'font_color': cls.COR_TITULO_BG,
                'bottom': 2, 'bottom_color': cls.COR_TITULO_BG
            }),
            'media_money': create_fmt({
                'bold': True, 'align': 'right',
                'num_format': '#,##0.00', 'bg_color': '#E5E8E8', 'font_color': cls.COR_TITULO_BG,
                'bottom': 2, 'bottom_color': cls.COR_TITULO_BG
            }),
            'media_percent': create_fmt({
                'bold': True, 'align': 'center',
                'num_format': '0.0%', 'bg_color': '#E5E8E8', 'font_color': '#7F8C8D',
                'bottom': 2, 'bottom_color': cls.COR_TITULO_BG, **right_border
            }),
            'media_total': create_fmt({
                'bold': True, 'align': 'right',
                'num_format': '#,##0.00', 'bg_color': '#D7DBDD', 
                'font_color': cls.COR_TITULO_BG,
                'bottom': 2, 'bottom_color': cls.COR_TITULO_BG
            }),
        }

    @staticmethod
    def _processar_dados_mes(dados, num_mes, termos_vista, tipo='venda'):
        """Helper para processar dados de um mês específico."""
        val_vista = Decimal(0)
        val_prazo = Decimal(0)
        
        # Filtra na memória
        itens_mes = []
        for d in dados:
            # Lidar com diferentes nomes de campo de data (para Vendas e Compras)
            data_ref = getattr(d, 'data_vencimento', None)
            if not data_ref:
                data_ref = getattr(d, 'data_gasto', None) # Caso seja GastoGeral/Gasolina
                
            if data_ref and data_ref.month == num_mes:
                itens_mes.append(d)

        for item in itens_mes:
            # Lidar com diferentes nomes de campo de valor
            valor = getattr(item, 'valor', None)
            if valor is None: # Se não tem 'valor', tenta 'valor_total' (GastoGeral) ou 'valor_comissao'
                valor = getattr(item, 'valor_total', None)
            if valor is None:
                valor = getattr(item, 'valor_comissao', None)
            
            valor = valor if valor else Decimal(0)
            
            # Concatena campos de texto para busca de palavras-chave
            texto_busca = (
                f"{getattr(item, 'forma_de_recebimento', '')} "
                f"{getattr(item, 'forma_principal_pagamento', '')} " # GastoGeral
                f"{getattr(item, 'observacoes', '')} "
                f"{getattr(item, 'categoria', '')} "
                f"{getattr(item, 'descricao', '')}"
            ).lower()
            
            if any(t in texto_busca for t in termos_vista):
                val_vista += valor
            else:
                val_prazo += valor

        total = val_vista + val_prazo
        return val_vista, val_prazo, total

    @staticmethod
    def gerar_relatorio_vendas(dados_receber, dados_pagar, workbook=None):
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True

        try:
            ws = workbook.add_worksheet("Vendas e Compras")
            ws.hide_gridlines(2)
            fmt = VendasExcelService._define_formats(workbook)

            # Configura Colunas
            ws.set_column('A:A', 22)
            ws.set_column('B:B', 18)
            ws.set_column('C:C', 10)
            ws.set_column('D:D', 18)
            ws.set_column('E:E', 10)
            ws.set_column('F:F', 22)

            meses_estrutura = [
                (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
                (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
                (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
            ]

            # =================================================================
            # PARTE 1: VENDAS (RECEBER)
            # =================================================================
            row = 1
            ws.set_row(row, 35)
            ws.merge_range(row, 0, row, 5, "RELATÓRIO DE DESEMPENHO (VENDAS)", fmt['main_title'])
            ws.set_row(row + 1, 8) 
            ws.merge_range(row + 1, 0, row + 1, 5, "", fmt['main_title_bar'])
            row += 2

            ws.set_row(row, 20)
            ws.merge_range(row, 0, row+1, 0, "PERÍODO", fmt['header_dark'])
            ws.merge_range(row, 1, row, 2, "À VISTA (Dinheiro/Pix)", fmt['header_vista'])
            ws.merge_range(row, 3, row, 4, "A PRAZO (Boleto/Cartão)", fmt['header_prazo'])
            ws.merge_range(row, 5, row+1, 5, "TOTAL GERAL", fmt['header_dark']) 
            
            ws.set_row(row+1, 20)
            ws.write(row+1, 1, "Valor (R$)", fmt['subheader'])
            ws.write(row+1, 2, "%", fmt['subheader'])
            ws.write(row+1, 3, "Valor (R$)", fmt['subheader'])
            ws.write(row+1, 4, "%", fmt['subheader'])
            row += 2

            # Processar Vendas
            termos_vendas = ['pix', 'dinheiro', 'especie', 'espécie', 'caixa', 'débito', 'debito', 'transferencia']
            dados_processados_vendas = []
            soma_v_vista, soma_v_prazo, soma_v_total, meses_v_mov = Decimal(0), Decimal(0), Decimal(0), 0

            todos_receber = list(dados_receber)

            for num_mes, nome_mes in meses_estrutura:
                vista, prazo, total = VendasExcelService._processar_dados_mes(todos_receber, num_mes, termos_vendas)
                
                if total > 0:
                    meses_v_mov += 1
                    soma_v_vista += vista
                    soma_v_prazo += prazo
                    soma_v_total += total

                dados_processados_vendas.append({'mes': nome_mes, 'vista': vista, 'prazo': prazo, 'total': total})

            # Escrever Linha de Média Vendas
            mv_vista = (soma_v_vista / meses_v_mov) if meses_v_mov > 0 else 0
            mv_prazo = (soma_v_prazo / meses_v_mov) if meses_v_mov > 0 else 0
            mv_total = (soma_v_total / meses_v_mov) if meses_v_mov > 0 else 0
            
            ws.set_row(row, 28)
            ws.write(row, 0, "MÉDIA MENSAL", fmt['media_label'])
            ws.write(row, 1, mv_vista, fmt['media_money'])
            ws.write(row, 2, (mv_vista/mv_total) if mv_total else 0, fmt['media_percent'])
            ws.write(row, 3, mv_prazo, fmt['media_money'])
            ws.write(row, 4, (mv_prazo/mv_total) if mv_total else 0, fmt['media_percent'])
            ws.write(row, 5, mv_total, fmt['media_total'])
            row += 1

            # Escrever Meses Vendas
            for d in dados_processados_vendas:
                ws.write(row, 0, d['mes'], fmt['month_label'])
                ws.write(row, 1, d['vista'], fmt['money'])
                ws.write(row, 2, (d['vista']/d['total']) if d['total'] else 0, fmt['percent'])
                ws.write(row, 3, d['prazo'], fmt['money'])
                ws.write(row, 4, (d['prazo']/d['total']) if d['total'] else 0, fmt['percent'])
                ws.write(row, 5, d['total'], fmt['total_money'])
                row += 1

            # =================================================================
            # ESPAÇO ENTRE TABELAS
            # =================================================================
            row += 3 

            # =================================================================
            # PARTE 2: COMPRAS (PAGAR)
            # =================================================================
            ws.set_row(row, 35)
            ws.merge_range(row, 0, row, 5, "RELATÓRIO DE DESEMPENHO (COMPRAS)", fmt['main_title'])
            ws.set_row(row + 1, 8) 
            ws.merge_range(row + 1, 0, row + 1, 5, "", fmt['main_title_bar'])
            row += 2

            ws.set_row(row, 20)
            ws.merge_range(row, 0, row+1, 0, "PERÍODO", fmt['header_dark'])
            # Headers com cores diferentes para Compras
            ws.merge_range(row, 1, row, 2, "À VISTA (Caixa/Pix)", fmt['header_compra_vista'])
            ws.merge_range(row, 3, row, 4, "A PRAZO (Fornecedores/Contas)", fmt['header_compra_prazo'])
            ws.merge_range(row, 5, row+1, 5, "TOTAL GERAL", fmt['header_dark']) 
            
            ws.set_row(row+1, 20)
            ws.write(row+1, 1, "Valor (R$)", fmt['subheader'])
            ws.write(row+1, 2, "%", fmt['subheader'])
            ws.write(row+1, 3, "Valor (R$)", fmt['subheader'])
            ws.write(row+1, 4, "%", fmt['subheader'])
            row += 2

            # Processar Compras
            # Termos que indicam pagamento imediato/caixa nas despesas
            termos_compras = ['pix', 'dinheiro', 'especie', 'espécie', 'caixa', 'débito', 'saque', 'lanche', 'refeição']
            dados_processados_compras = []
            soma_c_vista, soma_c_prazo, soma_c_total, meses_c_mov = Decimal(0), Decimal(0), Decimal(0), 0

            todos_pagar = list(dados_pagar)

            for num_mes, nome_mes in meses_estrutura:
                vista, prazo, total = VendasExcelService._processar_dados_mes(todos_pagar, num_mes, termos_compras)
                
                if total > 0:
                    meses_c_mov += 1
                    soma_c_vista += vista
                    soma_c_prazo += prazo
                    soma_c_total += total

                dados_processados_compras.append({'mes': nome_mes, 'vista': vista, 'prazo': prazo, 'total': total})

            # Escrever Linha de Média Compras
            mc_vista = (soma_c_vista / meses_c_mov) if meses_c_mov > 0 else 0
            mc_prazo = (soma_c_prazo / meses_c_mov) if meses_c_mov > 0 else 0
            mc_total = (soma_c_total / meses_c_mov) if meses_c_mov > 0 else 0
            
            ws.set_row(row, 28)
            ws.write(row, 0, "MÉDIA MENSAL", fmt['media_label'])
            ws.write(row, 1, mc_vista, fmt['media_money'])
            ws.write(row, 2, (mc_vista/mc_total) if mc_total else 0, fmt['media_percent'])
            ws.write(row, 3, mc_prazo, fmt['media_money'])
            ws.write(row, 4, (mc_prazo/mc_total) if mc_total else 0, fmt['media_percent'])
            ws.write(row, 5, mc_total, fmt['media_total'])
            row += 1

            # Escrever Meses Compras
            for d in dados_processados_compras:
                ws.write(row, 0, d['mes'], fmt['month_label'])
                ws.write(row, 1, d['vista'], fmt['money'])
                ws.write(row, 2, (d['vista']/d['total']) if d['total'] else 0, fmt['percent'])
                ws.write(row, 3, d['prazo'], fmt['money'])
                ws.write(row, 4, (d['prazo']/d['total']) if d['total'] else 0, fmt['percent'])
                ws.write(row, 5, d['total'], fmt['total_money'])
                row += 1

        except Exception as e:
            print(f"Erro ao gerar relatório vendas/compras: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output