import io
from decimal import Decimal
import xlsxwriter
from django.db.models import Sum

from apps.funcionarios.models import Funcionario
# Importação correta dos modelos
from .models import PagamentoFerias, PeriodoAquisitivo, RecibosContabilidade

try:
    from apps.banco_horas.models import BancoHoras
except ImportError:
    BancoHoras = None


class FeriasExcelService:
    # --- Paleta de Cores Profissional ---
    COR_TITULO_BG = '#2C3E50'       # Azul Petróleo Escuro
    COR_TITULO_TEXT = '#FFFFFF'     # Branco
    
    COR_HEADER_BG = '#34495E'       # Azul Petróleo
    COR_HEADER_TEXT = '#FFFFFF'     # Branco
    
    COR_SUBTITULO = '#2980B9'       # Azul Destaque
    
    COR_LINHA_PAR = '#FFFFFF'       # Branco
    COR_LINHA_IMPAR = '#F8F9F9'     # Cinza Muito Claro
    COR_BORDA = '#BDC3C7'           # Cinza para as bordas

    @classmethod
    def _define_formats(cls, workbook):
        # Base com text_wrap ativado para que textos longos "quebrem" para a linha de baixo
        base = {
            'font_name': 'Calibri', 
            'font_size': 10, 
            'valign': 'vcenter', 
            'border': 1, 
            'border_color': cls.COR_BORDA,
            'text_wrap': True 
        }
        
        return {
            'main_title': workbook.add_format({
                'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_TITULO_BG, 'font_color': cls.COR_TITULO_TEXT,
                'border': 1, 'border_color': cls.COR_TITULO_BG
            }),
            'section_title': workbook.add_format({
                'bold': True, 'font_size': 12, 'align': 'left', 'valign': 'vcenter',
                'font_color': cls.COR_SUBTITULO, 
                'bottom': 2, 'bottom_color': cls.COR_SUBTITULO
            }),
            'header': workbook.add_format({
                **base, 'bold': True, 'align': 'center', 
                'fg_color': cls.COR_HEADER_BG, 'font_color': cls.COR_HEADER_TEXT,
            }),
            'text_even': workbook.add_format({**base, 'align': 'left', 'fg_color': cls.COR_LINHA_PAR}),
            'text_odd': workbook.add_format({**base, 'align': 'left', 'fg_color': cls.COR_LINHA_IMPAR}),
            'center_even': workbook.add_format({**base, 'align': 'center', 'fg_color': cls.COR_LINHA_PAR}),
            'center_odd': workbook.add_format({**base, 'align': 'center', 'fg_color': cls.COR_LINHA_IMPAR}),
            'date_even': workbook.add_format({**base, 'align': 'center', 'num_format': 'dd/mm/yyyy', 'fg_color': cls.COR_LINHA_PAR}),
            'date_odd': workbook.add_format({**base, 'align': 'center', 'num_format': 'dd/mm/yyyy', 'fg_color': cls.COR_LINHA_IMPAR}),
            'money_even': workbook.add_format({**base, 'align': 'right', 'num_format': 'R$ #,##0.00', 'fg_color': cls.COR_LINHA_PAR}),
            'money_odd': workbook.add_format({**base, 'align': 'right', 'num_format': 'R$ #,##0.00', 'fg_color': cls.COR_LINHA_IMPAR}),
            'empty_msg': workbook.add_format({
                'font_name': 'Calibri', 'font_size': 10, 'italic': True, 'font_color': '#7F8C8D', 'text_wrap': False
            })
        }

    @staticmethod
    def gerar_relatorio_geral(ano):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet(f"Relatório Férias {ano}")
        
        ws.hide_gridlines(2)
        ws.freeze_panes(0, 1)

        fmt = FeriasExcelService._define_formats(workbook)

        # === CORREÇÃO DAS LARGURAS ===
        # Definindo tamanhos mais compactos. Onde tiver texto longo, o Excel vai
        # quebrar a linha automaticamente (text_wrap) em vez de alargar a coluna.
        
        ws.set_column('A:A', 25)  # Funcionário (Reduzido de 35)
        ws.set_column('B:B', 15)  # Datas
        ws.set_column('C:C', 18)  # Datas/Money (Reduzido drasticamente de 40)
        ws.set_column('D:D', 23)  # Período (dd/mm/aaaa a dd/mm/aaaa ocupa ~23 chars)
        ws.set_column('E:E', 14)  # Dias/Valores (Reduzido de 18)
        ws.set_column('F:F', 14)  # Recesso (Reduzido de 18)
        ws.set_column('G:G', 20)  # Carnaval/Obs (Reduzido de 40 -> Obs vai quebrar linha)
        ws.set_column('H:J', 13)  # Faltas/Gozo/Saldo (Reduzido de 18)
        ws.set_column('K:K', 40)  # Obs da Tabela 1 (Mantido largo pois é a principal obs)

        row = 1

        # === Título Geral ===
        ws.merge_range('A1:K1', f"RELATÓRIO GERAL DE FÉRIAS E PAGAMENTOS - {ano}", fmt['main_title'])
        ws.set_row(0, 30)
        row += 2

        # =====================================================
        # 1. CONTROLE DE FÉRIAS
        # =====================================================
        ws.write(row, 0, "1. CONTROLE DE PERÍODOS AQUISITIVOS", fmt['section_title'])
        row += 2

        headers_controle = [
            "Funcionário", "Adm. Contabil.", "Adm. Marcenaria", "Período Aquisitivo",
            "Dias Direito", "Recesso Final Ano", "Carnaval",
            "Faltas Justif.", "Total Gozados", "Saldo", "Observações"
        ]
        
        # Altura maior para cabeçalho permitir quebra de linha se necessário
        ws.set_row(row, 30) 
        for c, h in enumerate(headers_controle):
            ws.write(row, c, h, fmt['header'])
        row += 1

        periodos = PeriodoAquisitivo.objects.select_related(
            'funcionario', 'funcionario__dados_trabalhistas'
        ).prefetch_related('ferias_registradas').order_by('funcionario__nome')

        if not periodos:
            ws.write(row, 0, "Nenhum período aquisitivo encontrado.", fmt['empty_msg'])
            row += 1
        else:
            for idx, p in enumerate(periodos):
                suffix = '_odd' if idx % 2 else '_even'
                func = p.funcionario
                
                admissao_contab = None
                admissao_marc = None
                if hasattr(func, 'dados_trabalhistas'):
                    dt = func.dados_trabalhistas
                    admissao_contab = getattr(dt, 'data_admissao_contabilidade', getattr(dt, 'data_admissao', None))
                    admissao_marc = getattr(dt, 'data_admissao_marcenaria', None)

                total_recesso = sum(f.ferias_no_recesso_final_ano or 0 for f in p.ferias_registradas.all())
                total_carnaval = sum(f.ferias_no_carnaval or 0 for f in p.ferias_registradas.all())
                total_faltas = sum(f.faltas_justificadas_descontadas or 0 for f in p.ferias_registradas.all())
                
                obs_list = [f.observacoes for f in p.ferias_registradas.all() if f.observacoes]
                obs_str = "; ".join(obs_list) if obs_list else ""

                dados_linha = [
                    (func.nome, fmt[f'text{suffix}']),
                    (admissao_contab if admissao_contab else '-', fmt[f'date{suffix}']),
                    (admissao_marc if admissao_marc else '-', fmt[f'date{suffix}']),
                    (f"{p.data_inicio:%d/%m/%Y} a {p.data_fim:%d/%m/%Y}", fmt[f'center{suffix}']),
                    (p.dias_direito, fmt[f'center{suffix}']),
                    (total_recesso if total_recesso > 0 else "-", fmt[f'center{suffix}']),
                    (total_carnaval if total_carnaval > 0 else "-", fmt[f'center{suffix}']),
                    (total_faltas if total_faltas > 0 else "-", fmt[f'center{suffix}']),
                    (p.dias_gozados(), fmt[f'center{suffix}']),
                    (p.saldo_restante(), fmt[f'center{suffix}']),
                    (obs_str, fmt[f'text{suffix}'])
                ]

                for col, (valor, formato) in enumerate(dados_linha):
                    ws.write(row, col, valor, formato)
                row += 1

        row += 3

        # =====================================================
        # 2. PAGAMENTO DE 1/3 DE FÉRIAS
        # =====================================================
        ws.write(row, 0, "2. PAGAMENTOS REALIZADOS (1/3 FÉRIAS)", fmt['section_title'])
        row += 2

        headers_pgto = ["Funcionário", "Vencimento", "Salário Base", "Valor 1/3", "Data Pagamento", "Status", "Observações"]
        
        ws.set_row(row, 25)
        for c, h in enumerate(headers_pgto):
            ws.write(row, c, h, fmt['header'])
        row += 1

        pagamentos = PagamentoFerias.objects.select_related(
            'funcionario', 'funcionario__dados_trabalhistas'
        ).filter(data_pagamento__year=ano).order_by('data_pagamento')

        if not pagamentos:
            ws.write(row, 0, f"Nenhum pagamento registrado em {ano}.", fmt['empty_msg'])
            row += 1
        else:
            for idx, pg in enumerate(pagamentos):
                suffix = '_odd' if idx % 2 else '_even'
                
                salario = Decimal('0.00')
                if hasattr(pg.funcionario, 'dados_trabalhistas'):
                    salario = getattr(pg.funcionario.dados_trabalhistas, 'salario', Decimal('0.00')) or Decimal('0.00')
                
                status_display = pg.get_status_display() if hasattr(pg, 'get_status_display') else ''
                
                dados_linha = [
                    (pg.funcionario.nome, fmt[f'text{suffix}']),
                    (pg.vencimento, fmt[f'date{suffix}']),
                    (salario, fmt[f'money{suffix}']),
                    (pg.valor_a_pagar, fmt[f'money{suffix}']),
                    (pg.data_pagamento, fmt[f'date{suffix}']),
                    (status_display, fmt[f'center{suffix}']),
                    (pg.observacoes, fmt[f'text{suffix}']) # Vai usar quebra de linha (G = 20)
                ]

                for col, (valor, formato) in enumerate(dados_linha):
                    ws.write(row, col, valor, formato)
                row += 1

        row += 3

        # =====================================================
        # 3. BANCO DE HORAS
        # =====================================================
        ws.write(row, 0, "3. SALDO DE BANCO DE HORAS", fmt['section_title'])
        row += 2

        if BancoHoras:
            headers_bh = ["Funcionário", "Saldo Atual (Horas)"]
            
            ws.set_row(row, 25)
            for c, h in enumerate(headers_bh):
                ws.write(row, c, h, fmt['header'])
            row += 1

            bancos = BancoHoras.objects.select_related('funcionario').all().order_by('funcionario__nome')
            
            if not bancos:
                ws.write(row, 0, "Nenhum registro de banco de horas.", fmt['empty_msg'])
                row += 1
            else:
                for idx, b in enumerate(bancos):
                    suffix = '_odd' if idx % 2 else '_even'
                    horas = b.saldo if hasattr(b, 'saldo') else 0
                    
                    dados_linha = [
                        (b.funcionario.nome, fmt[f'text{suffix}']),
                        (horas, fmt[f'center{suffix}'])
                    ]
                    
                    for col, (valor, formato) in enumerate(dados_linha):
                        ws.write(row, col, valor, formato)
                    row += 1
        else:
            ws.write(row, 0, "Módulo de Banco de Horas não instalado.", fmt['empty_msg'])
            row += 1

        row += 3

        # =====================================================
        # 4. RECIBOS DA CONTABILIDADE
        # =====================================================
        ws.write(row, 0, "4. RECIBOS DE FÉRIAS (CONTABILIDADE)", fmt['section_title'])
        row += 2

        headers_recibos = ["Funcionário", "Data do Recibo", "Observações"]
        
        ws.set_row(row, 25)
        for c, h in enumerate(headers_recibos):
            ws.write(row, c, h, fmt['header'])
        row += 1

        try:
            recibos = RecibosContabilidade.objects.select_related('funcionario').all().order_by('-recibo_de_ferias_contabilidade')
            
            if not recibos:
                ws.write(row, 0, "Nenhum recibo registrado.", fmt['empty_msg'])
                row += 1
            else:
                for idx, r in enumerate(recibos):
                    suffix = '_odd' if idx % 2 else '_even'
                    
                    dados_linha = [
                        (r.funcionario.nome, fmt[f'text{suffix}']),
                        (r.recibo_de_ferias_contabilidade, fmt[f'date{suffix}']),
                        (r.observacoes, fmt[f'text{suffix}']) # Vai usar quebra de linha (C = 18)
                    ]
                    
                    for col, (valor, formato) in enumerate(dados_linha):
                        ws.write(row, col, valor, formato)
                    row += 1
        except Exception:
            ws.write(row, 0, "Tabela de recibos indisponível.", fmt['empty_msg'])
            row += 1

        workbook.close()
        output.seek(0)
        return output