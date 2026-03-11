import io
import xlsxwriter
from decimal import Decimal
from django.db.models import Sum

class FuncionarioFolhaExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Formatos padrão com TÍTULO."""
        return {
            'title': workbook.add_format({
                'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
                'font_name': 'Calibri'
            }),
            'header_table': workbook.add_format({
                'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
                'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF',
                'font_name': 'Calibri', 'border': 1
            }),
            'data_text': workbook.add_format({
                'align': 'left', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10
            }),
            'data_date': workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': 'dd/mm/yyyy'
            }),
            'data_money': workbook.add_format({
                'align': 'right', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10,
                'num_format': 'R$ #,##0.00'
            }),
            'total_row_money': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1,
                'font_name': 'Calibri', 'font_size': 10, 'bg_color': '#FFFFCC',
                'num_format': 'R$ #,##0.00'
            }),
            'total_label': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter',
                'font_name': 'Calibri', 'font_size': 11, 'bg_color': cls.COR_FUNDO_SECAO,
                'border': 1
            }),
            'total_final_money': workbook.add_format({
                'bold': True, 'align': 'right', 'valign': 'vcenter',
                'font_name': 'Calibri', 'font_size': 11, 'bg_color': cls.COR_FUNDO_SECAO,
                'num_format': 'R$ #,##0.00', 'border': 1
            })
        }

    # =========================================================================
    # RELATÓRIO GERAL (USADO PELA ROTA DE RELATÓRIOS)
    # =========================================================================
    @staticmethod
    def gerar_relatorio_folha(pagamentos, workbook=None):
        """
        Recebe um QuerySet de FolhaPagamento e retorna um buffer Excel (se workbook=None).
        """
        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            # Prefetch benefits para não penalizar o banco de dados (N+1 queries)
            pagamentos = pagamentos.prefetch_related('funcionario__beneficios')

            ws = workbook.add_worksheet("Folha de Pagamento")
            fmt = FuncionarioFolhaExcelService._define_formats(workbook)

            # Verifica se existem valores > 0 para decidir se exibe a coluna
            agregados = pagamentos.aggregate(
                sum_adiantamento=Sum('adiantamento'),
                sum_ferias_terco=Sum('ferias_terco'),
                sum_val_ferias=Sum('val_ferias'),
                sum_empreitada=Sum('empreitada'),
                sum_decimo=Sum('decimo_terceiro'),
                sum_vale=Sum('vale'),
                sum_extras=Sum('horas_extras_valor')
            )

            # NOVO: Verifica se há pelo menos um funcionário com algum desconto de benefício
            has_beneficios = False
            for item in pagamentos:
                if item.funcionario.beneficios.filter(valor_desconto__gt=0).exists():
                    has_beneficios = True
                    break

            def check_show(key):
                val = agregados.get(key)
                return val is not None and val > 0

            # Definição das colunas dinâmicas
            colunas_definicao = [
                ("Nome", "nome", 'data_text', 30, True),
                ("Cargo", "cargo", 'data_text', 20, True),
                ("Data Entrada", "dt_entrada", 'data_date', 12, True),
                ("Salário", "salario_real", 'data_money', 15, True),
                ("Adiantamento", "adiantamento", 'data_money', 15, check_show('sum_adiantamento')),
                ("Valor Férias", "val_ferias", 'data_money', 15, check_show('sum_val_ferias')),
                ("1/3 Férias", "ferias_terco", 'data_money', 15, check_show('sum_ferias_terco')),
                ("Empreitadas", "empreitada", 'data_money', 15, check_show('sum_empreitada')),
                ("13º Salário", "decimo", 'data_money', 15, check_show('sum_decimo')),
                ("Vale", "vale", 'data_money', 12, check_show('sum_vale')),
                ("Horas Extras", "extras", 'data_money', 15, check_show('sum_extras')),
                ("Benefícios (Desc.)", "beneficios", 'data_money', 18, has_beneficios),
                ("Observações", "obs", 'data_text', 30, True),
                ("TOTAL LÍQUIDO", "total_linha", 'total_row_money', 18, True),
            ]

            colunas_ativas = [c for c in colunas_definicao if c[4]]
            num_cols = len(colunas_ativas)

            row = 0
            ws.set_row(row, 25)
            if num_cols > 1:
                ws.merge_range(row, 0, row, num_cols - 1, "RELATÓRIO DE FOLHA DE PAGAMENTO / GASTOS COM PESSOAL", fmt['title'])
            else:
                ws.write(row, 0, "RELATÓRIO DE FOLHA DE PAGAMENTO", fmt['title'])
            row += 2 

            for col_idx, (titulo, _, _, largura, _) in enumerate(colunas_ativas):
                ws.set_column(col_idx, col_idx, largura) 
                ws.write(row, col_idx, titulo, fmt['header_table'])

            row += 1 
            total_geral = Decimal('0.00')

            for item in pagamentos:
                func = item.funcionario
                trabalhista = getattr(func, 'dados_trabalhistas', None)
                
                total_beneficios = sum(b.valor_desconto for b in func.beneficios.all() if b.valor_desconto)

                dados_linha = {
                    'nome': func.nome,
                    'cargo': trabalhista.funcao if trabalhista else "-",
                    'dt_entrada': (trabalhista.data_admissao_marcenaria or trabalhista.data_admissao_contabilidade) if trabalhista else None,
                    'salario_real': item.salario_real,
                    'adiantamento': item.adiantamento,
                    'val_ferias': item.val_ferias,
                    'ferias_terco': item.ferias_terco,
                    'empreitada': item.empreitada,
                    'decimo': item.decimo_terceiro,
                    'vale': item.vale,
                    'extras': item.horas_extras_valor,
                    'beneficios': total_beneficios,
                    'obs': item.observacoes or "",
                }

                total_linha = (
                    dados_linha['salario_real'] + dados_linha['val_ferias'] + 
                    dados_linha['ferias_terco'] + dados_linha['empreitada'] + 
                    dados_linha['decimo'] + dados_linha['extras']
                ) - dados_linha['adiantamento'] - dados_linha['vale'] - dados_linha['beneficios']
                
                dados_linha['total_linha'] = total_linha
                
                for col_idx, (_, chave, formato, _, _) in enumerate(colunas_ativas):
                    valor = dados_linha.get(chave)
                    if formato == 'data_date':
                        ws.write(row, col_idx, valor if valor else '-', fmt[formato])
                    else:
                        ws.write(row, col_idx, valor, fmt[formato])

                total_geral += total_linha
                row += 1

            row += 1
            if num_cols > 2:
                ws.merge_range(row, 0, row, num_cols - 2, "CUSTO LÍQUIDO TOTAL COM FUNCIONÁRIOS:", fmt['total_label'])
                ws.write(row, num_cols - 1, total_geral, fmt['total_final_money'])
            else:
                ws.write(row, 0, "TOTAL LÍQUIDO GERAL:", fmt['total_label'])
                ws.write(row, 1, total_geral, fmt['total_final_money'])
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatório de folha: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output

    # =========================================================================
    # RELATÓRIOS SEPARADOS (USADOS PELA ROTA DE CONTAS A PAGAR)
    # =========================================================================
    @staticmethod
    def gerar_relatorio_salario(pagamentos, workbook=None):
        """1. Planilha exclusiva de Salário (Simplificada com Nome, CPF, Pix, Liquido e Obs)."""
        output = io.BytesIO() if workbook is None else None
        workbook = xlsxwriter.Workbook(output, {'in_memory': True}) if workbook is None else workbook
        
        try:
            pagamentos = pagamentos.select_related('funcionario').prefetch_related('funcionario__beneficios')
            ws = workbook.add_worksheet("Salário a Pagar")
            fmt = FuncionarioFolhaExcelService._define_formats(workbook)

            colunas = [
                ("Nome do Funcionário", 35),
                ("CPF", 18),
                ("Chave PIX", 35),
                ("Salário Líquido", 20),
                ("Observações", 40),
            ]

            row = 0
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, len(colunas) - 1, "RELATÓRIO DE SALÁRIO LÍQUIDO MENSAL", fmt['title'])
            row += 2 

            for idx, (titulo, largura) in enumerate(colunas):
                ws.set_column(idx, idx, largura)
                ws.write(row, idx, titulo, fmt['header_table'])

            row += 1 
            total_geral = Decimal('0.00')

            for item in pagamentos:
                func = item.funcionario
                total_beneficios = sum(b.valor_desconto for b in func.beneficios.all() if b.valor_desconto)

                # === BUSCA DO CPF ===
                cpf = None
                if hasattr(func, 'cpf') and func.cpf:
                    cpf = func.cpf
                else:
                    try:
                        if hasattr(func, 'documentosfuncionario') and func.documentosfuncionario.cpf:
                            cpf = func.documentosfuncionario.cpf
                        elif hasattr(func, 'documentos') and func.documentos.cpf:
                            cpf = func.documentos.cpf
                    except Exception:
                        pass
                cpf = cpf if cpf else "-"

                # === BUSCA DO PIX ===
                pix = getattr(func, 'chave_pix', None)
                pix = pix if pix else "-"

                # Cálculo Total Líquido
                total_linha = (
                    item.salario_real + item.val_ferias + 
                    item.ferias_terco + item.empreitada + item.horas_extras_valor
                ) - item.adiantamento - item.vale - total_beneficios
                
                obs = item.observacoes if item.observacoes else ""
                
                ws.write(row, 0, func.nome, fmt.get('data_text'))
                ws.write(row, 1, cpf, fmt.get('data_text'))
                ws.write(row, 2, pix, fmt.get('data_text'))
                ws.write(row, 3, total_linha, fmt.get('total_row_money'))
                ws.write(row, 4, obs, fmt.get('data_text'))

                total_geral += total_linha
                row += 1

            row += 1
            ws.merge_range(row, 0, row, 2, "CUSTO LÍQUIDO TOTAL:", fmt['total_label'])
            ws.write(row, 3, total_geral, fmt['total_final_money'])

        finally:
            if output:
                workbook.close()
                output.seek(0)
                return output

    @staticmethod
    def gerar_relatorio_adiantamento(pagamentos, workbook=None):
        """2. Planilha exclusiva de Adiantamentos (Com PIX, CPF e Salário)."""
        output = io.BytesIO() if workbook is None else None
        workbook = xlsxwriter.Workbook(output, {'in_memory': True}) if workbook is None else workbook
        
        try:
            pagamentos = pagamentos.select_related('funcionario')
            ws = workbook.add_worksheet("Adiantamentos")
            fmt = FuncionarioFolhaExcelService._define_formats(workbook)

            colunas = [
                ("Nome do Funcionário", 40),
                ("CPF", 18),
                ("Chave PIX", 35),
                ("Salário", 20),
                ("Valor do Adiantamento", 25),
            ]

            row = 0
            ws.merge_range(row, 0, row, len(colunas) - 1, "RELATÓRIO DE ADIANTAMENTO SALARIAL", fmt.get('title'))
            row += 2

            for idx, (titulo, largura) in enumerate(colunas):
                ws.set_column(idx, idx, largura)
                ws.write(row, idx, titulo, fmt.get('header_table'))
            
            row += 1
            total_geral = Decimal('0.00')

            for item in pagamentos:
                func = item.funcionario
                
                # === BUSCA DO CPF ===
                cpf = None
                if hasattr(func, 'cpf') and func.cpf:
                    cpf = func.cpf
                else:
                    try:
                        if hasattr(func, 'documentosfuncionario') and func.documentosfuncionario.cpf:
                            cpf = func.documentosfuncionario.cpf
                        elif hasattr(func, 'documentos') and func.documentos.cpf:
                            cpf = func.documentos.cpf
                    except Exception:
                        pass
                cpf = cpf if cpf else "-"

                # === BUSCA DO PIX ===
                pix = getattr(func, 'chave_pix', None)
                pix = pix if pix else "-"
                
                ws.write(row, 0, func.nome, fmt.get('data_text'))
                ws.write(row, 1, cpf, fmt.get('data_text'))
                ws.write(row, 2, pix, fmt.get('data_text'))
                ws.write(row, 3, item.salario_real, fmt.get('data_money'))
                ws.write(row, 4, item.adiantamento, fmt.get('data_money'))
                
                total_geral += item.adiantamento
                row += 1

            row += 1
            ws.merge_range(row, 0, row, 3, "TOTAL ADIANTADO:", fmt.get('total_label'))
            ws.write(row, 4, total_geral, fmt.get('total_final_money'))

        finally:
            if output:
                workbook.close()
                output.seek(0)
                return output

    @staticmethod
    def gerar_relatorio_decimo(pagamentos, workbook=None):
        """3. Planilha de 13º em parcela única (Simplificada)."""
        output = io.BytesIO() if workbook is None else None
        workbook = xlsxwriter.Workbook(output, {'in_memory': True}) if workbook is None else workbook
        
        try:
            pagamentos = pagamentos.select_related('funcionario')
            ws = workbook.add_worksheet("13º Salário")
            fmt = FuncionarioFolhaExcelService._define_formats(workbook)

            colunas = [
                ("Nome do Funcionário", 40),
                ("CPF", 18),
                ("Chave PIX", 35),
                ("13º Salário", 20),
                ("Observações", 40),
            ]

            row = 0
            ws.merge_range(row, 0, row, len(colunas) - 1, "RELATÓRIO DE 13º SALÁRIO", fmt.get('title'))
            row += 2

            for idx, (titulo, largura) in enumerate(colunas):
                ws.set_column(idx, idx, largura)
                ws.write(row, idx, titulo, fmt.get('header_table'))
            
            row += 1
            total_geral = Decimal('0.00')

            for item in pagamentos:
                func = item.funcionario
                
                # === BUSCA DO CPF ===
                cpf = None
                if hasattr(func, 'cpf') and func.cpf:
                    cpf = func.cpf
                else:
                    try:
                        if hasattr(func, 'documentosfuncionario') and func.documentosfuncionario.cpf:
                            cpf = func.documentosfuncionario.cpf
                        elif hasattr(func, 'documentos') and func.documentos.cpf:
                            cpf = func.documentos.cpf
                    except Exception:
                        pass
                cpf = cpf if cpf else "-"

                # === BUSCA DO PIX ===
                pix = getattr(func, 'chave_pix', None)
                pix = pix if pix else "-"
                
                valor_total = item.decimo_terceiro
                obs = item.observacoes if item.observacoes else ""
                
                ws.write(row, 0, func.nome, fmt.get('data_text'))
                ws.write(row, 1, cpf, fmt.get('data_text'))
                ws.write(row, 2, pix, fmt.get('data_text'))
                ws.write(row, 3, valor_total, fmt.get('data_money'))
                ws.write(row, 4, obs, fmt.get('data_text'))
                
                total_geral += valor_total
                row += 1

            row += 1
            ws.merge_range(row, 0, row, 2, "TOTAL DE 13º SALÁRIO:", fmt.get('total_label'))
            ws.write(row, 3, total_geral, fmt.get('total_final_money'))

        finally:
            if output:
                workbook.close()
                output.seek(0)
                return output