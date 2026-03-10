from django.apps import \
    apps  # Necessário para buscar modelos sem import circular
from django.db import models, transaction

from apps.configuracoes.mixin import SoftDeleteMixin


# Choices (Mantidos iguais)
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
    chave_pix = models.CharField(max_length=255, verbose_name="Chave PIX", null=True, blank=True)

    def __str__(self):
        return self.nome
    
    def delete(self, using=None, keep_parents=False):
        """
        Sobrescreve o delete para propagar o Soft Delete para os modelos relacionados.
        """
        with transaction.atomic():
            # 1. Relacionamentos Básicos (OneToOne)
            if hasattr(self, 'endereco'):
                self.endereco.delete(using=using)
            
            if hasattr(self, 'documentos'):
                self.documentos.delete(using=using)
                
            if hasattr(self, 'dados_trabalhistas'):
                self.dados_trabalhistas.delete(using=using)

            # 2. Banco de Horas (OneToOne - relacionado como 'banco_horas')
            if hasattr(self, 'banco_horas'):
                self.banco_horas.delete(using=using)

            # 3. Lançamentos de Horas (ForeignKey - relacionado como 'lancamentos_horas')
            # Iteramos para garantir que o método .delete() do SoftDeleteMixin de cada lançamento seja chamado
            for lancamento in self.lancamentos_horas.all():
                lancamento.delete(using=using)

            for beneficio in self.beneficios.all():
                beneficio.delete(using=using)
            
            # Chama o delete do SoftDeleteMixin no próprio funcionário
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """
        Restaura o funcionário e seus dados relacionados.
        """
        with transaction.atomic():
            # Recupera os modelos via apps.get_model para evitar Import Circular
            BancoHoras = apps.get_model('banco_horas', 'BancoHoras')
            LancamentoHoras = apps.get_model('banco_horas', 'LancamentoHoras')

            # --- Restaura Relacionamentos Básicos ---
            try:
                end = EnderecoFuncionario.all_objects.get(funcionario=self)
                if end.is_deleted: end.restore()
            except EnderecoFuncionario.DoesNotExist: pass

            try:
                docs = DocumentosFuncionario.all_objects.get(funcionario=self)
                if docs.is_deleted: docs.restore()
            except DocumentosFuncionario.DoesNotExist: pass

            try:
                trab = DadosTrabalhistas.all_objects.get(funcionario=self)
                if trab.is_deleted: trab.restore()
            except DadosTrabalhistas.DoesNotExist: pass

            # --- Restaura Banco de Horas ---
            try:
                bh = BancoHoras.all_objects.get(funcionario=self)
                if bh.is_deleted: bh.restore()
            except BancoHoras.DoesNotExist: pass

            # --- Restaura Lançamentos de Horas ---
            # Busca todos os lançamentos (inclusive deletados) deste funcionário que estão na lixeira
            lancamentos_deletados = LancamentoHoras.trash.filter(funcionario=self)
            for lancamento in lancamentos_deletados:
                lancamento.restore()

            # --- Restaura Benefícios ---
            beneficios_deletados = BeneficioFuncionario.trash.filter(funcionario=self)
            for beneficio in beneficios_deletados:
                beneficio.restore()

            # Restaura o próprio funcionário
            super().restore()

# --- MODELOS RELACIONADOS ---

class BeneficioFuncionario(SoftDeleteMixin):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="beneficios")
    nome = models.CharField(max_length=100, verbose_name="Nome do Benefício (Ex: Odontológico)")
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor a Descontar (R$)")

    def __str__(self):
        return f"{self.nome} - R$ {self.valor_desconto}"

class EnderecoFuncionario(SoftDeleteMixin):
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

class DocumentosFuncionario(SoftDeleteMixin):
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

class DadosTrabalhistas(SoftDeleteMixin):
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