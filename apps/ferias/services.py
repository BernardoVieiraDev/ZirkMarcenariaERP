import io
from decimal import Decimal
import xlsxwriter
from django.db.models import Sum

from apps.funcionarios.models import Funcionario
# Importação correta dos modelos (Certifique-se que o models.py não tem erro)
from .models import PagamentoFerias, PeriodoAquisitivo, RecibosContabilidade

# Tenta importar o Banco de Horas
try:
    from apps.banco_horas.models import BancoHoras
except ImportError:
    BancoHoras = None


class FeriasExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_TEXTO_BRANCO = '#FFFFFF'

    @classmethod
    def _get_formats(cls, wb):
        return {
            'header': wb.add_format({
                'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': cls.COR_TEXTO_BRANCO,
                'font_name': 'Arial', 'border': 1, 'text_wrap': True
            }),
            'title': wb.add_format({
                'bold': True, 'font_size': 14, 'align': 'left', 'valign': 'vcenter',
                'font_name': 'Arial'
            }),
            'text': wb.add_format({
                'font_size': 10, 'align': 'left', 'valign': 'vcenter',
                'font_name': 'Arial', 'border': 1
            }),
            'center': wb.add_format({
                'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                'font_name': 'Arial', 'border': 1
            }),
            'date': wb.add_format({
                'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                'font_name': 'Arial', 'num_format': 'dd/mm/yyyy', 'border': 1
            }),
            'money': wb.add_format({
                'font_size': 10, 'align': 'right', 'valign': 'vcenter',
                'font_name': 'Arial', 'num_format': 'R$ #,##0.00', 'border': 1
            }),
        }

    @staticmethod
    def _ajustar_colunas(ws, col_widths):
        for col, length in col_widths.items():
            ws.set_column(col, col, max(12, min(length + 2, 60)))

    @staticmethod
    def gerar_relatorio_geral(ano):
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet(f"Geral {ano}")
        fmt = FeriasExcelService._get_formats(wb)

        col_widths = {}
        def update_width(col, value):
            size = len(str(value)) if value else 0
            col_widths[col] = max(col_widths.get(col, 0), size)

        row = 0

        # =====================================================
        # 1. CONTROLE DE FÉRIAS
        # =====================================================
        ws.write(row, 0, f"PLANILHA DE CONTROLE DE FÉRIAS {ano}", fmt['title'])
        row += 2
        
        # ... (CÓDIGO DA SEÇÃO 1 IGUAL AO ORIGINAL) ...
        # (Copie o bloco headers_controle e o loop periodos)
        headers_controle = [
            "Funcionário", "Admissão Contabilidade", "Admissão Marcenaria", "Período Aquisitivo",
            "Dias de Direito", "Férias tiradas no final do ano", "Férias tiradas no carnaval",
            "Faltas justificadas descontadas", "Total Dias Gozados", "Saldo", "Observações"
        ]
        for c, h in enumerate(headers_controle):
            ws.write(row, c, h, fmt['header'])
            update_width(c, h)

        periodos = PeriodoAquisitivo.objects.select_related('funcionario', 'funcionario__dados_trabalhistas').prefetch_related('ferias_registradas').order_by('funcionario__nome')
        row += 1
        for p in periodos:
            # ... (Logica de calculo existente) ...
            func = p.funcionario
            admissao_contabilidade = None
            if hasattr(func, 'dados_trabalhistas'):
                admissao_contabilidade = getattr(func.dados_trabalhistas, 'data_admissao_contabilidade', getattr(func.dados_trabalhistas, 'data_admissao', None))
            admissao_marcenaria = None
            if hasattr(func, 'dados_trabalhistas'):
                 admissao_marcenaria = getattr(func.dados_trabalhistas, 'data_admissao_marcenaria', None)
            
            total_recesso = sum(f.ferias_no_recesso_final_ano or 0 for f in p.ferias_registradas.all())
            total_carnaval = sum(f.ferias_no_carnaval or 0 for f in p.ferias_registradas.all())
            total_faltas = sum(f.faltas_justificadas_descontadas or 0 for f in p.ferias_registradas.all())
            obs = "; ".join(f.observacoes for f in p.ferias_registradas.all() if f.observacoes)

            dados = [
                func.nome, admissao_contabilidade, admissao_marcenaria,
                f"{p.data_inicio:%d/%m/%Y} a {p.data_fim:%d/%m/%Y}", p.dias_direito,
                total_recesso if total_recesso > 0 else "-", total_carnaval if total_carnaval > 0 else "-",
                total_faltas if total_faltas > 0 else "-", p.dias_gozados(), p.saldo_restante(), obs
            ]
            formatos = [fmt['text'], fmt['date'], fmt['date'], fmt['center'], fmt['center'], fmt['center'], fmt['center'], fmt['center'], fmt['center'], fmt['center'], fmt['text']]
            for c, (val, f) in enumerate(zip(dados, formatos)):
                ws.write(row, c, val, f)
                update_width(c, val)
            row += 1


        # =====================================================
        # 2. PAGAMENTO DE 1/3 DE FÉRIAS
        # =====================================================
        row += 3
        ws.write(row, 0, "PAGAMENTOS 1/3 DAS FÉRIAS", fmt['title'])
        row += 2
        
        # ... (CÓDIGO DA SEÇÃO 2 IGUAL AO ORIGINAL) ...
        headers_pgto = ["Funcionário", "Vencimento", "Salário Base", "Valor 1/3", "Data Pagamento", "Status", "Observações"]
        for c, h in enumerate(headers_pgto):
            ws.write(row, c, h, fmt['header'])
            update_width(c, h)
        
        pagamentos = PagamentoFerias.objects.select_related('funcionario', 'funcionario__dados_trabalhistas').filter(data_pagamento__year=ano).order_by('data_pagamento')
        row += 1
        for pg in pagamentos:
            salario = Decimal('0.00')
            if hasattr(pg.funcionario, 'dados_trabalhistas'):
                salario = getattr(pg.funcionario.dados_trabalhistas, 'salario', Decimal('0.00')) or Decimal('0.00')
            status = pg.get_status_display() if hasattr(pg, 'get_status_display') else ''
            dados = [pg.funcionario.nome, pg.vencimento, salario, pg.valor_a_pagar, pg.data_pagamento, status, pg.observacoes]
            formatos = [fmt['text'], fmt['date'], fmt['money'], fmt['money'], fmt['date'], fmt['center'], fmt['text']]
            for c, (val, f) in enumerate(zip(dados, formatos)):
                ws.write(row, c, val, f)
                update_width(c, val)
            row += 1

        # =====================================================
        # 3. (REMOVIDO DAQUI - AGORA SERÁ O ITEM 5)
        # =====================================================

        # =====================================================
        # 4. BANCO DE HORAS
        # =====================================================
        row += 3
        ws.write(row, 0, "BANCO DE HORAS", fmt['title'])
        row += 2

        headers_bh = ["Funcionário", "Saldo (Horas)"]
        for c, h in enumerate(headers_bh):
            ws.write(row, c, h, fmt['header'])
            update_width(c, h)

        if BancoHoras:
            bancos = BancoHoras.objects.select_related('funcionario').all()
            row += 1
            for b in bancos:
                horas = b.saldo if hasattr(b, 'saldo') else 0
                dados = [b.funcionario.nome, horas]
                formatos = [fmt['text'], fmt['center']]
                for c, (val, f) in enumerate(zip(dados, formatos)):
                    ws.write(row, c, val, f)
                    update_width(c, val)
                row += 1
        else:
            row += 1
            ws.write(row, 0, "Módulo Banco de Horas não instalado.", fmt['text'])

        # =====================================================
        # 5. RECIBOS DA CONTABILIDADE (NOVA POSIÇÃO)
        # =====================================================
        row += 3
        ws.write(row, 0, "RECIBOS DA CONTABILIDADE", fmt['title'])
        row += 2

        headers_recibos = ["Funcionário", "Recibo de Férias Contabilidade", "Observações"]
        for c, h in enumerate(headers_recibos):
            ws.write(row, c, h, fmt['header'])
            update_width(c, h)

        try:
            recibos = RecibosContabilidade.objects.select_related('funcionario').all().order_by('-recibo_de_ferias_contabilidade')
            row += 1
            for r in recibos:
                dados = [r.funcionario.nome, r.recibo_de_ferias_contabilidade, r.observacoes]
                formatos = [fmt['text'], fmt['date'], fmt['text']]
                for c, (val, f) in enumerate(zip(dados, formatos)):
                    ws.write(row, c, val, f)
                    update_width(c, val)
                row += 1
        except Exception:
            row += 1
            ws.write(row, 0, "Tabela de recibos vazia ou não migrada.", fmt['text'])


        FeriasExcelService._ajustar_colunas(ws, col_widths)
        wb.close()
        output.seek(0)
        return output