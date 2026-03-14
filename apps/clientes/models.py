# zirk_rh_financeiro/apps/clientes/models.py

from django.db import models

from apps.configuracoes.mixin import SoftDeleteMixin


class Cliente(SoftDeleteMixin):
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, verbose_name="CPF", unique=True, null=True, blank=True)
    rg = models.CharField(max_length=20, verbose_name="RG", null=True, blank=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone", null=True, blank=True)
    email = models.EmailField(max_length=255, verbose_name="E-mail", null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    chave_pix = models.CharField(max_length=255, verbose_name="Chave PIX", null=True, blank=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo

    @property
    def cpf_formatado(self):
        if self.cpf and len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf


class EnderecoCliente(models.Model):
    TIPO_CHOICES = [
        ('RESIDENCIAL', 'Endereço Residencial'),
        ('OBRA', 'Endereço da Obra'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='enderecos', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='RESIDENCIAL', null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    endereco = models.CharField(max_length=255, verbose_name="Logradouro", null=True, blank=True)
    numero = models.CharField(max_length=10, verbose_name="Número", null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True)
    complemento = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.endereco}, {self.numero}"