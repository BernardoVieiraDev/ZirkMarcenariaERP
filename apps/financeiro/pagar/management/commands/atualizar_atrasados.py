from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.financeiro.pagar.models import (Boleto, ComissaoArquiteto,
                                          FaturaCartao, GastoContabilidade,
                                          GastoGeral, GastoImovel,
                                          GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo, StatusPagamento)


class Command(BaseCommand):
    help = 'Atualiza automaticamente o status de contas pendentes vencidas para Atrasado'

    def handle(self, *args, **options):
        # Data de referência: Ontem. Se venceu ontem e não pagou, hoje está atrasado.
        # Ou: Hoje. Se venceu hoje e o script roda amanhã cedo, já pega.
        # Vamos usar "menor que hoje" (lt=hoje), ou seja, venceu até ontem.
        hoje = timezone.now().date()
        total_atualizados = 0

        self.stdout.write(f"Iniciando verificação em: {hoje}")

        # --- GRUPO 1: Modelos baseados em GastoBase (usam 'data_vencimento') ---
        modelos_padrao = [
            Boleto, 
            GastoVeiculoConsorcio, 
            GastoUtilidade, 
            FaturaCartao, 
            PrestacaoEmprestimo, 
            GastoContabilidade, 
            GastoImovel
        ]

        for model in modelos_padrao:
            contas_vencidas = model.objects.filter(
                status=StatusPagamento.PENDENTE,
                data_vencimento__lt=hoje
            )
            qtd = contas_vencidas.update(status=StatusPagamento.ATRASADO)
            if qtd > 0:
                self.stdout.write(f"[{model.__name__}] {qtd} contas marcadas como Atrasado.")
                total_atualizados += qtd

        # --- GRUPO 2: Comissões (usam 'data_pagamento' como previsão) ---
        comissoes = ComissaoArquiteto.objects.filter(
            status=StatusPagamento.PENDENTE,
            data_pagamento__lt=hoje
        )
        qtd_com = comissoes.update(status=StatusPagamento.ATRASADO)
        if qtd_com > 0:
            self.stdout.write(f"[ComissaoArquiteto] {qtd_com} comissões vencidas.")
            total_atualizados += qtd_com

        # --- GRUPO 3: Gastos Gerais (usam 'data_gasto') ---
        # Apenas para gastos "A Prazo" que ficaram pendentes
        gerais = GastoGeral.objects.filter(
            status=StatusPagamento.PENDENTE,
            data_gasto__lt=hoje
        )
        qtd_geral = gerais.update(status=StatusPagamento.ATRASADO)
        if qtd_geral > 0:
            self.stdout.write(f"[GastoGeral] {qtd_geral} gastos vencidos.")
            total_atualizados += qtd_geral

        self.stdout.write(self.style.SUCCESS(f'Concluído! Total atualizado: {total_atualizados}'))