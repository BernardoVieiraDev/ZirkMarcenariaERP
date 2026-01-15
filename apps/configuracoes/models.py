from django.core.exceptions import ValidationError
from django.db import models


class ConfiguracaoGlobal(models.Model):
    # --- Configurações da Lixeira (Soft Delete) ---
    lixeira_ativa = models.BooleanField(
        default=True, 
        verbose_name="Ativar Lixeira",
        help_text="Se desativado, exclusões serão permanentes imediatamente."
    )
    dias_retencao_lixeira = models.IntegerField(
        default=180, 
        verbose_name="Dias de retenção na Lixeira",
        help_text="Após este período, itens na lixeira serão excluídos permanentemente (ex: 180 dias = 6 meses)."
    )

    # --- Configurações de Limpeza de Dados Antigos (Histórico) ---
    limpeza_automatica_ativa = models.BooleanField(default=True, verbose_name="Ativar Limpeza de Histórico?")
    meses_retencao_historico = models.IntegerField(default=18, verbose_name="Meses de Retenção do Histórico (Padrão: 18)")
    
    # Controle para garantir que só exista um objeto
    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracaoGlobal.objects.exists():
            raise ValidationError('Apenas uma configuração global pode existir.')
        return super(ConfiguracaoGlobal, self).save(*args, **kwargs)

    def __str__(self):
        return "Configuração Global do Sistema"

    class Meta:
        verbose_name = "Configuração Global"
        verbose_name_plural = "Configurações Globais"