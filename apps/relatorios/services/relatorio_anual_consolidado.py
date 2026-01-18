import xlsxwriter
from io import BytesIO
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from datetime import date

# Importação dos Models
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
            'num_format': '#,##0.00', 'border': 1, 'align': 'right', 'valign': 'vcenter', 'font_size': 9, 'font_color': '#006100'
        })
        self.fmt_total_col = self.workbook.add_format({
            'bold': True, 'num_format': 'R$ #,##0.00', 'border': 1, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#D9D9D9'
        })

    def get_valores_mes(self, model, mes):
        """
        Retorna uma tupla (valor_nominal, valor_pago) para o mês especificado.
        """
        filters = {'is_deleted': False}
        
        # --- Lógica por Model ---
        
        if model == Boleto:
            # Vencimento
            filters['data_vencimento__range'] = [self.inicio, self.fim]
            filters['data_vencimento__month'] = mes
            qs = model.objects.filter(**filters)
            agg = qs.aggregate(nom=Sum('valor'), pg=Sum('valor_pago'))
            return (agg['nom'] or Decimal(0), agg['pg'] or Decimal(0))
            
        elif model == ComissaoArquiteto:
            # Alterado para Data de Vencimento para mostrar o "A Pagar"
            filters['data_vencimento__range'] = [self.inicio, self.fim]
            filters['data_vencimento__month'] = mes
            qs = model.objects.filter(**filters)
            agg = qs.aggregate(nom=Sum('valor_comissao'), pg=Sum('valor_pago'))
            return (agg['nom'] or Decimal(0), agg['pg'] or Decimal(0))

        elif model == FaturaCartao:
            # Data Vencimento. Não tem campo 'valor_pago' explícito, baseia-se no status.
            filters['data_vencimento__range'] = [self.inicio, self.fim]
            filters['data_vencimento__month'] = mes
            qs = model.objects.filter(**filters)
            
            nominal = qs.aggregate(s=Sum('valor'))['s'] or Decimal(0)
            pago = qs.filter(status__in=['Pago', 'PAGO', 'Recebido']).aggregate(s=Sum('valor'))['s'] or Decimal(0)
            return (nominal, pago)

        elif model == Cheque:
            # Data Emissão
            filters['data_emissao__range'] = [self.inicio, self.fim]
            filters['data_emissao__month'] = mes
            qs = model.objects.filter(**filters)
            
            nominal = qs.aggregate(s=Sum('valor'))['s'] or Decimal(0)
            pago = qs.filter(status__in=['Pago', 'Compensado']).aggregate(s=Sum('valor'))['s'] or Decimal(0)
            return (nominal, pago)

        elif model == GastoGeral:
            # Data Gasto
            filters['data_gasto__range'] = [self.inicio, self.fim]
            filters['data_gasto__month'] = mes
            qs = model.objects.filter(**filters)
            
            nominal = qs.aggregate(s=Sum('valor_total'))['s'] or Decimal(0)
            # Geralmente gasto geral nasce pago, mas respeita status se houver
            pago = qs.filter(status__in=['Pago', 'PAGO']).aggregate(s=Sum('valor_total'))['s'] or Decimal(0)
            return (nominal, pago)
            
        elif model == Emprestimo:
            # Data Inicio (Contração do Empréstimo)
            filters['data_inicio__range'] = [self.inicio, self.fim]
            filters['data_inicio__month'] = mes
            qs = model.objects.filter(**filters)
            val = qs.aggregate(s=Sum('valor_total'))['s'] or Decimal(0)
            return (val, val) # Assume-se realizado

        elif model == FolhaPagamento:
            # Data Referência
            filters['data_referencia__range'] = [self.inicio, self.fim]
            filters['data_referencia__month'] = mes
            qs = model.objects.filter(**filters)
            
            # Soma dos componentes
            expr = (Sum('salario_real') + Sum('ferias_terco') + 
                    Sum('empreitada') + Sum('decimo_terceiro') + 
                    Sum('horas_extras_valor'))
            
            nominal = qs.aggregate(t=expr)['t'] or Decimal(0)
            pago = qs.filter(status__in=['Pago', 'PAGO']).aggregate(t=expr)['t'] or Decimal(0)
            return (nominal, pago)

        return (Decimal(0), Decimal(0))

    def gerar(self):
        # 1. Configurar Colunas
        self.worksheet.set_column('A:A', 25)  # Coluna de Títulos
        # Colunas de B até AA (2 colunas x 12 meses + Totais)
        # B=1, C=2 ... Z=25, AA=26
        self.worksheet.set_column(1, 26, 11) 

        meses = [
            'JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
            'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'
        ]

        # 2. Cabeçalhos (Linha 0: Meses mesclados, Linha 1: Valor/Pago)
        self.worksheet.merge_range(0, 0, 1, 0, 'TIPO DE DESPESA', self.fmt_header_month)
        
        col = 1
        for mes in meses:
            # Mescla 2 colunas para o Mês (Ex: B e C)
            self.worksheet.merge_range(0, col, 0, col+1, mes, self.fmt_header_month)
            self.worksheet.write(1, col, "Valor", self.fmt_subheader)
            self.worksheet.write(1, col+1, "Pago", self.fmt_subheader)
            col += 2
            
        # Coluna de Totais
        self.worksheet.merge_range(0, col, 0, col+1, "TOTAL PERÍODO", self.fmt_header_month)
        self.worksheet.write(1, col, "Valor", self.fmt_subheader)
        self.worksheet.write(1, col+1, "Pago", self.fmt_subheader)

        # 3. Dados
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
        
        # Totais acumulados por coluna (12 meses * 2 colunas + 2 totais finais)
        totais_verticais = [Decimal(0)] * 26 

        for nome_gasto, model_class in tipos_gastos:
            self.worksheet.write(row, 0, nome_gasto, self.fmt_bold)
            
            total_linha_nom = Decimal(0)
            total_linha_pg = Decimal(0)
            
            col_idx = 1
            for mes_idx in range(1, 13):
                valor_nom, valor_pg = self.get_valores_mes(model_class, mes_idx)
                
                # Escreve Valor Nominal
                self.worksheet.write(row, col_idx, valor_nom, self.fmt_currency)
                totais_verticais[col_idx-1] += valor_nom
                
                # Escreve Valor Pago
                self.worksheet.write(row, col_idx+1, valor_pg, self.fmt_currency_paid)
                totais_verticais[col_idx] += valor_pg
                
                total_linha_nom += valor_nom
                total_linha_pg += valor_pg
                
                col_idx += 2
            
            # Totais da Linha
            self.worksheet.write(row, col_idx, total_linha_nom, self.fmt_total_col)     # Total Nominal
            self.worksheet.write(row, col_idx+1, total_linha_pg, self.fmt_total_col)  # Total Pago
            
            totais_verticais[col_idx-1] += total_linha_nom
            totais_verticais[col_idx] += total_linha_pg
            
            row += 1

        # 4. Linha de Totais Gerais
        self.worksheet.write(row, 0, "TOTAL GERAL", self.fmt_total_col)
        
        for i, total in enumerate(totais_verticais):
            self.worksheet.write(row, i+1, total, self.fmt_total_col)

        if self.should_close:
            self.workbook.close()
            self.output.seek(0)
            return self.output