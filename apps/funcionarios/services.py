import os
import xlsxwriter
from decimal import Decimal
from datetime import date

from .models import Funcionario, EnderecoFuncionario, DocumentosFuncionario, DadosTrabalhistas


class CadastroFuncionarioExcelService:
    COR_PRIMARIA_AZUL = '#004F9F'
    COR_FUNDO_SECAO = '#D9E1F2'
    COR_FUNDO_LABEL = '#F0F0F0'
    COR_BORDA = '#A9A9A9'

    @classmethod
    def _define_formats(cls, workbook: xlsxwriter.Workbook):
        """Define e retorna um dicionário de formatos reutilizáveis."""
        fmt_title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': cls.COR_PRIMARIA_AZUL,
            'font_color': '#FFFFFF',
            'font_name': 'Calibri'
        })

        fmt_subtitle = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': cls.COR_PRIMARIA_AZUL,
            'font_name': 'Calibri'
        })

        fmt_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter',
            'fg_color': cls.COR_FUNDO_SECAO,
            'border': 1,
            'font_name': 'Calibri'
        })

        fmt_label = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'fg_color': cls.COR_FUNDO_LABEL,
            'border': 1,
            'font_name': 'Calibri'
        })

        # formato base para células de dados
        fmt_data = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 10,
        })

        # formato texto (mantém zeros à esquerda)
        fmt_data_text = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 10,
            'num_format': '@'
        })

        # formato monetário
        fmt_money = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 10,
            'num_format': 'R$ #,##0.00'
        })

        # formato simples (sem borda) — **definido explicitamente**
        fmt_simple = workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 10,
            'align': 'left',
            'valign': 'vcenter'
        })

        return {
            'title': fmt_title,
            'subtitle': fmt_subtitle,
            'header': fmt_header,
            'label': fmt_label,
            'data': fmt_data,
            'data_text': fmt_data_text,
            'money': fmt_money,
            'simple': fmt_simple
        }

    @staticmethod
    def gerar_modelo(funcionario=None, caminho_arquivo="CADASTRO_ADMISSAO_MODELO.xlsx"):
        """
        Gera o arquivo Excel. Se 'funcionario' for passado, preenche com os dados disponíveis.
        """
        try:
            wb = xlsxwriter.Workbook(caminho_arquivo)
            ws = wb.add_worksheet("CADASTRO FUNCIONÁRIO")
            fmt = CadastroFuncionarioExcelService._define_formats(wb)

            # colunas
            ws.set_column('A:A', 28.5) #type: ignore
            ws.set_column('B:B', 35) #type: ignore
            ws.set_column('C:C', 22) #type: ignore
            ws.set_column('D:D', 35) #type: ignore
            ws.set_column('E:E', 10) #type: ignore
            ws.hide_gridlines(2)

            # extrai dados de forma segura
            f = funcionario
            end = getattr(f, "endereco", None) if f else None
            docs = getattr(f, "documentos", None) if f else None
            trab = getattr(f, "dados_trabalhistas", None) if f else None

            # logs de depuração (remova em produção)
            print(">>> Gerando Excel para funcionário:", getattr(f, "pk", None))
            print(">>> Endereço:", end)
            print(">>> Documentos:", docs)
            print(">>> Dados trabalhistas:", trab)

            row = 0

            # cabeçalho
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 3, "CADASTRO PARA ADMISSÃO DE FUNCIONÁRIO", fmt['title'])
            row += 1
            ws.merge_range(row, 0, row, 3, "Empresa Contratante: ZIRK MOVEIS E DECORAÇÕES LTDA", fmt['subtitle'])
            row += 2

            # I. Dados pessoais
            ws.merge_range(row, 0, row, 3, "I. DADOS DE IDENTIFICAÇÃO PESSOAL", fmt['header']); row += 1
            ws.write(row, 0, "Nome do Funcionário:", fmt['label'])
            nome_val = f.nome if f and getattr(f, "nome", None) else ''
            ws.write(row, 1, nome_val, fmt['data_text'])
            ws.write(row, 2, "Data de Nascimento:", fmt['label'])
            data_nasc = ''
            if f and getattr(f, "data_nascimento", None):
                try:
                    data_nasc = f.data_nascimento.strftime("%d/%m/%Y")
                except Exception:
                    data_nasc = str(f.data_nascimento)
            ws.write(row, 3, data_nasc, fmt['data'])
            row += 1

            ws.write(row, 0, "Sexo:", fmt['label'])
            sexo_display = f.get_sexo_display() if f and getattr(f, "sexo", None) else ''
            ws.write(row, 1, sexo_display, fmt['data'])
            ws.write(row, 2, "Natural de:", fmt['label'])
            ws.write(row, 3, f.natural_de if f and getattr(f, "natural_de", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "Grau de Instrução:", fmt['label'])
            grau_disp = f.get_grau_instrucao_display() if f and getattr(f, "grau_instrucao", None) else ''
            ws.write(row, 1, grau_disp, fmt['data'])
            ws.write(row, 2, "Estado Civil:", fmt['label'])
            estado_disp = f.get_estado_civil_display() if f and getattr(f, "estado_civil", None) else ''
            ws.write(row, 3, estado_disp, fmt['data'])
            row += 1

            ws.write(row, 0, "Nome do Cônjuge:", fmt['label'])
            ws.merge_range(row, 1, row, 3, f.conjuge if f and getattr(f, "conjuge", None) else '', fmt['data_text'])
            row += 1
            ws.write(row, 0, "Nome do Pai:", fmt['label'])
            ws.write(row, 1, f.nome_pai if f and getattr(f, "nome_pai", None) else '', fmt['data_text'])
            ws.write(row, 2, "Nome da Mãe:", fmt['label'])
            ws.write(row, 3, f.nome_mae if f and getattr(f, "nome_mae", None) else '', fmt['data_text'])
            row += 1

            ws.write(row, 0, "Número de filhos menores:", fmt['label'])
            ws.write(row, 1, f.numero_filhos if f and getattr(f, "numero_filhos", None) is not None else '', fmt['data'])
            row += 2

            # II. Endereço
            ws.merge_range(row, 0, row, 3, "II. ENDEREÇO COMPLETO", fmt['header']); row += 1
            ws.write(row, 0, "Endereço:", fmt['label'])
            endereco_val = end.endereco if end and getattr(end, "endereco", None) else ''
            ws.write(row, 1, endereco_val, fmt['data_text'])  # Coluna B
            ws.write(row, 2, 'Nº:', fmt['data_text'])            # Coluna C (deixa vazia ou use como quis            ws.write(row, 3, "Nº:", fmt['label'])
            ws.write(row, 4, end.numero if end and getattr(end, "numero", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "Bairro:", fmt['label'])
            ws.write(row, 1, end.bairro if end and getattr(end, "bairro", None) else '', fmt['data'])
            ws.write(row, 2, "Cidade:", fmt['label'])
            ws.write(row, 3, end.cidade if end and getattr(end, "cidade", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "UF:", fmt['label'])
            ws.write(row, 1, end.uf if end and getattr(end, "uf", None) else '', fmt['data'])
            ws.write(row, 2, "CEP:", fmt['label'])
            ws.write(row, 3, end.cep if end and getattr(end, "cep", None) else '', fmt['data_text'])
            row += 2

            # III. Documentos
            ws.merge_range(row, 0, row, 3, "III. DOCUMENTOS E REGISTROS", fmt['header']); row += 1
            ws.write(row, 0, "N.º PIS/PASEP:", fmt['label'])
            ws.write(row, 1, docs.pis_pasep if docs and getattr(docs, "pis_pasep", None) else '', fmt['data_text'])
            ws.merge_range(row, 2, row, 3, "( ) PIS   ( ) PASEP", fmt['simple'])
            row += 1

            ws.write(row, 0, "CTPS Nº:", fmt['label'])
            ws.write(row, 1, docs.ctps_numero if docs and getattr(docs, "ctps_numero", None) else '', fmt['data_text'])
            ws.write(row, 2, "Série / UF:", fmt['label'])
            serie_uf = ""
            if docs:
                serie = docs.ctps_serie or ''
                uf_ctps = docs.ctps_uf or ''
                serie_uf = f"{serie} / {uf_ctps}".strip()
            ws.write(row, 3, serie_uf, fmt['data_text'])
            row += 1

            ws.write(row, 0, "RG:", fmt['label'])
            ws.write(row, 1, docs.rg if docs and getattr(docs, "rg", None) else '', fmt['data_text'])
            ws.write(row, 2, "Órgão expedidor:", fmt['label'])
            ws.write(row, 3, docs.rg_orgao_expedidor if docs and getattr(docs, "rg_orgao_expedidor", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "CPF:", fmt['label'])
            ws.write(row, 1, docs.cpf if docs and getattr(docs, "cpf", None) else '', fmt['data_text'])
            ws.write(row, 2, "Título de Eleitor:", fmt['label'])
            ws.write(row, 3, docs.titulo_eleitor if docs and getattr(docs, "titulo_eleitor", None) else '', fmt['data_text'])
            row += 1

            ws.write(row, 0, "Certificado de reservista:", fmt['label'])
            ws.write(row, 1, docs.certificado_reservista if docs and getattr(docs, "certificado_reservista", None) else '', fmt['data'])
            row += 2

            # IV. Dados trabalhistas
            ws.merge_range(row, 0, row, 3, "IV. DADOS TRABALHISTAS E CONTRATUAIS", fmt['header']); row += 1
            ws.write(row, 0, "Data de Admissão (Contabilidade):", fmt['label'])
            data_adm = ''
            if trab and getattr(trab, "data_admissao_contabilidade", None):
                try:
                    data_adm = trab.data_admissao_contabilidade.strftime("%d/%m/%Y")
                except Exception:
                    data_adm = str(trab.data_admissao_contabilidade)
            ws.write(row, 1, data_adm, fmt['data'])
            ws.write(row, 2, "Função:", fmt['label'])
            ws.write(row, 3, trab.funcao if trab and getattr(trab, "funcao", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "CBO:", fmt['label'])
            ws.write(row, 1, trab.cbo if trab and getattr(trab, "cbo", None) else '', fmt['data_text'])
            ws.write(row, 2, "Salário R$:", fmt['label'])
            salario_val = ''
            if trab and getattr(trab, "salario", None) is not None:
                try:
                    salario_val = float(trab.salario)
                except Exception:
                    salario_val = trab.salario
            ws.write(row, 3, salario_val, fmt['money'])
            row += 1

            ws.write(row, 0, "Insalubridade %:", fmt['label'])
            insal = ''
            if trab and getattr(trab, "insalubridade", None) is not None:
                try:
                    insal = float(trab.insalubridade)
                except Exception:
                    insal = trab.insalubridade
            ws.write(row, 1, insal, fmt['data'])
            row += 1

            exp_str = ''
            if trab:
                dias = getattr(trab, "contrato_experiencia_dias", None) or ''
                pror = getattr(trab, "prorrogação_dias", None) or getattr(trab, "prorrogacao_dias", None) or ''
                exp_str = f"{dias} dias / Prorrogação: {pror} dias"
            ws.write(row, 0, "Contrato de experiência:", fmt['label'])
            ws.merge_range(row, 1, row, 3, exp_str, fmt['data'])
            row += 2

            ws.merge_range(row, 0, row, 3, "Horário de trabalho:", fmt['header'])
            row += 1
            ws.write(row, 0, "Segunda a Sexta:", fmt['label'])
            ws.write(row, 1, trab.horario_trabalho if trab and getattr(trab, "horario_trabalho", None) else '', fmt['data'])
            row += 1

            print(f"✅ Planilha gerada com sucesso: {caminho_arquivo}")

        except Exception as e:
            # mostra o erro no terminal/console do servidor
            print(f"❌ Erro ao gerar planilha: {e}")
        finally:
            # garante fechamento do workbook
            if 'wb' in locals():
                wb.close()
