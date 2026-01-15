import xlsxwriter
from io import BytesIO
from decimal import Decimal
from django.db.models import Sum, F
from django.utils import timezone
from datetime import date

# Importação dos Models
from apps.financeiro.pagar.models import (
    Boleto, Cheque, FaturaCartao, GastoGeral, 
    ComissaoArquiteto, FolhaPagamento, Emprestimo
)

class RelatorioAnualConsolidado:
    def __init__(self, ano=None):
        self.ano = int(ano) if ano else timezone.now().year
        self.output = BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output, {'in_memory': True})
        self.worksheet = self.workbook.add_worksheet(f"Consolidado {self.ano}")
        
        # --- Formatações (Design) ---
        self.fmt_header = self.workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': '#4F81BD',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        self.fmt_bold = self.workbook.add_format({
            'bold': True, 'border': 1, 'align': 'left', 'valign': 'vcenter'
        })
        self.fmt_currency = self.workbook.add_format({
            'num_format': 'R$ #,##0.00', 'border': 1, 'align': 'right', 'valign': 'vcenter'
        })
        self.fmt_currency_bold = self.workbook.add_format({
            'num_format': 'R$ #,##0.00', 'bold': True, 'border': 1, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#D9D9D9'
        })
        self.fmt_total_label = self.workbook.add_format({
            'bold': True, 'border': 1, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#D9D9D9'
        })

    def get_valor_mes(self, model, mes):
        """
        Retorna a soma dos valores para um model em um mês específico,
        lidando dinamicamente com os nomes de campos diferentes de cada model.
        """
        
        # 1. Definição Padrão (Boleto, FaturaCartao, etc.)
        date_field = 'data_vencimento'
        value_field = 'valor'

        # 2. Adaptação por Tipo de Model
        if model == Cheque:
            date_field = 'data_emissao'
            value_field = 'valor'
        
        elif model == GastoGeral:
            date_field = 'data_gasto'
            value_field = 'valor_total'
            
        elif model == ComissaoArquiteto:
            date_field = 'data_vencimento'
            value_field = 'valor_comissao'
            
        elif model == Emprestimo:
            date_field = 'data_inicio'
            value_field = 'valor_total'
            
        elif model == FolhaPagamento:
            date_field = 'data_referencia'
            # Folha não tem um campo único de valor total salvo no banco, precisa somar os componentes
            filters = {
                f'{date_field}__year': self.ano,
                f'{date_field}__month': mes,
                'is_deleted': False
            }
            qs = model.objects.filter(**filters)
            # Soma dos campos que compõem o custo do funcionário (baseado na property total_funcionario)
            soma = qs.aggregate(
                total=Sum('salario_real') + 
                      Sum('ferias_terco') + 
                      Sum('empreitada') + 
                      Sum('decimo_terceiro') + 
                      Sum('horas_extras_valor')
            )['total']
            return soma or Decimal(0)

        # 3. Query Genérica para os outros casos
        filters = {
            f'{date_field}__year': self.ano,
            f'{date_field}__month': mes,
            'is_deleted': False
        }
        
        qs = model.objects.filter(**filters)
        soma = qs.aggregate(Sum(value_field))[f'{value_field}__sum']
        
        return soma or Decimal(0)

    def gerar(self):
        # 1. Configurar Colunas
        self.worksheet.set_column('A:A', 30) 
        self.worksheet.set_column('B:N', 15)

        # 2. Cabeçalho
        meses = [
            'JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
            'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'
        ]
        headers = ['TIPO DE DESPESA'] + meses + ['TOTAL ANUAL']
        
        for col_num, header in enumerate(headers):
            self.worksheet.write(0, col_num, header, self.fmt_header)

        # 3. Dados (Linhas)
        tipos_gastos = [
            ("Boletos", Boleto),
            ("Cheques", Cheque),
            ("Cartão de Crédito", FaturaCartao),
            ("Pix / Transferências / Gerais", GastoGeral),
            ("Comissões Arquitetos", ComissaoArquiteto),
            ("Folha de Pagamento", FolhaPagamento),
            ("Empréstimos", Emprestimo),
        ]

        row = 1
        totais_colunas = [Decimal(0)] * 13 

        for nome_gasto, model_class in tipos_gastos:
            self.worksheet.write(row, 0, nome_gasto, self.fmt_bold)
            
            total_linha = Decimal(0)
            
            for mes_idx in range(1, 13):
                valor = self.get_valor_mes(model_class, mes_idx)
                
                # Escreve o valor do mês
                self.worksheet.write(row, mes_idx, valor, self.fmt_currency)
                
                total_linha += valor
                totais_colunas[mes_idx-1] += valor
            
            # Escreve o Total da Linha
            self.worksheet.write(row, 13, total_linha, self.fmt_currency_bold)
            totais_colunas[12] += total_linha 
            
            row += 1

        # 4. Linha de Totais Gerais
        self.worksheet.write(row, 0, "TOTAL GERAL", self.fmt_total_label)
        
        for i, total in enumerate(totais_colunas):
            self.worksheet.write(row, i+1, total, self.fmt_currency_bold)

        self.workbook.close()
        self.output.seek(0)
        return self.output