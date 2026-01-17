import uuid
from decimal import Decimal
from dateutil.relativedelta import relativedelta 

def gerar_parcelas(objeto_base, quantidade_parcelas, form_data):
    """
    Gera N cópias do objeto_base com datas e valores ajustados.
    objeto_base: A instância do modelo (já com os dados do formulário, mas não salva).
    quantidade_parcelas: Inteiro (ex: 10).
    form_data: Dados limpos do formulário (para pegar o valor total original).
    """
    if quantidade_parcelas <= 1:
        objeto_base.save()
        return

    valor_total = form_data.get('valor') or form_data.get('valor_total') or form_data.get('valor_comissao') or Decimal('0.00')
    
    # CORREÇÃO AQUI: Adicionado form_data.get('data_emissao')
    data_inicial = (
        form_data.get('data_vencimento') or 
        form_data.get('data_gasto') or 
        form_data.get('data_pagamento') or 
        form_data.get('data_emissao')
    )
    
    # Cálculo dos valores (evitar dízima)
    valor_parcela = (valor_total / quantidade_parcelas).quantize(Decimal('0.01'))
    diferenca = valor_total - (valor_parcela * quantidade_parcelas)
    
    # Gerar ID único para o grupo
    grupo_id = uuid.uuid4()
    
    descricao_original = getattr(objeto_base, 'descricao', '') or getattr(objeto_base, 'historico', '')
    
    lista_objetos = []
    
    for i in range(quantidade_parcelas):
        # Clona o objeto (na memória)
        nova_parcela = type(objeto_base)()
        
        # Copia todos os campos do original
        for field in objeto_base._meta.fields:
            if field.name not in ['id', 'pk']:
                setattr(nova_parcela, field.name, getattr(objeto_base, field.name))
        
        # Ajustes Específicos da Parcela
        nova_parcela.parcelamento_uuid = grupo_id
        
        # 1. Ajuste de Valor (Soma a diferença na primeira parcela)
        if i == 0:
            valor_final = valor_parcela + diferenca
        else:
            valor_final = valor_parcela
            
        # Define o valor no campo correto (dependendo do Model)
        if hasattr(nova_parcela, 'valor'): nova_parcela.valor = valor_final
        elif hasattr(nova_parcela, 'valor_total'): nova_parcela.valor_total = valor_final
        elif hasattr(nova_parcela, 'valor_comissao'): nova_parcela.valor_comissao = valor_final

        # 2. Ajuste de Data (+1 mês por parcela)
        if data_inicial:
            nova_data = data_inicial + relativedelta(months=i)
            
            # CORREÇÃO AQUI: Adicionado tratamento para 'data_emissao'
            if hasattr(nova_parcela, 'data_vencimento'): nova_parcela.data_vencimento = nova_data
            elif hasattr(nova_parcela, 'data_gasto'): nova_parcela.data_gasto = nova_data
            elif hasattr(nova_parcela, 'data_pagamento'): nova_parcela.data_pagamento = nova_data
            elif hasattr(nova_parcela, 'data_emissao'): nova_parcela.data_emissao = nova_data

        # 3. Ajuste de Descrição
        parcela_str = f" ({i+1}/{quantidade_parcelas})"
        
        if hasattr(nova_parcela, 'descricao'):
            nova_parcela.descricao = f"{descricao_original}{parcela_str}"
        elif hasattr(nova_parcela, 'historico'):
             nova_parcela.historico = f"{descricao_original}{parcela_str}"

        lista_objetos.append(nova_parcela)

    # Salva todos os objetos gerados
    for item in lista_objetos:
        item.save()