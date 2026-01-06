import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
# A CORREÇÃO ESTÁ NA LINHA ABAIXO:
from apps.socios.models import Socio, CategoriaSocio, LancamentoSocio

class Command(BaseCommand):
    help = 'Gera dados mockados de despesas para Sócios em todas as categorias'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando geração de dados mockados...'))

        # 1. Definição das Categorias e Subtipos fornecidos
        DADOS_CATEGORIAS = {
            'RENDA_FAMILIAR': [
                'Salários', '13º. Salário', 'Férias', 'Retirada de Poupança', 
                'Empréstimos', 'Outros'
            ],
            'HABITACAO': [
                'Aluguel/Prestação', 'Água', 'Netflix', 'Luz', 'Telefones', 
                'Gás', 'Internet', 'Supermercado', 'Reformas/Consertos', 'Outros'
            ],
            'SAUDE': [
                'Plano de Saúde', 'Médico', 'Dentista', 'Medicamentos', 'Outros'
            ],
            'TRANSPORTE': [
                'Ônibus', 'Táxi', 'Aplicativos'
            ],
            'AUTOMOVEL': [
                'Prestação', 'Seguro', 'Combustível', 'Lavagens', 
                'IPVA', 'Mecânico', 'Multas', 'Outros'
            ],
            'DESPESAS_PESSOAIS': [
                'Higiene Pessoal', 'Cosméticos', 'Cabeleireiro/barbeiro', 
                'Vestuário', 'Academia', 'Telefone Celular', 'Outros'
            ],
            'LAZER': [
                'Restaurantes', 'Hotéis', 'Passeios/viagens', 'Outros'
            ],
            'DEPENDENTES': [
                'Escola/Faculdade', 'Cursos Extras', 'Material escolar', 
                'Esportes/Uniformes', 'Previdência Privada', 'Vestuário', 'Outros'
            ]
        }

        # 2. Garantir que um Sócio de teste exista
        socio, created = Socio.objects.get_or_create(nome="Sócio Teste Mock")
        if created:
            self.stdout.write(self.style.SUCCESS(f'Sócio criado: {socio.nome}'))
        else:
            self.stdout.write(f'Usando sócio existente: {socio.nome}')

        lancamentos_criados = []

        # 3. Iterar sobre os grupos e criar/buscar categorias e gerar lançamentos
        for grupo_chave, lista_nomes in DADOS_CATEGORIAS.items():
            self.stdout.write(f'Processando grupo: {grupo_chave}...')
            
            for nome_categoria in lista_nomes:
                # Cria ou recupera a CategoriaSocio
                categoria_obj, cat_created = CategoriaSocio.objects.get_or_create(
                    grupo=grupo_chave,
                    nome=nome_categoria
                )
                
                # Gerar de 1 a 3 lançamentos por subtipo para ter volume de dados
                qtd_lancamentos = random.randint(1, 3)
                
                for _ in range(qtd_lancamentos):
                    # Data aleatória nos últimos 60 dias
                    dias_atras = random.randint(0, 60)
                    data_lancamento = timezone.now().date() - timedelta(days=dias_atras)
                    
                    # Valor aleatório entre 50.00 e 2000.00
                    valor_aleatorio = Decimal(random.uniform(50.0, 2000.0)).quantize(Decimal("0.01"))
                    
                    lancamento = LancamentoSocio(
                        socio=socio,
                        categoria=categoria_obj,
                        data=data_lancamento,
                        valor=valor_aleatorio,
                        observacao=f"Mock gerado automaticamente para {nome_categoria}"
                    )
                    lancamentos_criados.append(lancamento)

        # 4. Salvar todos os lançamentos em lote (bulk_create) para performance
        if lancamentos_criados:
            LancamentoSocio.objects.bulk_create(lancamentos_criados)
            self.stdout.write(self.style.SUCCESS(f'Sucesso! {len(lancamentos_criados)} lançamentos de despesas foram criados.'))
        else:
            self.stdout.write(self.style.WARNING('Nenhum lançamento foi criado.'))