from django.db import models


# Choices
class GrauInstrucao(models.IntegerChoices):
    ANALFABETO = 1, "Analfabeto"
    FUNDAMENTAL_INCOMPLETO = 2, "1ª a 4ª Série incompleta"
    FUNDAMENTAL_COMPLETO = 3, "4ª Série completa"
    FUNDAMENTAL_2_INCOMPLETO = 4, "5ª a 8ª Série incompleta"
    FUNDAMENTAL_2_COMPLETO = 5, "1º Grau completo"
    MEDIO_INCOMPLETO = 6, "2º Grau incompleto"
    MEDIO_COMPLETO = 7, "2º Grau completo"
    SUPERIOR_INCOMPLETO = 8, "Superior incompleto"
    SUPERIOR_COMPLETO = 9, "Superior completo"

class EstadoCivil(models.TextChoices):
    SOLTEIRO = "SOL", "Solteiro(a)"
    CASADO = "CAS", "Casado(a)"
    DIVORCIADO = "DIV", "Divorciado(a)"
    VIUVO = "VIU", "Viúvo(a)"
    UNIAO_ESTAVEL = "UNI", "União Estável"

class Sexo(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMININO = "F", "Feminino"
    OUTRO = "O", "Outro"

# Model principal
class Funcionario(models.Model):
    nome = models.CharField(max_length=200)
    data_nascimento = models.DateField(null=True, blank=True)
    natural_de = models.CharField(max_length=100, blank=True, null=True)
    sexo = models.CharField(
        max_length=1, 
        choices=Sexo.choices,
        default=Sexo.OUTRO)


    grau_instrucao = models.IntegerField(choices=GrauInstrucao.choices, null=True, blank=True)
    estado_civil = models.CharField(max_length=3, choices=EstadoCivil.choices, blank=True, null=True)
    conjuge = models.CharField(max_length=200, blank=True, null=True)

    nome_pai = models.CharField(max_length=200, blank=True, null=True)
    nome_mae = models.CharField(max_length=200, blank=True, null=True)

    numero_filhos = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nome

# Endereço separado
class EnderecoFuncionario(models.Model):
    funcionario = models.OneToOneField(Funcionario, on_delete=models.CASCADE, related_name="endereco")
    endereco = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)


class TipoDocumentoPis(models.TextChoices):
    PIS = "PIS", "PIS"
    PASEP = "PASEP", "PASEP"

# Documentos
class DocumentosFuncionario(models.Model):
    funcionario = models.OneToOneField(Funcionario, on_delete=models.CASCADE, related_name="documentos")

    pis_pasep = models.CharField(max_length=20, blank=True, null=True, verbose_name="PIS/PASEP")
    rg = models.CharField(max_length=20, blank=True, null=True)
    rg_orgao_expedidor = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True)
    ctps_numero = models.CharField(max_length=20, blank=True, null=True)
    ctps_serie = models.CharField(max_length=10, blank=True, null=True)
    ctps_uf = models.CharField(max_length=2, blank=True, null=True)
    titulo_eleitor = models.CharField(max_length=20, blank=True, null=True)
    certificado_reservista = models.CharField(max_length=20, blank=True, null=True)

    tipo_pis_pasep = models.CharField(
            max_length=5,
            choices=TipoDocumentoPis.choices,
            default=TipoDocumentoPis.PIS,
            blank=True, 
            null=True,
            verbose_name="Tipo (PIS/PASEP)"
        )

    rg = models.CharField(max_length=20, blank=True, null=True)


    @property
    def cpf_formatado(self):
        """Retorna o CPF formatado como 000.000.000-00"""
        if not self.cpf:
            return None
        
        # Garante que só temos números
        numeros = ''.join(filter(str.isdigit, self.cpf))
        
        if len(numeros) == 11:
            return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
        
        return self.cpf # Retorna original se não tiver 11 dígitos

# Dados trabalhistas
class DadosTrabalhistas(models.Model):
    funcionario = models.OneToOneField(Funcionario, on_delete=models.CASCADE, related_name="dados_trabalhistas")

    data_admissao_contabilidade = models.DateField()
    data_admissao_marcenaria = models.DateField()
    funcao = models.CharField(max_length=100)
    cbo = models.CharField(max_length=20, blank=True, null=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    insalubridade = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentual (%)", null=True, blank=True)

    horario_trabalho = models.CharField(max_length=200, blank=True, null=True)

    contrato_experiencia_dias = models.PositiveIntegerField(null=True, blank=True)
    prorrogação_dias = models.PositiveIntegerField(null=True, blank=True)


