from django.db import models
from django.utils import timezone

from .models import ConfiguracaoGlobal


class ActiveManager(models.Manager):
    def get_queryset(self):
        # Por padrão, esconde os deletados
        return super().get_queryset().filter(is_deleted=False)

class TrashManager(models.Manager):
    def get_queryset(self):
        # Mostra apenas os deletados
        return super().get_queryset().filter(is_deleted=True)

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, verbose_name="Está na Lixeira?")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Data da Exclusão")

    # Managers
    objects = ActiveManager()      # Manager padrão (invisível se deletado)
    trash = TrashManager()         # Manager para acessar a lixeira
    all_objects = models.Manager() # Manager para acessar tudo (útil para auditoria)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        # Verifica se a lixeira está ativa nas configurações
        config = ConfiguracaoGlobal.objects.first()
        use_soft_delete = config.lixeira_ativa if config else True

        if use_soft_delete:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(using=using)
        else:
            # Exclusão real
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restaura o item da lixeira"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
        
    def hard_delete(self):
        """Força a exclusão permanente"""
        super().delete()