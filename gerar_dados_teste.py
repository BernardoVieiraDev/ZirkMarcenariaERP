import os
import django
import random
from decimal import Decimal
from datetime import timedelta

# 1. Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.socios.models import Socio, LancamentoSocio, CategoriaSocio

# 2. DADOS (Copiados da sua lista)
ESTRUTURA_COMPLETA = {
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

def obter_valor_realista(item):
    """Gera um valor aproximado baseado no nome do item"""
    item = item.lower()
    if 'salário' in item: return Decimal(random.uniform(5000, 15000))
    if 'férias' in item: return Decimal(random.uniform(6000, 8000))
    if 'aluguel' in item or 'prestação' in item: return Decimal(random.uniform(1500, 4000))
    if 'netflix' in item: return Decimal('55.90')
    if 'luz' in item: return Decimal(random.uniform(200, 500))
    if 'internet' in item: return Decimal('149.90')
    if 'supermercado' in item: return Decimal(random.uniform(500, 2000))
    if 'escola' in item: return Decimal(random.uniform(1200, 3000))
    if 'combustível' in item: return Decimal(random.uniform(200, 400))
    if 'restaurantes' in item: return Decimal(random.uniform(100, 400))
    return Decimal(random.uniform(50, 300))

def executar():
    print("🧹 Apagando lançamentos antigos de sócios...")
    LancamentoSocio.objects.all().delete()
    
    print("🚀 Iniciando criação dos novos registros...")
    
    # Garante os sócios
    socios = []
    for nome in ["Bernardo CEO", "Sócio Investidor"]:
        s, _ = Socio.objects.get_or_create(nome=nome)
        socios.append(s)

    hoje = timezone.now().date()
    total = 0

    # Loop Principal
    for cat_nome, lista_subitens in ESTRUTURA_COMPLETA.items():
        
        # Define se é Entrada ou Saída
        tipo_mov = 'ENTRADA' if cat_nome == 'RENDA_FAMILIAR' else 'SAIDA'
        
        # 1. Tenta criar Categoria com 'tipo'
        # Se o campo 'tipo' não existir em CategoriaSocio, ele ignora e cria sem.
        try:
            cat_obj, _ = CategoriaSocio.objects.get_or_create(nome=cat_nome, defaults={'tipo': tipo_mov})
        except:
            # Fallback se o model CategoriaSocio não tiver 'tipo'
            cat_obj, _ = CategoriaSocio.objects.get_or_create(nome=cat_nome)

        print(f"  📂 Processando Categoria: {cat_nome}...")

        for subitem in lista_subitens:
            # Cria 4 registros para CADA subitem
            for _ in range(4):
                socio = random.choice(socios)
                data_lanc = hoje - timedelta(days=random.randint(0, 150))
                valor = obter_valor_realista(subitem)

                # 2. Criação do Lançamento (SEM O CAMPO TIPO, que causou o erro)
                LancamentoSocio.objects.create(
                    socio=socio,
                    categoria=cat_obj,
                    data=data_lanc,
                    valor=valor.quantize(Decimal('0.01')),
                    observacao=subitem  # AQUI ESTÁ O NOME (ex: Netflix)
                )
                total += 1

    print("="*50)
    print(f"✅ FINALIZADO! {total} lançamentos criados.")
    print("="*50)

if __name__ == "__main__":
    executar()