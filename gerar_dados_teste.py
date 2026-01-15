import os
import django
import random
from decimal import Decimal
from datetime import timedelta, date

# 1. Configuração do Ambiente Django
# Isso permite que o script rode fora da estrutura de comandos do manage.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. Importações (Agora que o Django está carregado)
from django.db.models import Sum
from faker import Faker

# RH: Funcionários e Férias
from apps.funcionarios.models import (
    Funcionario, EnderecoFuncionario, DocumentosFuncionario, 
    DadosTrabalhistas, Sexo, EstadoCivil, GrauInstrucao
)
from apps.ferias.models import PeriodoAquisitivo, Ferias, PagamentoFerias

# RH: Banco de Horas e Empreitadas
from apps.banco_horas.models import BancoHoras, LancamentoHoras
from apps.empreitadas.models import Empreitada, PagamentoEmpreitada

# Core / Clientes
from apps.clientes.models import Cliente, EnderecoCliente
from apps.comissionamento.models import Arquiteta, ContratoRT, ComissaoArquiteto

# Financeiro: Receber e Bancos
from apps.financeiro.receber.models import Banco, Receber, MovimentoBanco, CaixaDiario

# Financeiro: Pagar
from apps.financeiro.pagar.models import (
    Boleto, GastoUtilidade, FaturaCartao, GastoContabilidade,
    GastoImovel, GastoGeral, FolhaPagamento,
    Cheque, StatusPagamento, FormaPagamento
)

# Sócios
from apps.socios.models import Socio, CategoriaSocio, LancamentoSocio

fake = Faker('pt_BR')

