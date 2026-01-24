import xlsxwriter
from io import BytesIO
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from datetime import date

from apps.financeiro.pagar.models import (
    Boleto, Cheque, FaturaCartao, GastoGeral, 
    ComissaoArquiteto, FolhaPagamento, Emprestimo
)

class RelatorioAnualConsolidado:
    def __init__(self, ano=None, inicio=None, fim=None, workbook=None):
        if inicio and fim:
            self.inicio = inicio
            self.fim = fim
            self.ano = inicio.year
        else:
            self.ano = int(ano) if ano else timezone.now().year
            self.inicio = date(self.ano, 1, 1)
            self.fim = date(self.ano, 12, 31)

        if workbook:
            self.workbook = workbook
            self.should_close = False
        else:
            self.output = BytesIO()
            self.workbook = xlsxwriter.Workbook(self.output, {'in_memory': True})
            self.should_close = True

        self.worksheet = self.workbook.add_worksheet(f"Consolidado {self.ano}")

        # 🔹 AUMENTA ALTURA PADRÃO DAS LINHAS
        self.worksheet.set_default_row(21)

        # --- Formatações ---
        self.fmt_header_month = self.workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': '#4F81BD',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        self.fmt_subheader = self.workbook.add_format({
            'bold': True, 'font_size': 9, 'bg_color': '#DCE6F1',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        self.fmt_bold = self.workbook.add_format({
            'bold': True, 'border': 1, 'align': 'left', 'valign': 'vcenter'
        })
        self.fmt_currency = self.workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'align': 'right', 'valign': 'vcenter', 'font_size': 9
        })
        self.fmt_currency_paid = self.workbook.add_format({
            'num_format': '#,##0.00', 'border': 1, 'align': 'right', 'valign': 'vcenter',
            'font_size': 9, 'font_color': '#006100'
        })
        self.fmt_total_col = self.workbook.add_format({
            'bold': True, 'num_format': 'R$ #,##0.00', 'border': 1,
            'align': 'right', 'valign': 'vcenter', 'bg_color': '#D9D9D9'
        })

    def gerar(self):
        # 1. Colunas
        self.worksheet.set_column('A:A', 25)
        self.worksheet.set_column(1, 26, 11)

        # 🔹 AUMENTA ALTURA DOS CABEÇALHOS
        self.worksheet.set_row(0, 26)
        self.worksheet.set_row(1, 22)

        meses = [
            'JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
            'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'
        ]

        # Cabeçalhos
        self.worksheet.merge_range(0, 0, 1, 0, 'TIPO DE DESPESA', self.fmt_header_month)

        col = 1
        for mes in meses:
            self.worksheet.merge_range(0, col, 0, col+1, mes, self.fmt_header_month)
            self.worksheet.write(1, col, "Valor", self.fmt_subheader)
            self.worksheet.write(1, col+1, "Pago", self.fmt_subheader)
            col += 2

        self.worksheet.merge_range(0, col, 0, col+1, "TOTAL PERÍODO", self.fmt_header_month)
        self.worksheet.write(1, col, "Valor", self.fmt_subheader)
        self.worksheet.write(1, col+1, "Pago", self.fmt_subheader)

        tipos_gastos = [
            ("Boletos", Boleto),
            ("Cheques", Cheque),
            ("Cartão de Crédito", FaturaCartao),
            ("Pix / Gerais", GastoGeral),
            ("Comissões Arquitetos", ComissaoArquiteto),
            ("Folha de Pagamento", FolhaPagamento),
            ("Empréstimos", Emprestimo),
        ]

        row = 2
        totais_verticais = [Decimal(0)] * 26

        for nome_gasto, model_class in tipos_gastos:
            # 🔹 AUMENTA ALTURA DAS LINHAS DE DADOS
            self.worksheet.set_row(row, 18)

            self.worksheet.write(row, 0, nome_gasto, self.fmt_bold)

            total_linha_nom = Decimal(0)
            total_linha_pg = Decimal(0)

            col_idx = 1
            for mes_idx in range(1, 13):
                valor_nom, valor_pg = self.get_valores_mes(model_class, mes_idx)

                self.worksheet.write(row, col_idx, valor_nom, self.fmt_currency)
                totais_verticais[col_idx-1] += valor_nom

                self.worksheet.write(row, col_idx+1, valor_pg, self.fmt_currency_paid)
                totais_verticais[col_idx] += valor_pg

                total_linha_nom += valor_nom
                total_linha_pg += valor_pg

                col_idx += 2

            self.worksheet.write(row, col_idx, total_linha_nom, self.fmt_total_col)
            self.worksheet.write(row, col_idx+1, total_linha_pg, self.fmt_total_col)

            totais_verticais[col_idx-1] += total_linha_nom
            totais_verticais[col_idx] += total_linha_pg

            row += 1

        # Total Geral
        self.worksheet.set_row(row, 20)
        self.worksheet.write(row, 0, "TOTAL GERAL", self.fmt_total_col)

        for i, total in enumerate(totais_verticais):
            self.worksheet.write(row, i+1, total, self.fmt_total_col)

        if self.should_close:
            self.workbook.close()
            self.output.seek(0)
            return self.output
