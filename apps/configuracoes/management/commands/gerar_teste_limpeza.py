from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.financeiro.pagar.models import Boleto
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Gera boletos fictícios (antigos e novos) para testar a limpeza do sistema.'

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        
        # Datas para teste
        data_recente = hoje - relativedelta(months=10)  # 10 meses atrás (NÃO deve apagar)
        data_antiga = hoje - relativedelta(months=20)   # 20 meses atrás (DEVE apagar se pago)
        
        self.stdout.write("--- GERANDO DADOS DE TESTE ---")

        # CASO 1: Boleto Antigo (20 meses) e PAGO -> DEVE SER ARQUIVADO
        b1 = Boleto.objects.create(
            descricao="TESTE LIMPEZA - Antigo e Pago (Deve Arquivar)",
            valor=Decimal('100.00'),
            data_vencimento=data_antiga,
            status='Pago',
            is_deleted=False
        )
        self.stdout.write(self.style.SUCCESS(f"[CRIADO] ID {b1.id}: Antigo (20 meses) + PAGO. (Esperado: Arquivar)"))

        # CASO 2: Boleto Antigo (20 meses) mas PENDENTE -> NÃO DEVE APAGAR
        b2 = Boleto.objects.create(
            descricao="TESTE LIMPEZA - Antigo e Pendente (Não Apagar)",
            valor=Decimal('200.00'),
            data_vencimento=data_antiga,
            status='Pendente',
            is_deleted=False
        )
        self.stdout.write(self.style.WARNING(f"[CRIADO] ID {b2.id}: Antigo (20 meses) + PENDENTE. (Esperado: Manter)"))

        # CASO 3: Boleto Recente (10 meses) e PAGO -> NÃO DEVE APAGAR AINDA
        b3 = Boleto.objects.create(
            descricao="TESTE LIMPEZA - Recente e Pago (Não Apagar)",
            valor=Decimal('300.00'),
            data_vencimento=data_recente,
            status='Pago',
            is_deleted=False
        )
        self.stdout.write(self.style.WARNING(f"[CRIADO] ID {b3.id}: Recente (10 meses) + PAGO. (Esperado: Manter)"))

        self.stdout.write("\nAgora rode: python manage.py limpar_sistema")
        self.stdout.write("Depois confira se o ID do Caso 1 foi movido para a lixeira (is_deleted=True).")