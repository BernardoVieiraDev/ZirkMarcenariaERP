from django.core.management.base import BaseCommand
from apps.socios.models import CategoriaSocio

class Command(BaseCommand):
    help = 'Carrega as categorias padrão da Planilha Sebrae'

    def handle(self, *args, **kwargs):
        # Mapeamento EXATO da Planilha "1-Desp Sócios.csv"
        dados = {
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

        # Iterar na ordem exata de definição do dicionário (Python 3.7+ mantém ordem de inserção)
        for grupo, itens in dados.items():
            for item in itens:
                obj, created = CategoriaSocio.objects.get_or_create(grupo=grupo, nome=item)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Criado: {grupo} - {item}'))
                else:
                    self.stdout.write(f'Já existe: {grupo} - {item}')