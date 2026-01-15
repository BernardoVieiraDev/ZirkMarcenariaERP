from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.apps import apps
from apps.configuracoes.models import ConfiguracaoGlobal

# Lista corrigida de modelos e seus campos de data
MODELS_TO_CLEAN_HISTORY = [
    ('pagar', 'Boleto', 'data_vencimento'),
    ('pagar', 'GastoGeral', 'data_gasto'),
    ('pagar', 'GastoUtilidade', 'data_vencimento'),
    ('pagar', 'FaturaCartao', 'data_vencimento'),
    ('pagar', 'GastoImovel', 'data_vencimento'),
    ('pagar', 'GastoVeiculoConsorcio', 'data_vencimento'),
    ('pagar', 'GastoContabilidade', 'data_vencimento'),
    ('pagar', 'PrestacaoEmprestimo', 'data_vencimento'),
    ('pagar', 'Cheque', 'data_emissao'),
    ('pagar', 'GastoGasolina', 'data_gasto'), # CORRIGIDO: Era data_pagamento
    ('pagar', 'ComissaoArquiteto', 'data_pagamento'), # Verifique se este modelo tem este campo
    ('receber', 'Receber', 'data_vencimento'),
    ('receber', 'MovimentoBanco', 'data'),
    ('comissionamento', 'ContratoRT', 'data_contrato'),
    ('pagar', 'FolhaPagamento', 'data_referencia'),
    ('rescisao', 'Rescisao', 'data_demissao'),
    ('ferias', 'Ferias', 'periodo__data_fim'), 
]

class Command(BaseCommand):
    help = 'Executa limpeza da lixeira e arquivamento de dados antigos.'

    def handle(self, *args, **kwargs):
        config = ConfiguracaoGlobal.objects.first()
        now = timezone.now()

        # --- CONFIGURAÇÃO DE TEMPO (MESES) ---
        # Tenta pegar do banco, se não existir usa 18 como padrão
        meses_retencao = 18
        if config and hasattr(config, 'meses_retencao_historico'):
            meses_retencao = config.meses_retencao_historico
        
        # Data de corte
        cutoff_hist = now - relativedelta(months=meses_retencao)

        self.stdout.write(self.style.WARNING(f"DATA DE CORTE: {cutoff_hist.date()} ({meses_retencao} meses atrás)"))

        # --- 1. LIXEIRA ---
        if config and config.lixeira_ativa:
            cutoff_lixeira = now - relativedelta(days=config.dias_retencao_lixeira)
            self.stdout.write(f"\n--- Limpando Lixeira (Antes de {cutoff_lixeira.date()}) ---")
            
            for model in apps.get_models():
                if hasattr(model, 'trash'):
                    qs = model.trash.filter(deleted_at__lt=cutoff_lixeira)
                    count = qs.count()
                    if count > 0:
                        qs.delete()
                        self.stdout.write(self.style.SUCCESS(f"Lixeira - {model.__name__}: {count} excluídos."))

        # --- 2. HISTÓRICO ---
        self.stdout.write(f"\n--- Arquivando Histórico (PAGOS antes de {cutoff_hist.date()}) ---")

        for app_label, model_name, date_field in MODELS_TO_CLEAN_HISTORY:
            try:
                ModelClass = apps.get_model(app_label, model_name)
                
                filter_kwargs = {
                    f"{date_field}__lt": cutoff_hist,
                    'is_deleted': False 
                }
                
                if hasattr(ModelClass, 'status'):
                    filter_kwargs['status__in'] = ['PAGO', 'Pago', 'CONCLUIDO', 'Concluido', 'RECEBIDO', 'Recebido']

                old_items = ModelClass.objects.filter(**filter_kwargs)
                count = old_items.count()
                
                if count > 0:
                    old_items.update(is_deleted=True, deleted_at=now)
                    self.stdout.write(self.style.SUCCESS(f"Histórico - {model_name}: {count} arquivados."))
                    
            except LookupError:
                pass
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao processar {model_name}: {e}"))
    
        self.stdout.write(self.style.SUCCESS("\n--- PROCESSO CONCLUÍDO ---"))