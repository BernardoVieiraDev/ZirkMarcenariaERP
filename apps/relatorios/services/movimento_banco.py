import io
import xlsxwriter
import calendar
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.financeiro.receber.models import Banco, MovimentoBanco

class MovimentoBancoExcelService:
    # --- Paleta de Cores (Estilo Visual Unificado) ---
    COR_TITULO_BG = '#2C3E50'       
    COR_TITULO_TEXTO = '#FFFFFF'    
    
    COR_SUBTITULO_BG = '#ECF0F1'
    COR_SUBTITULO_TEXT = '#7F8C8D'

    COR_TABLE_HEADER_BG = '#34495E' 
    COR_TABLE_HEADER_TEXT = '#FFFFFF'
    
    # Entradas (Verde)
    COR_HEADER_ENTRADA = '#27AE60'
    COR_BG_ENTRADA = '#E9F7EF'
    COR_TEXT_ENTRADA = '#145A32'
    
    # Saídas (Vermelho)
    COR_HEADER_SAIDA = '#C0392B'
    COR_BG_SAIDA = '#F9EBEA'
    COR_TEXT_SAIDA = '#7B241C'
    
    # Saldo
    COR_SALDO_BG = '#D6EAF8'        
    COR_SALDO_TEXT = '#2980B9'
    
    COR_LINHA_DIVISORIA = '#BDC3C7'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        font_base = {'font_name': 'Calibri', 'valign': 'vcenter', 'font_size': 10}
        
        def create_fmt(updates):
            f = font_base.copy()
            f.update(updates)
            return workbook.add_format(f)

        return {
            'main_title': create_fmt({
                'bold': True, 'font_size': 16, 'align': 'left', 'indent': 1,
                'font_color': cls.COR_TITULO_TEXTO, 'bg_color': cls.COR_TITULO_BG,
                'border': 1, 'border_color': cls.COR_TITULO_BG
            }),
            'info_banco': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'left', 'indent': 1,
                'font_color': cls.COR_SUBTITULO_TEXT, 'bg_color': cls.COR_SUBTITULO_BG,
                'border': 1, 'border_color': '#BDC3C7'
            }),
            'section_title': create_fmt({
                'bold': True, 'font_size': 11, 'align': 'left',
                'font_color': '#2C3E50', 'bottom': 2, 'bottom_color': '#34495E'
            }),
            
            # --- Resumo ---
            'resumo_label': create_fmt({
                'bold': True, 'align': 'left', 'indent': 1,
                'bg_color': '#ECF0F1', 'font_color': '#7F8C8D',
                'border': 1, 'border_color': '#BDC3C7'
            }),
            'resumo_value': create_fmt({
                'bold': True, 'align': 'right', 'num_format': 'R$ #,##0.00',
                'bg_color': '#FFFFFF', 'font_color': '#2C3E50',
                'border': 1, 'border_color': '#BDC3C7', 'indent': 1
            }),
            'resumo_saldo_label': create_fmt({
                'bold': True, 'align': 'left', 'indent': 1,
                'bg_color': cls.COR_SALDO_BG, 'font_color': cls.COR_SALDO_TEXT,
                'border': 1, 'border_color': '#BDC3C7'
            }),
            'resumo_saldo_value': create_fmt({
                'bold': True, 'align': 'right', 'num_format': 'R$ #,##0.00',
                'bg_color': cls.COR_SALDO_BG, 'font_color': cls.COR_SALDO_TEXT,
                'border': 1, 'border_color': '#BDC3C7', 'indent': 1
            }),

            # --- Headers Tabela ---
            'header_base': create_fmt({
                'bold': True, 'font_size': 10, 'align': 'center',
                'bg_color': cls.COR_TABLE_HEADER_BG, 'font_color': cls.COR_TABLE_HEADER_TEXT,
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            'header_entrada': create_fmt({
                'bold': True, 'font_size': 10, 'align': 'center',
                'bg_color': cls.COR_HEADER_ENTRADA, 'font_color': '#FFFFFF',
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),
            'header_saida': create_fmt({
                'bold': True, 'font_size': 10, 'align': 'center',
                'bg_color': cls.COR_HEADER_SAIDA, 'font_color': '#FFFFFF',
                'border': 1, 'border_color': cls.COR_LINHA_DIVISORIA
            }),

            # --- Células Dados ---
            'cell_date': create_fmt({
                'align': 'center', 'num_format': 'dd/mm/yyyy',
                'bottom': 1, 'bottom_color': '#BDC3C7', 
                'right': 1, 'right_color': '#BDC3C7',
                'bg_color': '#FDFEFE'
            }),
            
            # Colunas Entrada
            'cell_desc_in': create_fmt({
                'align': 'left', 'text_wrap': True,
                'bottom': 1, 'bottom_color': '#D5D8DC', 
                'right': 1, 'right_color': '#D5D8DC',
                'bg_color': cls.COR_BG_ENTRADA, 'font_color': cls.COR_TEXT_ENTRADA
            }),
            'cell_val_in': create_fmt({
                'align': 'right', 'num_format': '#,##0.00',
                'bottom': 1, 'bottom_color': '#D5D8DC', 
                'right': 1, 'right_color': '#BDC3C7', # Divisória forte no meio
                'bg_color': cls.COR_BG_ENTRADA, 'font_color': cls.COR_TEXT_ENTRADA,
                'bold': True
            }),

            # Colunas Saída
            'cell_desc_out': create_fmt({
                'align': 'left', 'text_wrap': True,
                'bottom': 1, 'bottom_color': '#D5D8DC', 
                'right': 1, 'right_color': '#D5D8DC',
                'bg_color': cls.COR_BG_SAIDA, 'font_color': cls.COR_TEXT_SAIDA
            }),
            'cell_val_out': create_fmt({
                'align': 'right', 'num_format': '#,##0.00',
                'bottom': 1, 'bottom_color': '#D5D8DC', 
                'right': 1, 'right_color': '#BDC3C7',
                'bg_color': cls.COR_BG_SAIDA, 'font_color': cls.COR_TEXT_SAIDA,
                'bold': True
            }),
            
            # Vazios (traços para dias sem movimento)
            'cell_empty_in': create_fmt({'align': 'center', 'bg_color': '#F8F9F9', 'bottom': 1, 'bottom_color': '#D5D8DC', 'right': 1, 'right_color': '#BDC3C7'}),
            'cell_empty_out': create_fmt({'align': 'center', 'bg_color': '#F8F9F9', 'bottom': 1, 'bottom_color': '#D5D8DC'}),
        }

    @staticmethod
    def gerar_excel(banco, movimentacoes, resumo_dados, ano, mes, workbook=None):
        output = None
        should_close = False

        # Se não passar workbook, cria um novo em memória (Modo Individual)
        # Se passar, usa o existente (Modo Pacote) e NÃO fecha ao final
        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        # IMPORTANTE: Definir os formatos usando o workbook atual
        fmt = MovimentoBancoExcelService._define_formats(workbook)

        # Nome da aba dinâmico para evitar conflito no pacote com múltiplos bancos
        # Excel limita nomes de abas a 31 caracteres
        nome_aba = f"Ext {banco.nome}"[:31]
        
        ws = workbook.add_worksheet(nome_aba)
        ws.hide_gridlines(2)
        
        # Configuração de Colunas (Layout Lado a Lado)
        # A: Data | B: Desc Ent | C: Val Ent || D: Desc Sai | E: Val Sai
        ws.set_column('A:A', 14) # Data# type: ignore
        ws.set_column('B:B', 35) # Descrição Entrada# type: ignore
        ws.set_column('C:C', 16) # Valor Entrada# type: ignore
        ws.set_column('D:D', 35) # Descrição Saída# type: ignore
        ws.set_column('E:E', 16) # Valor Saída# type: ignore

        row = 1
        
        # --- Título ---
        ws.set_row(row, 30)
        ws.merge_range(row, 0, row, 4, f" EXTRATO BANCÁRIO - {banco.nome.upper()}", fmt['main_title'])
        row += 1
        
        # --- Subtítulo (Agência/Conta) ---
        ws.set_row(row, 20)
        info_conta = f" Agência: {banco.agencia} | Conta: {banco.conta}"
        ws.merge_range(row, 0, row, 4, info_conta, fmt['info_banco'])
        row += 2

        # --- Resumo (Topo) ---
        ws.write(row, 0, "RESUMO DO MÊS", fmt['section_title'])
        row += 1
        
        # Saldo Anterior
        ws.write(row, 0, "Saldo Anterior", fmt['resumo_label'])
        ws.write(row, 1, resumo_dados['saldo_anterior'], fmt['resumo_value'])
        
        # Entradas
        ws.write(row+1, 0, "Total Entradas (+)", fmt['resumo_label'])
        ws.write(row+1, 1, resumo_dados['total_entradas'], fmt['resumo_value'])
        
        # Saídas
        ws.write(row+2, 0, "Total Saídas (-)", fmt['resumo_label'])
        ws.write(row+2, 1, resumo_dados['total_saidas'], fmt['resumo_value'])
        
        # Saldo Atual
        ws.write(row+3, 0, "SALDO FINAL", fmt['resumo_saldo_label'])
        ws.write(row+3, 1, resumo_dados['saldo_atual'], fmt['resumo_saldo_value'])
        
        row += 5 

        # --- Cabeçalho Tabela ---
        ws.set_row(row, 25)
        ws.write(row, 0, "DATA", fmt['header_base'])
        ws.write(row, 1, "HISTÓRICO ENTRADA", fmt['header_entrada'])
        ws.write(row, 2, "VALOR (R$)", fmt['header_entrada'])
        ws.write(row, 3, "HISTÓRICO SAÍDA", fmt['header_saida'])
        ws.write(row, 4, "VALOR (R$)", fmt['header_saida'])
        
        row += 1
        
        # --- Processamento dos Dias ---
        
        # 1. Agrupar por data e separar tipos
        mapa_movimentacoes = {}
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        
        # Inicializa todos os dias do mês
        for dia in range(1, ultimo_dia + 1):
            data_atual = date(ano, mes, dia)
            mapa_movimentacoes[data_atual] = {'E': [], 'S': []}


        for item in movimentacoes:
            if item.data in mapa_movimentacoes:
                # 1. Tratamento da Descrição
                desc = getattr(item, 'historico', getattr(item, 'descricao', 'Movimento'))
                obs = getattr(item, 'observacoes', None)
                if obs:
                    desc += f" ({obs})"
                
                # 2. Tratamento do Tipo
                tipo_real = item.tipo
                
                # Mapeia tipos legados/incorretos se existirem
                if tipo_real == 'C': # Crédito -> Entrada
                    tipo_real = 'E'
                elif tipo_real == 'D': # Débito -> Saída
                    tipo_real = 'S'
                
                # Só adiciona se o tipo for válido (E ou S)
                if tipo_real in mapa_movimentacoes[item.data]:
                    mapa_movimentacoes[item.data][tipo_real].append((desc, item.valor))

        # 2. Renderizar linhas
        for dia in range(1, ultimo_dia + 1):
            data_atual = date(ano, mes, dia)
            dados = mapa_movimentacoes[data_atual]
            
            entradas = dados['E']
            saidas = dados['S']
            
            # Descobre quantas linhas esse dia vai ocupar (o maior entre qtd entradas e saídas)
            n_linhas = max(len(entradas), len(saidas), 1) 
            
            # Se for dia vazio, imprime traços
            if not entradas and not saidas:
                ws.write(row, 0, data_atual, fmt['cell_date'])
                ws.write(row, 1, "-", fmt['cell_empty_in'])
                ws.write(row, 2, "-", fmt['cell_empty_in'])
                ws.write(row, 3, "-", fmt['cell_empty_out'])
                ws.write(row, 4, "-", fmt['cell_empty_out'])
                row += 1
                continue

            # Se tiver dados, itera as linhas necessárias
            # Mescla a célula da data se houver mais de uma linha para o mesmo dia
            if n_linhas > 1:
                ws.merge_range(row, 0, row + n_linhas - 1, 0, data_atual, fmt['cell_date'])
            else:
                ws.write(row, 0, data_atual, fmt['cell_date'])

            for i in range(n_linhas):
                # Coluna Entrada
                if i < len(entradas):
                    desc, val = entradas[i]
                    ws.write(row, 1, desc, fmt['cell_desc_in'])
                    ws.write(row, 2, val, fmt['cell_val_in'])
                else:
                    # Espaço vazio na coluna de entrada (com formatação verde clara)
                    ws.write(row, 1, "", fmt['cell_desc_in'])
                    ws.write(row, 2, "", fmt['cell_val_in'])

                # Coluna Saída
                if i < len(saidas):
                    desc, val = saidas[i]
                    ws.write(row, 3, desc, fmt['cell_desc_out'])
                    ws.write(row, 4, val, fmt['cell_val_out'])
                else:
                    # Espaço vazio na coluna de saída (com formatação vermelha clara)
                    ws.write(row, 3, "", fmt['cell_desc_out'])
                    ws.write(row, 4, "", fmt['cell_val_out'])
                
                row += 1

        # Linha final para fechar a borda inferior visualmente
        border_top = workbook.add_format({'top': 1, 'top_color': '#BDC3C7'})
        for col in range(5):
            ws.write(row, col, "", border_top)

        # Só fecha e retorna o output se fomos nós que criamos o workbook
        if should_close:
            workbook.close()
            assert output is not None
            output.seek(0)
            return output
        
        return None


def gerar_relatorio_movimento_banco(ano, mes, banco_id):
    """
    Função principal chamada pela View.
    Recupera dados e chama o serviço de Excel.
    """
    # 1. Recuperar o Banco
    try:
        banco = Banco.objects.get(pk=banco_id)
    except Banco.DoesNotExist:
        return None

    # 2. Dados do Período
    data_inicio = date(ano, mes, 1)
    
    # 3. Cálculo do Saldo Anterior (Tudo antes do dia 01/mes)
    # Importante: Usamos Decimal(0) para evitar erro de tipos mistos no Django 5+
    entradas_ant = MovimentoBanco.objects.filter(
        banco=banco, 
        data__lt=data_inicio, 
        tipo='E'
    ).aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    
    saidas_ant = MovimentoBanco.objects.filter(
        banco=banco, 
        data__lt=data_inicio, 
        tipo='S'
    ).aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    
    saldo_anterior = banco.saldo_inicial + entradas_ant - saidas_ant

    # 4. Movimentações do Mês
    movimentacoes = MovimentoBanco.objects.filter(
        banco=banco, 
        data__year=ano, 
        data__month=mes
    ).order_by('data')
    
    # Totais do Mês
    total_entradas = sum(m.valor for m in movimentacoes if m.tipo == 'E')
    total_saidas = sum(m.valor for m in movimentacoes if m.tipo == 'S')
    saldo_atual = saldo_anterior + total_entradas - total_saidas

    # Prepara dicionário de resumo para o Excel
    resumo_dados = {
        'saldo_anterior': saldo_anterior,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_atual': saldo_atual
    }

    # 5. Gerar Excel
    return MovimentoBancoExcelService.gerar_excel(banco, movimentacoes, resumo_dados, ano, mes)