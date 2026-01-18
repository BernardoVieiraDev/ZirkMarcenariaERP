import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.financeiro.pagar.models import (
    ParcelamentoPagar, Boleto, GastoUtilidade, FaturaCartao,
    PrestacaoEmprestimo, GastoContabilidade, GastoImovel,
    Cheque, GastoGeral, GastoGasolina, FolhaPagamento,
    ComissaoArquiteto, GastoVeiculoConsorcio, FormaPagamento, StatusPagamento
)
from apps.financeiro.receber.models import Banco
from apps.funcionarios.models import Funcionario, Sexo
from apps.comissionamento.models import Arquiteta, ContratoRT
from apps.clientes.models import Cliente

class Command(BaseCommand):
    help = 'Gera dados fictícios (mock) para todas as contas a pagar.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando o mocking de Contas a Pagar...'))
        fake = Faker('pt_BR')

        # 1. Garantir Dependências
        self.stdout.write("Criando dependências...")
        banco, _ = Banco.objects.get_or_create(
            nome="Banco Mock", defaults={'agencia': '0001', 'conta': '12345-6', 'saldo_inicial': 100000}
        )

        # Criar Funcionário Fake
        funcionario = Funcionario.objects.first()
        if not funcionario:
            funcionario = Funcionario.objects.create(
                nome=fake.name(),
                data_nascimento=date(1990, 1, 1),
                sexo=Sexo.MASCULINO,
                data_admissao_contabilidade=date(2023, 1, 1),
                data_admissao_marcenaria=date(2023, 1, 1),
                funcao="Marceneiro",
                salario=Decimal('2500.00'),
            )

        # Criar Arquiteta Fake
        arquiteta, _ = Arquiteta.objects.get_or_create(
            nome="Arquiteta Mock",
            defaults={
                'banco': 'Nubank', 'agencia': '0001', 'conta': '9999-9'
            }
        )
        
        # Criar Cliente e Contrato RT
        cliente, _ = Cliente.objects.get_or_create(
            nome_completo="Cliente Mock", 
            defaults={'cpf': fake.cpf()}
        )
        
        contrato_rt, _ = ContratoRT.objects.get_or_create(
            arquiteta=arquiteta,
            cliente=cliente,
            defaults={
                'valor_servico': 50000,
                'valor_rt': 5000,
                'data_contrato': date.today()
            }
        )

        # Função auxiliar para gerar datas
        def random_date():
            return date.today() + timedelta(days=random.randint(-30, 60))

        # 2. Gerar Parcelamentos e Itens Vinculados (GastoBase)
        
        # --- Boletos ---
        self.criar_parcelamento_com_itens(
            model=Boleto,
            qtd_parcelas=5,
            prefixo="Compra Material",
            campos_extras={'credor': 'Fornecedor ABC', 'nota_fiscal': '12345'}
        )
        
        # --- Gasto Veículo/Consórcio ---
        self.criar_parcelamento_com_itens(
            model=GastoVeiculoConsorcio,
            qtd_parcelas=12,
            prefixo="Consórcio Hilux",
            campos_extras={'tipo_gasto': 'CONS', 'veiculo_referencia': 'Toyota Hilux'}
        )

        # --- Gasto Utilidade ---
        for tipo, nome in GastoUtilidade.TIPO_CHOICES:
            GastoUtilidade.objects.create(
                tipo_cliente=tipo,
                valor=Decimal(random.randrange(100, 500)),
                data_vencimento=random_date(),
                status=StatusPagamento.PENDENTE,
                descricao=f"Conta de {nome}"
            )
        self.stdout.write(f"Criados {len(GastoUtilidade.TIPO_CHOICES)} Gastos de Utilidade.")

        # --- Fatura Cartão ---
        for cartao, nome in FaturaCartao.TIPO_CHOICES:
            FaturaCartao.objects.create(
                cartao=cartao,
                valor=Decimal(random.randrange(2000, 15000)),
                data_vencimento=random_date(),
                status=StatusPagamento.PENDENTE
            )
        self.stdout.write(f"Criadas Faturas de Cartão.")

        # --- Prestação Empréstimo ---
        self.criar_parcelamento_com_itens(
            model=PrestacaoEmprestimo,
            qtd_parcelas=10,
            prefixo="Empréstimo Capital Giro",
            campos_extras={} 
        )

        # --- Gasto Contabilidade ---
        for tipo, nome in GastoContabilidade.TIPO_CHOICES:
            GastoContabilidade.objects.create(
                tipo_gasto=tipo,
                valor=Decimal(random.randrange(200, 1000)),
                data_vencimento=random_date(),
                status=StatusPagamento.PENDENTE,
                descricao=f"{nome} ref. mês anterior"
            )
        self.stdout.write("Criados Gastos de Contabilidade.")

        # --- Gasto Imóvel ---
        for tipo, nome in GastoImovel.TIPO_CHOICES:
            GastoImovel.objects.create(
                tipo_gasto=tipo,
                local_lote="Lote 15 Quadra B",
                valor=Decimal(random.randrange(500, 2000)),
                data_vencimento=random_date(),
                status=StatusPagamento.PENDENTE
            )
        self.stdout.write("Criados Gastos Imobiliários.")

        # 3. Gerar Itens Independentes

        # --- Cheques ---
        for i in range(5):
            Cheque.objects.create(
                descricao=f"Pagamento Cheque {i}",
                valor=Decimal(random.randrange(500, 3000)),
                data_emissao=random_date(),
                numero_cheque=str(random.randint(100000, 999999)),
                status='EMI',
                tipo_entidade='J'
            )
        self.stdout.write("Criados 5 Cheques.")

        # --- Gasto Geral ---
        for i in range(10):
            GastoGeral.objects.create(
                descricao=fake.sentence(nb_words=3),
                data_gasto=random_date(),
                valor_total=Decimal(random.randrange(50, 300)),
                tipo_pagamento='VISTA',
                credor=fake.company(),
                status=StatusPagamento.PAGO,
                forma_principal_pagamento='PIX'
            )
        self.stdout.write("Criados 10 Gastos Gerais.")

        # --- Gasto Gasolina ---
        for i in range(5):
            GastoGasolina.objects.create(
                descricao="Abastecimento Semanal",
                data_gasto=random_date(),
                valor_total=Decimal(random.randrange(200, 400)),
                carro="Fiat Strada",
                status=StatusPagamento.PAGO
            )
        self.stdout.write("Criados 5 Gastos de Gasolina.")

        # --- Folha de Pagamento ---
        if funcionario:
            if not FolhaPagamento.objects.filter(funcionario=funcionario, data_referencia=date.today().replace(day=5)).exists():
                FolhaPagamento.objects.create(
                    funcionario=funcionario,
                    data_referencia=date.today().replace(day=5),
                    salario_real=Decimal('3500.00'),
                    vale=Decimal('200.00'),
                    status=StatusPagamento.PENDENTE
                )
                self.stdout.write("Criada Folha de Pagamento.")

        # --- Comissão Arquiteta ---
        # Removido o campo 'arquiteta' pois o modelo parece usar apenas 'contrato_rt'
        ComissaoArquiteto.objects.create(
            contrato_rt=contrato_rt,
            data_vencimento=random_date(),
            valor_comissao=Decimal('1500.00'),
            status=StatusPagamento.PENDENTE,
            observacoes="1ª Parcela RT"
        )
        self.stdout.write("Criada Comissão de Arquiteta.")

        self.stdout.write(self.style.SUCCESS('Mocking concluído com sucesso!'))

    def criar_parcelamento_com_itens(self, model, qtd_parcelas, prefixo, campos_extras):
        """
        Cria um ParcelamentoPagar e vincula N itens do modelo especificado.
        """
        valor_parcela = Decimal(random.randrange(500, 5000))
        valor_total = valor_parcela * qtd_parcelas

        # 1. Criar o Pai (Parcelamento)
        parcelamento = ParcelamentoPagar.objects.create(
            descricao=f"{prefixo} - Parcelamento Mock",
            valor_total_original=valor_total,
            qtd_parcelas=qtd_parcelas
        )

        # 2. Criar as Parcelas (Filhos)
        data_base = date.today()
        
        for i in range(qtd_parcelas):
            vencimento = data_base + timedelta(days=30 * i)
            
            # Preparar dados
            dados = {
                'parcelamento': parcelamento,
                'descricao': f"{prefixo} {i+1}/{qtd_parcelas}",
                'valor': valor_parcela,
                'data_vencimento': vencimento,
                'status': StatusPagamento.PENDENTE,
                'forma_pagamento': FormaPagamento.BOLETO
            }
            dados.update(campos_extras)

            # Ajuste específico para PrestacaoEmprestimo
            if model == PrestacaoEmprestimo:
                dados['prestacao'] = i + 1
                if 'credor' not in dados: dados['credor'] = 'Banco Empréstimo'

            model.objects.create(**dados)

        self.stdout.write(f"Criado Parcelamento '{prefixo}' com {qtd_parcelas} parcelas de {model._meta.verbose_name}.")