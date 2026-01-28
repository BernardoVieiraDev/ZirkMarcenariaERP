import random
from decimal import Decimal
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

# Importação dos Models
from apps.funcionarios.models import (
    Funcionario, EnderecoFuncionario, DocumentosFuncionario, 
    DadosTrabalhistas, Sexo, EstadoCivil, GrauInstrucao
)
from apps.ferias.models import PeriodoAquisitivo
from apps.banco_horas.models import BancoHoras

class Command(BaseCommand):
    help = 'Gera funcionários fictícios com dados completos (Endereço, Docs, RH) para teste.'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, nargs='?', default=5, help='Quantidade de funcionários a criar')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        fake = Faker('pt_BR')
        
        self.stdout.write(self.style.WARNING(f'Iniciando criação de {total} funcionários...'))

        criados = 0

        # Usamos transaction.atomic para garantir que ou cria tudo do funcionário ou nada (evita dados órfãos)
        try:
            with transaction.atomic():
                for _ in range(total):
                    # 1. Dados Pessoais Básicos
                    sexo_escolhido = random.choice([Sexo.MASCULINO, Sexo.FEMININO])
                    if sexo_escolhido == Sexo.MASCULINO:
                        nome = fake.name_male()
                    else:
                        nome = fake.name_female()

                    funcionario = Funcionario.objects.create(
                        nome=nome,
                        data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=60),
                        natural_de=fake.city(),
                        sexo=sexo_escolhido,
                        grau_instrucao=random.choice(GrauInstrucao.values),
                        estado_civil=random.choice(EstadoCivil.values),
                        nome_mae=fake.name_female(),
                        nome_pai=fake.name_male(),
                        numero_filhos=random.randint(0, 4)
                    )

                    # 2. Endereço
                    EnderecoFuncionario.objects.create(
                        funcionario=funcionario,
                        endereco=fake.street_name(),
                        numero=str(fake.building_number()),
                        bairro=fake.bairro(),
                        cidade=fake.city(),
                        uf=fake.state_abbr(),
                        cep=fake.postcode()
                    )

                    # 3. Documentos (CPF e RG)
                    DocumentosFuncionario.objects.create(
                        funcionario=funcionario,
                        cpf=fake.cpf(),
                        rg=fake.rg(),
                        rg_orgao_expedidor="SSP/MG",
                        pis_pasep=str(random.randint(12000000000, 99999999999)),
                        ctps_numero=str(random.randint(10000, 99999)),
                        ctps_serie=str(random.randint(100, 999))
                    )

                    # 4. Dados Trabalhistas
                    data_adm = fake.date_between(start_date='-5y', end_date='today')
                    
                    DadosTrabalhistas.objects.create(
                        funcionario=funcionario,
                        data_admissao_contabilidade=data_adm,
                        data_admissao_marcenaria=data_adm, # Assume a mesma data para simplificar
                        funcao=fake.job(),
                        cbo=str(random.randint(1000, 9999)),
                        salario=Decimal(random.uniform(1800.00, 8500.00)).quantize(Decimal('0.01')),
                        horario_trabalho="08:00 às 18:00 (Seg a Sex)"
                    )

                    # 5. Inicializar Banco de Horas (Opcional, mas útil para o sistema não quebrar)
                    BancoHoras.objects.get_or_create(funcionario=funcionario, defaults={'saldo': 0})

                    # 6. Gerar Períodos Aquisitivos de Férias (Passado e Futuro)
                    # Cria o primeiro período a partir da admissão
                    data_inicio_periodo = data_adm
                    for _ in range(6): # Tenta criar até 6 períodos (cobre 5 anos de casa)
                        data_fim_periodo = data_inicio_periodo + timedelta(days=364)
                        
                        # Só cria se o período já começou
                        if data_inicio_periodo <= date.today():
                            PeriodoAquisitivo.objects.get_or_create(
                                funcionario=funcionario,
                                data_inicio=data_inicio_periodo,
                                defaults={'data_fim': data_fim_periodo}
                            )
                        
                        data_inicio_periodo = data_fim_periodo + timedelta(days=1)

                    criados += 1
                    self.stdout.write(f'  + Funcionário criado: {funcionario.nome}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao gerar dados: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Concluído! {criados} funcionários foram inseridos no banco.'))