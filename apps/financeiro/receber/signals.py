from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Receber, MovimentoBanco, CaixaDiario

@receiver(post_save, sender=Receber)
def gerenciar_recebimento(sender, instance, created, **kwargs):
    # (MANTENHA O CÓDIGO DO post_save IGUAL AO SEU ORIGINAL)
    # Verifica se está recebido
    if instance.status == 'Recebido':
        valor = instance.valor_recebido if instance.valor_recebido else instance.valor
        data = instance.data_recebimento if instance.data_recebimento else instance.data_vencimento
        descricao = f"Receb.: {instance.descricao or 'Venda'} - {instance.cliente or ''}"

        # --- CASO 1: Recebimento no BANCO ---
        if instance.banco_destino:
            if instance.movimento_caixa:
                instance.movimento_caixa.delete()
                Receber.objects.filter(pk=instance.pk).update(movimento_caixa=None)

            if instance.movimento_banco:
                mov = instance.movimento_banco
                mov.banco = instance.banco_destino
                mov.data = data
                mov.valor = valor
                mov.historico = descricao
                mov.save()
            else:
                mov = MovimentoBanco.objects.create(
                    banco=instance.banco_destino,
                    data=data,
                    historico=descricao,
                    tipo='E',
                    valor=valor
                )
                Receber.objects.filter(pk=instance.pk).update(movimento_banco=mov)

        # --- CASO 2: Recebimento no CAIXA ---
        else:
            if instance.movimento_banco:
                instance.movimento_banco.delete()
                Receber.objects.filter(pk=instance.pk).update(movimento_banco=None)

            if instance.movimento_caixa:
                mov = instance.movimento_caixa
                mov.data = data
                mov.valor = valor
                mov.historico = descricao
                mov.save()
            else:
                mov = CaixaDiario.objects.create(
                    data=data,
                    historico=descricao,
                    tipo='E',
                    valor=valor
                )
                Receber.objects.filter(pk=instance.pk).update(movimento_caixa=mov)
    else:
        # Se voltou a ser Pendente
        if instance.movimento_banco: instance.movimento_banco.delete()
        if instance.movimento_caixa: instance.movimento_caixa.delete()
    from apps.financeiro.fluxo.services import FluxoCaixaService
    FluxoCaixaService.clear_fluxo_cache()

@receiver(post_delete, sender=Receber)
def remover_recebimento(sender, instance, **kwargs):
    """
    Remove os movimentos financeiros associados ao excluir o Recebimento.
    Usa tratamento de erro para evitar falhas se o objeto já tiver sido excluído.
    """
    # Remove Movimento Banco com segurança
    if instance.movimento_banco_id:
        try:
            # Tenta buscar e deletar apenas se existir
            if instance.movimento_banco:
                instance.movimento_banco.delete()
        except (MovimentoBanco.DoesNotExist, ValueError, AttributeError):
            pass

    # Remove Movimento Caixa com segurança
    if instance.movimento_caixa_id:
        try:
            if instance.movimento_caixa:
                instance.movimento_caixa.delete()
        except (CaixaDiario.DoesNotExist, ValueError, AttributeError):
            pass