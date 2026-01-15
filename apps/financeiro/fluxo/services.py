from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Q

# Imports dos Models
from apps.financeiro.receber.models import Receber, CaixaDiario, Banco, MovimentoBanco
from apps.financeiro.pagar.models import (
    Boleto, Cheque, ComissaoArquiteto, FaturaCartao, FolhaPagamento,
    GastoContabilidade, GastoGasolina, GastoGeral, GastoImovel,
    GastoUtilidade, GastoVeiculoConsorcio, PrestacaoEmprestimo
)

class FluxoCaixaService:

    @staticmethod
    def get_saldo_atual():
        """Calcula o Saldo Real HOJE (Bancos + Caixa)"""
        total_bancos_inicial = Banco.objects.aggregate(s=Sum('saldo_inicial'))['s'] or Decimal(0)
        mov_entrada = MovimentoBanco.objects.filter(tipo='E').aggregate(s=Sum('valor'))['s'] or Decimal(0)
        mov_saida = MovimentoBanco.objects.filter(tipo='S').aggregate(s=Sum('valor'))['s'] or Decimal(0)
        saldo_bancos = total_bancos_inicial + mov_entrada - mov_saida

        caixa_entrada = CaixaDiario.objects.filter(tipo='E').aggregate(s=Sum('valor'))['s'] or Decimal(0)
        caixa_saida = CaixaDiario.objects.filter(tipo='S').aggregate(s=Sum('valor'))['s'] or Decimal(0)
        saldo_caixa = caixa_entrada - caixa_saida

        return saldo_bancos + saldo_caixa

    @classmethod
    def gerar_fluxo_detalhado(cls, data_inicio, num_dias):
        dias = []
        saldo_anterior = cls.get_saldo_atual()
        
        timeline = {
            'entradas': {
                'vendas_vista': [],
                'recebimentos_debito': [],
                'recebimentos_credito': [],
                'outras': [],
                'total': []
            },
            'saidas': {
                'compras_vista': [],     # Compras à vista (Caixa)
                'pagamentos_contas': [], # Pagamentos (Contas a Pagar + Cheques)
                'outros_pagamentos': [], # Pessoal, Comissões
                'outras_saidas': [],     # Investimentos
                'total': []
            },
            'conclusao': {
                'resultado_dia': [],
                'saldo_anterior': [],
                'saldo_acumulado': [],
                'previsao_emprestimo': [],
                'saldo_final': [],
                'alerta': []
            }
        }

        # Configuração: Mapeia (Modelo, CampoData, Categoria)
        config_saidas = [
            # 1. Compras à vista (Caixa)
            (GastoGeral, 'data_gasto', 'compras_vista'),
            (GastoGasolina, 'data_gasto', 'compras_vista'),

            # 2. Pagamentos (Contas a Pagar)
            # Mudei CHEQUE para cá se você quiser vê-lo junto com as contas principais
            (Boleto, 'data_vencimento', 'pagamentos_contas'),
            (GastoUtilidade, 'data_vencimento', 'pagamentos_contas'),
            (GastoImovel, 'data_vencimento', 'pagamentos_contas'),
            (GastoContabilidade, 'data_vencimento', 'pagamentos_contas'),
            (FaturaCartao, 'data_vencimento', 'pagamentos_contas'),
            (Cheque, 'data_emissao', 'pagamentos_contas'), # <--- MOVIDO PARA PAGAMENTOS DE CONTAS

            # 3. Outros Pagamentos (Pessoal)
            (FolhaPagamento, 'data_referencia', 'outros_pagamentos'), 
            (ComissaoArquiteto, 'data_pagamento', 'outros_pagamentos'),
            
            # 4. Outras Saídas
            (PrestacaoEmprestimo, 'data_vencimento', 'outras_saidas'),
            (GastoVeiculoConsorcio, 'data_vencimento', 'outras_saidas'),
        ]

        for i in range(num_dias):
            dia_atual = data_inicio + timedelta(days=i)
            dias.append(dia_atual)

            # ==========================================
            # === 1. ENTRADAS
            # ==========================================
            qs_receber = Receber.objects.filter(data_vencimento=dia_atual).exclude(status='Recebido')
            
            # (Lógica de entradas mantida igual...)
            vendas_vista = qs_receber.filter(Q(tipo_recebimento='VISTA') | Q(forma_recebimento__in=['DINHEIRO', 'PIX'])).aggregate(s=Sum('valor'))['s'] or Decimal(0)
            rec_debito = qs_receber.filter(forma_recebimento='DEBITO').aggregate(s=Sum('valor'))['s'] or Decimal(0)
            rec_credito = qs_receber.filter(forma_recebimento='CREDITO').aggregate(s=Sum('valor'))['s'] or Decimal(0)
            outras_entradas = qs_receber.exclude(Q(tipo_recebimento='VISTA') | Q(forma_recebimento__in=['DINHEIRO', 'PIX', 'DEBITO', 'CREDITO'])).aggregate(s=Sum('valor'))['s'] or Decimal(0)
            total_entradas_dia = vendas_vista + rec_debito + rec_credito + outras_entradas
            
            timeline['entradas']['vendas_vista'].append(vendas_vista)
            timeline['entradas']['recebimentos_debito'].append(rec_debito)
            timeline['entradas']['recebimentos_credito'].append(rec_credito)
            timeline['entradas']['outras'].append(outras_entradas)
            timeline['entradas']['total'].append(total_entradas_dia)

            # ==========================================
            # === 2. SAÍDAS
            # ==========================================
            
            totais_dia = {
                'compras_vista': Decimal(0),
                'pagamentos_contas': Decimal(0),
                'outros_pagamentos': Decimal(0),
                'outras_saidas': Decimal(0)
            }

            for Model, date_field, categoria_key in config_saidas:
                filtro = {date_field: dia_atual}
                qs = Model.objects.filter(**filtro)

                # --- CORREÇÃO DE STATUS ---
                if hasattr(Model, 'status'):
                    # Verifica os campos do modelo
                    field_names = [f.name for f in Model._meta.get_fields()]
                    if 'status' in field_names:
                        
                        # --- MODIFICAÇÃO SUGERIDA ---
                        # Se for Cheque, só exclui se estiver Devolvido ou Cancelado.
                        # Se estiver Compensado ('COM'), mantemos na lista para visualização,
                        # MAS precisamos cuidar para não duplicar o saldo (ver nota abaixo).
                        if Model.__name__ == 'Cheque':
                             qs = qs.exclude(status__in=['DEV', 'CAN', 'Devolvido', 'Cancelado'])
                        else:
                            # Para outros itens (Boletos, etc), mantém a lógica original
                            qs = qs.exclude(status__in=[
                                'Pago', 'PAGO', 'Baixado', 'Recebido', 
                                'DEV', 'CAN'
                            ])

                for item in qs:
                    valor = getattr(item, 'valor', 0)
                    if hasattr(item, 'get_valor_consolidado'): valor = item.get_valor_consolidado()
                    elif hasattr(item, 'valor_total'): valor = item.valor_total
                    elif hasattr(item, 'valor_comissao'): valor = item.valor_comissao
                    
                    if valor:
                        totais_dia[categoria_key] += valor

            total_saidas_dia = sum(totais_dia.values())

            timeline['saidas']['compras_vista'].append(totais_dia['compras_vista'])
            timeline['saidas']['pagamentos_contas'].append(totais_dia['pagamentos_contas'])
            timeline['saidas']['outros_pagamentos'].append(totais_dia['outros_pagamentos'])
            timeline['saidas']['outras_saidas'].append(totais_dia['outras_saidas'])
            timeline['saidas']['total'].append(total_saidas_dia)

            # ==========================================
            # === 3. CONCLUSÃO
            # ==========================================
            resultado_dia = total_entradas_dia - total_saidas_dia
            saldo_acumulado = saldo_anterior + resultado_dia
            previsao_emprestimo = Decimal(0)
            saldo_final = saldo_acumulado + previsao_emprestimo

            timeline['conclusao']['resultado_dia'].append(resultado_dia)
            timeline['conclusao']['saldo_anterior'].append(saldo_anterior)
            timeline['conclusao']['saldo_acumulado'].append(saldo_acumulado)
            timeline['conclusao']['previsao_emprestimo'].append(previsao_emprestimo)
            timeline['conclusao']['saldo_final'].append(saldo_final)
            timeline['conclusao']['alerta'].append(saldo_final < 0)

            saldo_anterior = saldo_final

        return dias, timeline