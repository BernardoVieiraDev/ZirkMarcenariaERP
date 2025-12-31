from django.db import models
from django.utils import timezone

class Socio(models.Model):
    nome = models.CharField(max_length=150)
    
    def __str__(self):
        return self.nome

class CategoriaSocio(models.Model):
    # Grupos exatos da Planilha Sebrae
    GRUPO_CHOICES = [
        ('RENDA_FAMILIAR', 'Renda Familiar'),
        ('HABITACAO', 'Habitação'),
        ('AUTOMOVEL', 'Automóvel'),
        ('DESPESAS_PESSOAIS', 'Despesas Pessoais'),
        ('SAUDE', 'Saúde'),
        ('EDUCACAO', 'Educação'),
        ('LAZER', 'Lazer'),
        ('DEPENDENTES', 'Dependentes'),
        ('INVESTIMENTOS', 'Investimentos/Dívidas'),
        ('OUTROS', 'Outros'),
    ]

    grupo = models.CharField(max_length=50, choices=GRUPO_CHOICES)
    nome = models.CharField(max_length=100) # Ex: Aluguel, Escola, IPTU
    
    class Meta:
        ordering = ['grupo', 'nome']
        unique_together = ('grupo', 'nome') # Evita duplicatas

    def __str__(self):
        return f"{self.get_grupo_display()} - {self.nome}"

class LancamentoSocio(models.Model):
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, verbose_name="Sócio")
    categoria = models.ForeignKey(CategoriaSocio, on_delete=models.PROTECT, verbose_name="Categoria")
    data = models.DateField("Data", default=timezone.now)
    valor = models.DecimalField("Valor (R$)", max_digits=12, decimal_places=2)
    observacao = models.CharField("Observação", max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-data']