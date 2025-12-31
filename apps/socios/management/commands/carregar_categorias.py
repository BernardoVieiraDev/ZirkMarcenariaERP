from django.core.management.base import BaseCommand
from apps.socios.models import CategoriaSocio

class Command(BaseCommand):
    help = 'Carrega as categorias padrão da Planilha Sebrae'

    def handle(self, *args, **kwargs):
        # Mapeamento da Planilha
        dados = {
            'RENDA_FAMILIAR': ['Salários', '13º Salário', 'Férias', 'Retirada de Poupança', 'Empréstimos', 'Outros'],
            'HABITACAO': ['Aluguel/Prestação', 'Condomínio', 'IPTU', 'Energia Elétrica', 'Água', 'Gás', 'Manutenção/Reparos', 'Telefone Fixo', 'Celular', 'Internet/TV Cabo', 'Empregada/Diarista', 'Supermercado/Feira/Padaria'],
            'AUTOMOVEL': ['Prestação', 'Seguro', 'Combustível', 'Lavagens', 'IPVA', 'Mecânico', 'Multas', 'Outros'],
            'DESPESAS_PESSOAIS': ['Higiene Pessoal', 'Cosméticos', 'Cabeleireiro/Barbeiro', 'Vestuário', 'Academia', 'Presentes'],
            'SAUDE': ['Plano de Saúde', 'Médicos/Dentistas', 'Medicamentos', 'Óculos/Lentes'],
            'EDUCACAO': ['Matrícula', 'Mensalidade Escolar', 'Material Escolar/Uniformes', 'Cursos Extras', 'Transporte Escolar'],
            'LAZER': ['Cinema/Teatro/Shows', 'Livros/Revistas/Jornais', 'Clubes/Associações', 'Restaurantes/Bares', 'Viagens'],
            'DEPENDENTES': ['Mesada', 'Vestuário', 'Outros'],
            'INVESTIMENTOS': ['Poupança', 'Previdência Privada', 'Ações/Fundos', 'Pagamento de Dívidas'],
            'OUTROS': ['Doações/Dízimos', 'Imposto de Renda', 'INSS/Previdência']
        }

        for grupo, itens in dados.items():
            for item in itens:
                obj, created = CategoriaSocio.objects.get_or_create(grupo=grupo, nome=item)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Criado: {item}'))