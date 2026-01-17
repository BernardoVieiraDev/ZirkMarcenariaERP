from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Q
from django.core.cache import cache # Importação adicionada

# Imports dos Models (mantidos)
from apps.financeiro.receber.models import Receber, CaixaDiario, Banco, MovimentoBanco
from apps.financeiro.pagar.models import (
    Boleto, Cheque, ComissaoArquiteto, FaturaCartao, FolhaPagamento,
    GastoContabilidade, GastoGasolina, GastoGeral, GastoImovel,
    GastoUtilidade, GastoVeiculoConsorcio, PrestacaoEmprestimo
)

class FluxoCaixaService:
    
    # Prefixos de Chaves de Cache
    KEY_SALDO_ATUAL = "fluxo_saldo_atual_real"
    KEY_TIMELINE_PREFIX = "fluxo_timeline_"

    @staticmethod
    def clear_fluxo_cache():
        """
        Método CRÍTICO: Deve ser chamado por signals sempre que houver movimentação financeira.
        Apaga o saldo atual e todas as projeções de fluxo cacheadas.
        """
        cache.delete(FluxoCaixaService.KEY_SALDO_ATUAL)
        # Para limpar as timelines, o ideal é usar delete_pattern se seu backend (Redis) suportar,
        # ou versionamento. Como fallback seguro, limpamos apenas o saldo, 
        # mas forçamos as timelines a terem TTL curto (ex: 5 min).
        # Se usar Redis, pode fazer: cache.delete_pattern("fluxo_timeline_*")
        try:
            cache.delete_pattern(f"{FluxoCaixaService.KEY_TIMELINE_PREFIX}*")
        except AttributeError:
            # Backend LocMemCache ou DatabaseCache pode não ter delete_pattern
            pass

    @staticmethod
    def get_saldo_atual():
        """Calcula o Saldo Real HOJE (Bancos + Caixa) - COM CACHE"""
        saldo = cache.get(FluxoCaixaService.KEY_SALDO_ATUAL)
        
        if saldo is None:
            # Cálculo Original Pesado
            total_bancos_inicial = Banco.objects.aggregate(s=Sum('saldo_inicial'))['s'] or Decimal(0)
            mov_entrada = MovimentoBanco.objects.filter(tipo='E').aggregate(s=Sum('valor'))['s'] or Decimal(0)
            mov_saida = MovimentoBanco.objects.filter(tipo='S').aggregate(s=Sum('valor'))['s'] or Decimal(0)
            saldo_bancos = total_bancos_inicial + mov_entrada - mov_saida

            caixa_entrada = CaixaDiario.objects.filter(tipo='E').aggregate(s=Sum('valor'))['s'] or Decimal(0)
            caixa_saida = CaixaDiario.objects.filter(tipo='S').aggregate(s=Sum('valor'))['s'] or Decimal(0)
            saldo_caixa = caixa_entrada - caixa_saida

            saldo = saldo_bancos + saldo_caixa
            # Cache por tempo indeterminado até que um Signal invalide
            cache.set(FluxoCaixaService.KEY_SALDO_ATUAL, saldo, timeout=None)

        return saldo

    @classmethod
    def gerar_fluxo_detalhado(cls, data_inicio, num_dias):
        # Chave baseada nos parâmetros
        cache_key = f"{cls.KEY_TIMELINE_PREFIX}{data_inicio.isoformat()}_{num_dias}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        dias = []
        # Importante: get_saldo_atual() já usa seu próprio cache interno
        saldo_anterior = cls.get_saldo_atual()
        
        timeline = {
            'entradas': {
                'vendas_vista': [], 'recebimentos_debito': [], 'recebimentos_credito': [], 'outras': [], 'total': []
            },
            'saidas': {
                'compras_vista': [], 'pagamentos_contas': [], 'outros_pagamentos': [], 'outras_saidas': [], 'total': []
            },
            'conclusao': {
                'resultado_dia': [], 'saldo_anterior': [], 'saldo_acumulado': [], 
                'previsao_emprestimo': [], 'saldo_final': [], 'alerta': [], 'itens_saldo_final': []
            }
        }

        # Configuração de Saídas (Mantida)
        config_saidas = [
            (GastoGeral, 'data_gasto', 'compras_vista'),
            (GastoGasolina, 'data_gasto', 'compras_vista'),
            (Boleto, 'data_vencimento', 'pagamentos_contas'),
            (GastoUtilidade, 'data_vencimento', 'pagamentos_contas'),
            (GastoImovel, 'data_vencimento', 'pagamentos_contas'),
            (GastoContabilidade, 'data_vencimento', 'pagamentos_contas'),
            (FaturaCartao, 'data_vencimento', 'pagamentos_contas'),
            (Cheque, 'data_emissao', 'pagamentos_contas'), 
            (FolhaPagamento, 'data_referencia', 'outros_pagamentos'), 
            (ComissaoArquiteto, 'data_pagamento', 'outros_pagamentos'),
            (PrestacaoEmprestimo, 'data_vencimento', 'outras_saidas'),
            (GastoVeiculoConsorcio, 'data_vencimento', 'outras_saidas'),
        ]

        for i in range(num_dias):
            dia_atual = data_inicio + timedelta(days=i)
            dias.append(dia_atual)

            # === 1. ENTRADAS ===
            qs_receber = Receber.objects.filter(data_vencimento=dia_atual).exclude(status='Recebido')
            
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

            # === 2. SAÍDAS ===
            totais_dia = {
                'compras_vista': Decimal(0), 'pagamentos_contas': Decimal(0),
                'outros_pagamentos': Decimal(0), 'outras_saidas': Decimal(0)
            }

            for Model, date_field, categoria_key in config_saidas:
                filtro = {date_field: dia_atual}
                qs = Model.objects.filter(**filtro)

                if hasattr(Model, 'status'):
                    field_names = [f.name for f in Model._meta.get_fields()]
                    if 'status' in field_names:
                        if Model.__name__ == 'Cheque':
                             qs = qs.exclude(status__in=['DEV', 'CAN', 'Devolvido', 'Cancelado'])
                        else:
                            qs = qs.exclude(status__in=['Pago', 'PAGO', 'Baixado', 'Recebido', 'DEV', 'CAN'])

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

            # === 3. CONCLUSÃO ===
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

            timeline['conclusao']['itens_saldo_final'].append({
                'valor': saldo_final,
                'alerta': saldo_final < 0
            })

            saldo_anterior = saldo_final
        
        result = (dias, timeline)
        # Cache curto (15 min) para o relatório detalhado, pois ele é complexo
        # A invalidação forçada ocorre via clear_fluxo_cache()
        cache.set(cache_key, result, 60 * 15)
        
        return result