import io
import xlsxwriter
from decimal import Decimal
from datetime import date
import locale

# Tenta configurar locale para data em português
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass

class RescisaoExcelService:
    # --- PALETA DE CORES CORPORATIVA (ZIRK) ---
    COR_AZUL_ESCURO = '#1F497D'
    COR_AZUL_MEDIO  = '#4F81BD'
    COR_CINZA_SECAO = '#EFEFEF'
    COR_TOTAL       = '#FFFFCC'
    COR_BORDA       = '#000000'

    @classmethod
    def _get_formats(cls, wb):
        """Define estilos de célula (Fonte, Bordas, Cores)"""
        base = {'font_name': 'Calibri', 'font_size': 11, 'border': 1, 'border_color': cls.COR_BORDA}
        
        fmt_titulo = base.copy()
        fmt_titulo.update({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 
            'fg_color': cls.COR_AZUL_ESCURO, 'font_color': 'white'
        })
        
        fmt_secao = base.copy()
        fmt_secao.update({
            'bold': True, 'font_size': 12, 'align': 'left', 'valign': 'vcenter', 
            'fg_color': cls.COR_CINZA_SECAO, 'indent': 1
        })
        
        fmt_label = base.copy()
        fmt_label.update({
            'bold': True, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#F9F9F9'
        })
        
        fmt_texto = base.copy()
        fmt_texto.update({'align': 'left', 'valign': 'vcenter', 'text_wrap': False, 'indent': 1})
        
        fmt_center = base.copy()
        fmt_center.update({'align': 'center', 'valign': 'vcenter'})

        fmt_data = base.copy()
        fmt_data.update({'num_format': 'dd/mm/yyyy', 'align': 'center', 'valign': 'vcenter'})
        
        fmt_dinheiro = base.copy()
        fmt_dinheiro.update({
            'num_format': '_-R$ * #,##0.00_-;-R$ * #,##0.00_-;_-R$ * "-"??_-;_-@_-', 
            'align': 'right', 'valign': 'vcenter'
        })
        
        fmt_th = base.copy()
        fmt_th.update({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 
            'fg_color': cls.COR_AZUL_MEDIO, 'font_color': 'white'
        })
        
        fmt_total = base.copy()
        fmt_total.update({
            'bold': True, 'num_format': '_-R$ * #,##0.00_-', 
            'align': 'right', 'valign': 'vcenter', 'bg_color': cls.COR_TOTAL
        })

        fmt_ass = {'font_name': 'Calibri', 'font_size': 11, 'align': 'center', 'valign': 'top'}
        fmt_linha_ass = {'top': 1, 'align': 'center', 'valign': 'top'}

        return {
            'titulo': wb.add_format(fmt_titulo),
            'secao': wb.add_format(fmt_secao),
            'label': wb.add_format(fmt_label),
            'texto': wb.add_format(fmt_texto),
            'center': wb.add_format(fmt_center),
            'data': wb.add_format(fmt_data),
            'money': wb.add_format(fmt_dinheiro),
            'th': wb.add_format(fmt_th),
            'total_label': wb.add_format({'bold': True, 'align': 'right', 'bg_color': cls.COR_TOTAL, 'border': 1}),
            'total_val': wb.add_format(fmt_total),
            'ass': wb.add_format(fmt_ass),
            'linha_ass': wb.add_format(fmt_linha_ass)
        }

    @staticmethod
    def gerar_termo_rescisao(rescisao):
        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet("Rescisão")
        
        ws.hide_gridlines(2)
        ws.set_zoom(85)
        ws.set_paper(9)
        ws.set_margins(0.5, 0.5, 0.5, 0.5)

        fmt = RescisaoExcelService._get_formats(wb)

        # Colunas
        ws.set_column('A:A', 40)
        ws.set_column('B:B', 15)
        ws.set_column('C:C', 18)
        ws.set_column('D:E', 20)

        row = 1
        
        # 1. CABEÇALHO
        ws.merge_range(row, 0, row, 4, "TERMO DE RESCISÃO DE CONTRATO", fmt['titulo'])
        row += 2

        # 2. IDENTIFICAÇÃO
        ws.merge_range(row, 0, row, 4, "1. IDENTIFICAÇÃO", fmt['secao'])
        row += 1

        ws.write(row, 0, "Empregador", fmt['label'])
        ws.merge_range(row, 1, row, 4, "ZIRK MÓVEIS E DECORAÇÕES LTDA", fmt['texto'])
        row += 1
        
        f = rescisao.funcionario
        dt = getattr(f, 'dados_trabalhistas', None)
        ws.write(row, 0, "Colaborador", fmt['label'])
        ws.merge_range(row, 1, row, 2, f.nome.upper(), fmt['texto'])
        ws.write(row, 3, "CPF", fmt['label'])
        cpf = f.documentos.cpf_formatado if hasattr(f, 'documentos') else ""
        ws.write(row, 4, cpf, fmt['center'])
        row += 1

        ws.write(row, 0, "Data Admissão", fmt['label'])
        ws.write(row, 1, dt.data_admissao_contabilidade if dt else "-", fmt['data'])
        ws.write(row, 2, "", fmt['center'])
        ws.write(row, 3, "Salário Base", fmt['label'])
        
        salario_base = dt.salario if dt else 0
        ws.write(row, 4, salario_base, fmt['money'])
        row += 1

        ws.write(row, 0, "Data Demissão", fmt['label'])
        ws.write(row, 1, rescisao.data_demissao, fmt['data'])
        ws.write(row, 2, "", fmt['center'])
        ws.write(row, 3, "Motivo", fmt['label'])
        ws.write(row, 4, rescisao.get_motivo_display(), fmt['center'])
        row += 2

        # 3. CÁLCULOS
        ws.merge_range(row, 0, row, 4, "2. DEMONSTRATIVO DE VERBAS RESCISÓRIAS", fmt['secao'])
        row += 1

        titulos = ["Rubrica", "Referência", "Base Calc.", "Proventos (+)", "Descontos (-)"]
        for col, t in enumerate(titulos):
            ws.write(row, col, t, fmt['th'])
        row += 1

        # --- Montagem dos Itens ---
        itens = []
        
        # add agora recebe explicitamente o base_calc. Se for None, fica vazio.
        def add(nome, valor, tipo, ref="", base_calc=None):
            if valor and valor > 0:
                base_final = base_calc if base_calc is not None else ""
                itens.append((nome, valor, tipo, ref, base_final))

        # -- Proventos --
        # AQUI ESTÁ A REGRA: Salário Base APENAS nestes 3 campos
        add("Saldo de Salário", rescisao.val_dias_trabalhados, 'P', base_calc=salario_base)
        add("Férias Vencidas", rescisao.val_ferias, 'P', base_calc=salario_base)
        add("1/3 Constitucional de Férias", rescisao.val_terco_ferias, 'P', ref="") # Sem base
        add("13º Salário Proporcional", rescisao.val_13_salario, 'P', base_calc=salario_base)
        add("Remunerados (DSR)", rescisao.val_remunerados, 'P') # Sem base
        
        # Outros (Provento)
        if rescisao.outro_tipo == 'P' and rescisao.outro_valor:
            nome_outro = rescisao.outro_nome if rescisao.outro_nome else "Outros Proventos"
            add(nome_outro, rescisao.outro_valor, 'P', ref="")

        # -- Descontos --
        add("Adiantamento Salarial", rescisao.val_adiantamento, 'D')
        add("Atrasos", rescisao.val_atrasos, 'D')
        add("Multa Art. 480 CLT", rescisao.val_multa_480, 'D')
        
        desc_falta = f"Faltas ({rescisao.desc_faltas})" if rescisao.desc_faltas else "Faltas"
        add(desc_falta, rescisao.val_faltas, 'D')

        # Outros (Desconto)
        if rescisao.outro_tipo == 'D' and rescisao.outro_valor:
            nome_outro = rescisao.outro_nome if rescisao.outro_nome else "Outros Descontos"
            add(nome_outro, rescisao.outro_valor, 'D', ref="")

        # Escrita na Planilha
        total_p = Decimal(0)
        total_d = Decimal(0)
        linhas_minimas = 6
        linhas_usadas = 0

        for nome, valor, tipo, ref, base_val in itens:
            ws.write(row, 0, f"  {nome}", fmt['texto'])
            ws.write(row, 1, ref, fmt['center'])
            
            # Escreve Base se existir, senão traço
            if base_val:
                ws.write(row, 2, base_val, fmt['money'])
            else:
                ws.write(row, 2, "-", fmt['center'])
            
            if tipo == 'P':
                ws.write(row, 3, valor, fmt['money'])
                ws.write(row, 4, "", fmt['money'])
                total_p += valor
            else:
                ws.write(row, 3, "", fmt['money'])
                ws.write(row, 4, valor, fmt['money'])
                total_d += valor
            
            row += 1
            linhas_usadas += 1

        # Linhas vazias estéticas
        while linhas_usadas < linhas_minimas:
            for c in range(5):
                f_vazio = fmt['money'] if c >= 2 else fmt['texto']
                ws.write(row, c, "", f_vazio) 
            row += 1
            linhas_usadas += 1

        # Totais
        ws.write(row, 0, "SUBTOTAL", fmt['total_label'])
        ws.write(row, 1, "", fmt['total_label'])
        ws.write(row, 2, "", fmt['total_label'])
        ws.write(row, 3, total_p, fmt['total_val'])
        ws.write(row, 4, total_d, fmt['total_val'])
        row += 2

        # Líquido
        liquido = total_p - total_d
        ws.merge_range(row, 0, row, 3, "VALOR LÍQUIDO A RECEBER", fmt['titulo'])
        ws.write(row, 4, liquido, fmt['total_val'])
        row += 4

        # 4. QUITAÇÃO
        ws.merge_range(row, 0, row, 4, "3. QUITAÇÃO", fmt['secao'])
        row += 2

        texto_legal = (
            f"Eu, {f.nome}, declaro ter recebido da empresa ZIRK MÓVEIS E DECORAÇÕES LTDA "
            f"a importância líquida de R$ {liquido:,.2f}, referente ao pagamento das verbas "
            f"rescisórias discriminadas neste documento, outorgando plena e geral quitação."
        )
        
        fmt_texto_livre = wb.add_format({'font_name': 'Calibri', 'font_size': 11, 'align': 'justify', 'text_wrap': True})
        ws.merge_range(row, 0, row+2, 4, texto_legal, fmt_texto_livre)
        row += 5

        # Assinaturas
        data_hoje = date.today().strftime('%d/%m/%Y')
        ws.merge_range(row, 0, row, 4, f"Belo Horizonte, {data_hoje}", fmt['ass'])
        row += 4

        ws.merge_range(row, 0, row, 1, "", fmt['linha_ass'])
        ws.merge_range(row, 3, row, 4, "", fmt['linha_ass'])
        row += 1
        
        ws.merge_range(row, 0, row, 1, "ZIRK MÓVEIS E DECORAÇÕES LTDA", fmt['ass'])
        ws.merge_range(row, 3, row, 4, f.nome, fmt['ass'])

        wb.close()
        output.seek(0)
        return output