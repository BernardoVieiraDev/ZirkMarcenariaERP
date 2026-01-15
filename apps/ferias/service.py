from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from .models import PeriodoAquisitivo
from apps.funcionarios.models import Funcionario

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from .models import PeriodoAquisitivo
from apps.funcionarios.models import Funcionario

def gerar_novo_periodo_aquisitivo(funcionario):
    # 1. Validações iniciais (mantém as existentes)
    if getattr(funcionario, 'is_deleted', False):
        return None

    if not hasattr(funcionario, 'dados_trabalhistas'):
        return None
    
    dados = funcionario.dados_trabalhistas
    # Data base é a admissão (marcenaria tem preferência conforme seu código original)
    data_admissao = dados.data_admissao_marcenaria or dados.data_admissao_contabilidade
    if not data_admissao:
        return None

    ultimo_periodo = funcionario.periodos_aquisitivos.order_by('-data_fim').first()
    hoje = timezone.now().date()
    
    # 2. Definição da Data de Corte (Ex: 2 anos atrás)
    # Períodos mais antigos que isso serão ignorados se não existirem no banco.
    data_limite_retroativa = hoje - relativedelta(years=2)

    data_inicio_calculada = None

    # --- Lógica de Definição do Início ---
    if not ultimo_periodo:
        # Cenário A: Nenhum período existe. Deveria começar na admissão.
        data_inicio_calculada = data_admissao
    else:
        # Cenário B: Já existem períodos. O próximo seria o fim do último + 1 dia.
        if ultimo_periodo.data_fim >= hoje:
            return None  # Período atual ainda está vigente
            
        # Nota: Seu código original usava +1 dia. 
        # Idealmente o período seguinte começa no mesmo dia do ano que terminou o anterior (ex: 01/01 a 01/01).
        # Mantive sua lógica de +1 dia para não quebrar compatibilidade, mas avalie ajustar.
        data_inicio_calculada = ultimo_periodo.data_fim + timedelta(days=1)

    # 3. Verificação de "Salto Temporal" (A Correção Principal)
    # Se a data calculada for muito antiga, calculamos o ciclo mais atual
    if data_inicio_calculada < data_limite_retroativa:
        # Calcula o aniversário de admissão no ano corrente
        aniversario_ano_atual = date(hoje.year, data_admissao.month, data_admissao.day)
        
        # Se ainda não fez aniversário este ano, o período vigente começou ano passado
        if aniversario_ano_atual > hoje:
            inicio_vigente = aniversario_ano_atual - relativedelta(years=1)
        else:
            inicio_vigente = aniversario_ano_atual
            
        # Segurança: Garante que não vamos criar um período que sobreponha o último (caso raro de inconsistência)
        if ultimo_periodo and inicio_vigente <= ultimo_periodo.data_fim:
            data_inicio_calculada = ultimo_periodo.data_fim + timedelta(days=1)
        else:
            data_inicio_calculada = inicio_vigente

    # 4. Criação do Período
    if data_inicio_calculada:
        # Garante que não estamos criando datas futuras absurdas
        limite_futuro = hoje + relativedelta(months=4)

        if data_inicio_calculada > limite_futuro:
            return None

        data_fim = data_inicio_calculada + relativedelta(years=1) 
        
        # Opcional: Validação extra para não duplicar se houver race condition
        if PeriodoAquisitivo.objects.filter(
            funcionario=funcionario, 
            data_inicio=data_inicio_calculada
        ).exists():
            return None

        novo_periodo = PeriodoAquisitivo.objects.create(
            funcionario=funcionario,
            data_inicio=data_inicio_calculada,
            data_fim=data_fim,
            dias_direito=30
        )
        return novo_periodo

    return None

def atualizar_todos_periodos():
    """
    Roda a verificação para TODOS os funcionários ativos.
    """
    funcionarios = Funcionario.objects.all() # O SoftDeleteMixin já deve filtrar os deletados
    for func in funcionarios:
        # Garante que não pega deletados se o manager padrão não filtrar
        if getattr(func, 'is_deleted', False):
            continue
        gerar_novo_periodo_aquisitivo(func)