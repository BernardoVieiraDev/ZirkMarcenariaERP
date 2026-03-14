# zirk_rh_financeiro/apps/clientes/models.py

from django.db import models

from apps.configuracoes.mixin import SoftDeleteMixin


class Cliente(SoftDeleteMixin):
    TIPO_PESSOA_CHOICES = [
        ('F', 'Pessoa Física'),
        ('J', 'Pessoa Jurídica'),
    ]
    
    tipo_pessoa = models.CharField(max_length=1, choices=TIPO_PESSOA_CHOICES, default='F', verbose_name="Tipo de Pessoa")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo / Razão Social")
    
    # Dados Pessoa Física
    cpf = models.CharField(max_length=14, verbose_name="CPF", unique=True, null=True, blank=True)
    rg = models.CharField(max_length=20, verbose_name="RG", null=True, blank=True)
    
    # Dados Pessoa Jurídica
    cnpj = models.CharField(max_length=18, verbose_name="CNPJ", unique=True, null=True, blank=True)
    inscricao_estadual = models.CharField(max_length=30, verbose_name="Inscrição Estadual", null=True, blank=True)
    
    # Contatos e Outros
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

    @property
    def cnpj_formatado(self):
        if self.cnpj and len(self.cnpj) == 14:
            return f"{self.cnpj[:2]}.{self.cnpj[2:5]}.{self.cnpj[5:8]}/{self.cnpj[8:12]}-{self.cnpj[12:]}"
        return self.cnpj

    @property
    def documento_principal(self):
        if self.tipo_pessoa == 'J' and self.cnpj:
            return self.cnpj_formatado
        return self.cpf_formatado


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