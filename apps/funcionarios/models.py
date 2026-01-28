from django.db import models
from django.db import transaction # Importante para garantir integridade
from apps.configuracoes.mixin import SoftDeleteMixin

# Choices (Mantenha igual)
class GrauInstrucao(models.IntegerChoices):
    # ... (mantenha as opções)
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
    # ... (mantenha as opções)
    SOLTEIRO = "SOL", "Solteiro(a)"
    CASADO = "CAS", "Casado(a)"
    DIVORCIADO = "DIV", "Divorciado(a)"
    VIUVO = "VIU", "Viúvo(a)"
    UNIAO_ESTAVEL = "UNI", "União Estável"

class Sexo(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMININO = "F", "Feminino"
    OUTRO = "O", "Outro"

# --- MODELO PRINCIPAL ---
class Funcionario(SoftDeleteMixin):
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
    
    def delete(self, using=None, keep_parents=False):
        """
        Sobrescreve o delete para propagar o Soft Delete para os modelos 1-to-1 relacionados.
        """
        with transaction.atomic():
            # Tenta excluir (soft delete) os relacionados se existirem
            if hasattr(self, 'endereco'):
                self.endereco.delete(using=using)
            
            if hasattr(self, 'documentos'):
                self.documentos.delete(using=using)
                
            if hasattr(self, 'dados_trabalhistas'):
                self.dados_trabalhistas.delete(using=using)
            
            # Chama o delete do SoftDeleteMixin (que seta is_deleted=True no Funcionario)
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restaura o funcionário e seus dados relacionados.
        """
        with transaction.atomic():
            # Restaura os relacionados usando o manager 'trash' (pois estão deletados)
            # Nota: O acesso direto (self.endereco) pode falhar se estiver deletado dependendo do Manager padrão,
            # então acessamos via query explícita na lixeira ou verify check.
            
            # Como o SoftDeleteMixin esconde itens deletados do 'objects', usamos o 'all_objects' ou 'trash'
            
            # Endereço
            try:
                end = EnderecoFuncionario.all_objects.get(funcionario=self)
                if end.is_deleted:
                    end.restore()
            except EnderecoFuncionario.DoesNotExist:
                pass

            # Documentos
            try:
                docs = DocumentosFuncionario.all_objects.get(funcionario=self)
                if docs.is_deleted:
                    docs.restore()
            except DocumentosFuncionario.DoesNotExist:
                pass

            # Dados Trabalhistas
            try:
                trab = DadosTrabalhistas.all_objects.get(funcionario=self)
                if trab.is_deleted:
                    trab.restore()
            except DadosTrabalhistas.DoesNotExist:
                pass

            # Restaura o próprio funcionário
            super().restore()

# --- MODELOS RELACIONADOS (AGORA COM SoftDeleteMixin) ---

class EnderecoFuncionario(SoftDeleteMixin): # Alterado de models.Model para SoftDeleteMixin
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

class DocumentosFuncionario(SoftDeleteMixin): # Alterado de models.Model para SoftDeleteMixin
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

    @property
    def cpf_formatado(self):
        if not self.cpf: return None
        numeros = ''.join(filter(str.isdigit, self.cpf))
        if len(numeros) == 11:
            return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
        return self.cpf

class DadosTrabalhistas(SoftDeleteMixin): # Alterado de models.Model para SoftDeleteMixin
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