def run():
    print('🚀 Iniciando Mocking Completo (Script Raiz)...')

    # ==============================================================================
    # 1. INFRAESTRUTURA BÁSICA (Bancos, Arquitetas, Clientes, Sócios)
    # ==============================================================================
    
    print('--- Criando Bancos...')
    bancos_objs = []
    for nome in ['Banco do Brasil', 'Nubank', 'Sicoob', 'Caixa Econômica', 'Inter']:
        banco, _ = Banco.objects.get_or_create(
            nome=nome,
            defaults={'saldo_inicial': Decimal(random.uniform(10000, 500000))}
        )
        bancos_objs.append(banco)

    print('--- Criando Arquitetas...')
    arquitetas_objs = []
    for _ in range(5):
        arq, _ = Arquiteta.objects.get_or_create(
            nome=fake.name_female(),
            defaults={
                'cpf': fake.cpf(),
                'banco': 'Nubank',
                'agencia': '0001',
                'conta': str(random.randint(10000, 99999))
            }
        )
        arquitetas_objs.append(arq)

    print('--- Criando Clientes...')
    clientes_objs = []
    for _ in range(12):
        cli = Cliente.objects.create(
            nome_completo=fake.name(),
            cpf=fake.cpf(),
            rg=fake.rg(),
            telefone=fake.phone_number(),
            email=fake.email()
        )
        EnderecoCliente.objects.create(
            cliente=cli,
            cep=fake.postcode(),
            endereco=fake.street_name(),
            numero=fake.building_number(),
            bairro=fake.bairro(),
            cidade=fake.city(),
            uf=fake.state_abbr()
        )
        clientes_objs.append(cli)

    print('--- Criando Sócios...')
    socios_objs = []
    for nome in ["Bernardo CEO", "Sócio Investidor"]:
        s, _ = Socio.objects.get_or_create(nome=nome)
        socios_objs.append(s)

    # ==============================================================================
    # 2. FUNCIONÁRIOS E RH (Férias, Banco de Horas, Empreitadas)
    # ==============================================================================
    print('--- Criando 15 Funcionários e dados de RH...')
    funcionarios_objs = []
    
    for _ in range(15):
        # 2.1 Criar Funcionário
        func = Funcionario.objects.create(
            nome=fake.name_male(),
            data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=55),
            natural_de=fake.city(),
            sexo='M',
            grau_instrucao=random.choice(GrauInstrucao.values),
            estado_civil=random.choice(EstadoCivil.values),
            numero_filhos=random.randint(0, 3)
        )
        funcionarios_objs.append(func)

        # Endereço e Docs
        EnderecoFuncionario.objects.create(
            funcionario=func, endereco=fake.street_name(), numero=fake.building_number(),
            bairro=fake.bairro(), cidade=fake.city(), uf=fake.state_abbr(), cep=fake.postcode()
        )
        DocumentosFuncionario.objects.create(
            funcionario=func, cpf=fake.cpf(), rg=fake.rg(),
            pis_pasep=str(random.randint(10000000000, 99999999999))
        )

        # Dados Trabalhistas
        dt_adm = fake.date_between(start_date='-4y', end_date='-1y')
        salario = Decimal(random.uniform(2500, 7000)).quantize(Decimal('0.00'))
        
        dados_trab = DadosTrabalhistas.objects.create(
            funcionario=func,
            data_admissao_contabilidade=dt_adm,
            data_admissao_marcenaria=dt_adm,
            funcao=fake.job(),
            salario=salario,
            horario_trabalho="07:00 as 17:00"
        )

        # 2.2 Férias (2 períodos)
        inicio_pa = dt_adm
        for i in range(2):
            fim_pa = inicio_pa + timedelta(days=365)
            pa = PeriodoAquisitivo.objects.create(
                funcionario=func, data_inicio=inicio_pa, data_fim=fim_pa, dias_direito=30
            )
            if i == 0: # Período antigo tirou férias
                Ferias.objects.create(periodo=pa, dias_tirados=30, observacoes="Férias gozadas")
            inicio_pa = fim_pa + timedelta(days=1)

        # 2.3 Banco de Horas
        banco_h, _ = BancoHoras.objects.get_or_create(funcionario=func)
        saldo_horas = Decimal(0)
        for _ in range(random.randint(3, 8)):
            horas = Decimal(random.uniform(-5, 10)).quantize(Decimal('0.01'))
            valor_h = (salario / 220).quantize(Decimal('0.01'))
            LancamentoHoras.objects.create(
                funcionario=func,
                horas=horas,
                valor_hora=valor_h
            )
            saldo_horas += horas
        banco_h.saldo = saldo_horas
        banco_h.save()

        # 2.4 Empreitadas
        if random.choice([True, False]): 
            emp = Empreitada.objects.create(
                funcionario=func,
                cliente=random.choice(clientes_objs),
                ambiente=random.choice(['Cozinha', 'Quarto Casal', 'Sala de Estar', 'Área Gourmet']),
                descricao=fake.sentence(),
                valor_total=Decimal(random.uniform(2000, 8000)),
                data_inicio=fake.date_this_year(),
                status='EM_ANDAMENTO'
            )
            PagamentoEmpreitada.objects.create(
                empreitada=emp,
                valor=emp.valor_total / 2,
                observacao="Adiantamento 50%"
            )

    # ==============================================================================
    # 3. FINANCEIRO (Receber e Contratos RT)
    # ==============================================================================
    print('--- Gerando Financeiro (Receber e Contratos RT)...')
    
    for _ in range(8):
        cliente_rt = random.choice(clientes_objs)
        arquiteta_rt = random.choice(arquitetas_objs)
        valor_servico = Decimal(random.uniform(50000, 200000))
        percentual = Decimal(random.choice([5, 10, 15]))
        valor_rt = valor_servico * (percentual / 100)

        contrato = ContratoRT.objects.create(
            arquiteta=arquiteta_rt,
            cliente=cliente_rt,
            data_contrato=fake.date_between(start_date='-1y', end_date='today'),
            percentual=percentual,
            valor_servico=valor_servico,
            valor_rt=valor_rt,
            observacoes="Projeto Residencial Alto Padrão"
        )

        parcelas = 4
        valor_parcela = valor_servico / parcelas
        for p in range(parcelas):
            dt_venc = contrato.data_contrato + timedelta(days=30*(p+1))
            status = 'Recebido' if dt_venc < date.today() else 'Pendente'
            
            rec = Receber.objects.create(
                descricao=f"Parcela {p+1}/{parcelas} - {cliente_rt.nome_completo}",
                cliente=cliente_rt,
                contrato_rt=contrato,
                valor=valor_parcela,
                data_vencimento=dt_venc,
                tipo_recebimento='PRAZO',
                status=status
            )
            
            if status == 'Recebido':
                rec.valor_recebido = valor_parcela
                rec.data_recebimento = dt_venc
                rec.banco_destino = random.choice(bancos_objs)
                rec.save()

        # Comissão a Pagar para Arquiteta
        ComissaoArquiteto.objects.create(
            arquiteta=arquiteta_rt,
            contrato_rt=contrato,
            data_vencimento=contrato.data_contrato + timedelta(days=45),
            valor_comissao=valor_rt,
            status=StatusPagamento.PENDENTE,
            forma_pagamento=FormaPagamento.PIX,
            observacoes="Comissão ref. Projeto X"
        )

    # ==============================================================================
    # 4. FINANCEIRO (Pagar - Diversos)
    # ==============================================================================
    print('--- Gerando Financeiro (Contas a Pagar)...')

    # 4.1 Gastos Gerais
    for _ in range(15):
        GastoGeral.objects.create(
            descricao=f"Compra na {fake.company()}",
            data_gasto=fake.date_this_month(),
            valor_total=Decimal(random.uniform(50, 600)),
            tipo_pagamento='VISTA',
            status=StatusPagamento.PAGO,
            motorista=fake.first_name()
        )

    # 4.2 Utilidades
    tipos_util = ['CEL', 'INT_MARCENARIA', 'ESC_MARCENARIA', 'CESAN_MARCENARIA']
    for tipo in tipos_util:
        GastoUtilidade.objects.create(
            tipo_cliente=tipo,
            descricao=f"Conta {tipo}",
            valor=Decimal(random.uniform(150, 1000)),
            data_vencimento=fake.date_this_month(),
            status=StatusPagamento.PENDENTE
        )

    # 4.3 Boletos
    for _ in range(10):
        Boleto.objects.create(
            credor=fake.company(),
            descricao="Material Marcenaria",
            valor=Decimal(random.uniform(500, 5000)),
            data_vencimento=fake.future_date(),
            status=StatusPagamento.PENDENTE,
            nota_fiscal=str(random.randint(1000, 9000))
        )
    
    # 4.4 Folha de Pagamento
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)
    for func in funcionarios_objs:
        FolhaPagamento.objects.create(
            funcionario=func,
            data_referencia=primeiro_dia_mes,
            salario_real=func.dados_trabalhistas.salario,
            status=StatusPagamento.PENDENTE,
            forma_pagamento=FormaPagamento.PIX,
            referencia_holerite="30 dias"
        )

    # ==============================================================================
    # 5. LANÇAMENTOS SÓCIOS
    # ==============================================================================
    print('--- Gerando Lançamentos de Sócios (Pessoal)...')
    
    ESTRUTURA_SOCIOS = {
        'RENDA_FAMILIAR': ['Salários', 'Dividendos', 'Aluguéis'],
        'HABITACAO': ['Aluguel', 'Condomínio', 'Luz', 'Internet'],
        'AUTOMOVEL': ['Combustível', 'Seguro', 'IPVA'],
        'LAZER': ['Restaurante', 'Viagem', 'Cinema'],
        'SAUDE': ['Plano de Saúde', 'Farmácia']
    }

    for cat_nome, subitens in ESTRUTURA_SOCIOS.items():
        # Cria ou obtém a categoria geral se necessário
        # Nota: Seu model tem unique_together('grupo', 'nome').
        
        for subitem in subitens:
            # Garante que a categoria específica existe
            cat_especifica, _ = CategoriaSocio.objects.get_or_create(
                grupo=cat_nome,
                nome=subitem
            )

            for _ in range(3):
                LancamentoSocio.objects.create(
                    socio=random.choice(socios_objs),
                    categoria=cat_especifica,
                    data=fake.date_between(start_date='-6m', end_date='today'),
                    valor=Decimal(random.uniform(100, 2000)),
                    observacao=f"Gasto com {subitem}"
                )

    print('✅ MOCKING COMPLETO REALIZADO COM SUCESSO!')

if __name__ == "__main__":
    run()