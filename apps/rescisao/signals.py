from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Rescisao

@receiver(post_save, sender=Rescisao)
def desativar_funcionario_apos_rescisao(sender, instance, created, **kwargs):
    """
    Ao criar ou salvar uma Rescisão, movemos o funcionário para a lixeira (Soft Delete).
    Isso impede que ele apareça em seletores globais de funcionários ativos.
    """
    if instance.funcionario and not instance.funcionario.is_deleted:
        # Move para a lixeira (Soft Delete)
        instance.funcionario.delete()

@receiver(post_delete, sender=Rescisao)
def reativar_funcionario_ao_excluir_rescisao(sender, instance, **kwargs):
    """
    Se a rescisão for excluída (estorno), podemos restaurar o funcionário
    se desejado. (Opcional, depende da regra de negócio)
    """
    if instance.funcionario and instance.funcionario.is_deleted:
        # Restaura o funcionário (tira da lixeira)
        instance.funcionario.restore()