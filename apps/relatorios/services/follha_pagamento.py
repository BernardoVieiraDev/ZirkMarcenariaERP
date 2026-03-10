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