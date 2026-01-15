import random
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.financeiro.pagar.models import FolhaPagamento
from apps.funcionarios.models import Funcionario


class Command(BaseCommand):
    help = 'Gera dados de folha de pagamento antigos para testar a limpeza do sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- INICIANDO GERAÇÃO DE DADOS DE TESTE (FOLHA) ---")

        # 1. Obter ou Criar um Funcionário de Teste
        # Tenta pegar o primeiro que existir, se não, cria um dummy.
        funcionario = Funcionario.objects.first()
        if not funcionario:
            self.stdout.write("Nenhum funcionário encontrado. Criando 'Funcionario Teste'...")
            funcionario = Funcionario.objects.create(
                nome="Funcionario Teste Limpeza",
                cpf="000.000.000-00",
                # Adicione outros campos obrigatórios do seu model se der erro (ex: cargo, data_admissao)
            )
        else:
            self.stdout.write(f"Usando funcionário existente: {funcionario.nome}")

        # 2. Definir Datas
        hoje = timezone.now().date()
        data_antiga = hoje - relativedelta(months=20)  # 20 meses atrás (Deve ser apagado)
        data_recente = hoje - relativedelta(months=2)  # 2 meses atrás (Deve ser mantido)

        # 3. Criar Folha ANTIGA e PAGA (Alvo da Limpeza)
        # Tenta criar com campos comuns. Se seu modelo tiver campos obrigatórios diferentes, o erro avisará.
        try:
            folha_velha = FolhaPagamento.objects.create(
                funcionario=funcionario,
                data_referencia=data_antiga,
                status='Pago',  # Status que permite limpeza
                # Campos de valor fictícios (ajuste nomes se seu model for diferente, ex: salario_liquido)
                # Como não tenho o model exato, estou assumindo que ele aceita criação sem valor ou tem defaults.
                # Se der erro de campo obrigatório, adicione aqui: valor_total=Decimal('1500.00')
            )
            self.stdout.write(self.style.SUCCESS(
                f"[CRIADO] Folha ID {folha_velha.id}: Data {data_antiga} (20 meses) - Status: Pago -> DEVE SER ARQUIVADA"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao criar folha antiga: {e}"))

        # 4. Criar Folha ANTIGA mas PENDENTE (Segurança)
        try:
            folha_pendente = FolhaPagamento.objects.create(
                funcionario=funcionario,
                data_referencia=data_antiga,
                status='Pendente',  # NÃO deve apagar
            )
            self.stdout.write(self.style.WARNING(
                f"[CRIADO] Folha ID {folha_pendente.id}: Data {data_antiga} (20 meses) - Status: Pendente -> DEVE SER MANTIDA"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao criar folha pendente: {e}"))

        # 5. Criar Folha RECENTE (Segurança)
        try:
            folha_nova = FolhaPagamento.objects.create(
                funcionario=funcionario,
                data_referencia=data_recente,
                status='Pago',
            )
            self.stdout.write(self.style.WARNING(
                f"[CRIADO] Folha ID {folha_nova.id}: Data {data_recente} (2 meses) - Status: Pago -> DEVE SER MANTIDA"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao criar folha nova: {e}"))

        self.stdout.write("\nAgora rode: python manage.py limpar_sistema")