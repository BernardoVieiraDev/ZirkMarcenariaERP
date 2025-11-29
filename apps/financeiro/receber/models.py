from django.db import models

class Receber(models.Model):
    cliente = models.CharField('Cliente', max_length=120)
    desc = models.CharField('Descrição', max_length=255, blank=True)
    value = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    when = models.DateField('Recebimento', null=True, blank=True)
    status = models.CharField('Status', max_length=30, default='Agendado')

    def __str__(self):
        return f"{self.cliente} - {self.value}"

