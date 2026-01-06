import io
import xlsxwriter
from decimal import Decimal
from datetime import date

# Ajuste os imports conforme a estrutura real do seu projeto
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
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
            'fg_color': cls.COR_PRIMARIA_AZUL, 'font_color': '#FFFFFF', 'font_name': 'Calibri'
        })

        fmt_subtitle = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
            'font_color': cls.COR_PRIMARIA_AZUL, 'font_name': 'Calibri'
        })

        fmt_header = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'left', 'valign': 'vcenter',
            'fg_color': cls.COR_FUNDO_SECAO, 'border': 1, 'font_name': 'Calibri'
        })

        fmt_label = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'right', 'valign': 'vcenter',
            'fg_color': cls.COR_FUNDO_LABEL, 'border': 1, 'font_name': 'Calibri'
        })

        fmt_data = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1,
            'font_name': 'Calibri', 'font_size': 10,
        })

        fmt_data_text = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1,
            'font_name': 'Calibri', 'font_size': 10, 'num_format': '@'
        })

        fmt_money = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1,
            'font_name': 'Calibri', 'font_size': 10, 'num_format': 'R$ #,##0.00'
        })

        fmt_simple = workbook.add_format({
            'font_name': 'Calibri', 'font_size': 10,
            'align': 'left', 'valign': 'vcenter'
        })
        
        # Novo formato específico para os itens do checklist (sem fundo, com borda)
        fmt_checklist_item = workbook.add_format({
            'font_name': 'Calibri', 'font_size': 10,
            'align': 'left', 'valign': 'vcenter',
            'border': 1
        })

        return {
            'title': fmt_title,
            'subtitle': fmt_subtitle,
            'header': fmt_header,
            'label': fmt_label,
            'data': fmt_data,
            'data_text': fmt_data_text,
            'money': fmt_money,
            'simple': fmt_simple,
            'checklist_item': fmt_checklist_item
        }

    @staticmethod
    def gerar_modelo(funcionario=None):
        """
        Gera o arquivo Excel em memória e retorna o buffer.
        """
        output = io.BytesIO()
        try:
            wb = xlsxwriter.Workbook(output, {'in_memory': True})
            ws = wb.add_worksheet("CADASTRO FUNCIONÁRIO")
            fmt = CadastroFuncionarioExcelService._define_formats(wb)

            # --- Configuração de Colunas ---
            ws.set_column('A:A', 28.5)
            ws.set_column('B:B', 35)
            ws.set_column('C:C', 22)
            ws.set_column('D:D', 35)
            ws.set_column('E:E', 10)
            ws.hide_gridlines(2) 

            # --- Extração Segura de Dados ---
            f = funcionario
            end = getattr(f, "endereco", None) if f else None
            docs = getattr(f, "documentos", None) if f else None
            trab = getattr(f, "dados_trabalhistas", None) if f else None

            row = 0

            # --- CABEÇALHO ---
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 3, "CADASTRO PARA ADMISSÃO DE FUNCIONÁRIO", fmt['title'])
            row += 1
            ws.merge_range(row, 0, row, 3, "Empresa Contratante: ZIRK MOVEIS E DECORAÇÕES LTDA", fmt['subtitle'])
            row += 2

            # --- I. DADOS PESSOAIS ---
            ws.merge_range(row, 0, row, 3, "I. DADOS DE IDENTIFICAÇÃO PESSOAL", fmt['header']); row += 1
            
            ws.write(row, 0, "Nome do Funcionário:", fmt['label'])
            ws.write(row, 1, f.nome if f and getattr(f, "nome", None) else '', fmt['data_text'])
            ws.write(row, 2, "Data de Nascimento:", fmt['label'])
            data_nasc = f.data_nascimento.strftime("%d/%m/%Y") if f and getattr(f, "data_nascimento", None) else ''
            ws.write(row, 3, data_nasc, fmt['data'])
            row += 1

            ws.write(row, 0, "Sexo:", fmt['label'])
            ws.write(row, 1, f.get_sexo_display() if f and getattr(f, "sexo", None) else '', fmt['data'])
            ws.write(row, 2, "Natural de:", fmt['label'])
            ws.write(row, 3, f.natural_de if f and getattr(f, "natural_de", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "Grau de Instrução:", fmt['label'])
            ws.write(row, 1, f.get_grau_instrucao_display() if f and getattr(f, "grau_instrucao", None) else '', fmt['data'])
            ws.write(row, 2, "Estado Civil:", fmt['label'])
            ws.write(row, 3, f.get_estado_civil_display() if f and getattr(f, "estado_civil", None) else '', fmt['data'])
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

            # --- II. ENDEREÇO ---
            ws.merge_range(row, 0, row, 3, "II. ENDEREÇO COMPLETO", fmt['header']); row += 1
            
            ws.write(row, 0, "Endereço:", fmt['label'])
            ws.write(row, 1, end.endereco if end and getattr(end, "endereco", None) else '', fmt['data_text'])
            ws.write(row, 2, "Nº:", fmt['label'])
            ws.write(row, 3, end.numero if end and getattr(end, "numero", None) else '', fmt['data'])
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

            # --- III. DOCUMENTOS ---
            ws.merge_range(row, 0, row, 3, "III. DOCUMENTOS E REGISTROS", fmt['header']); row += 1
            
            ws.write(row, 0, "N.º PIS/PASEP:", fmt['label'])
            ws.write(row, 1, docs.pis_pasep if docs and getattr(docs, "pis_pasep", None) else '', fmt['data_text'])
            
            texto_selecao = "( ) PIS   ( ) PASEP"
            if docs:
                tipo = getattr(docs, "tipo_pis_pasep", None)
                if tipo == 'PIS': texto_selecao = "(X) PIS   ( ) PASEP"
                elif tipo == 'PASEP': texto_selecao = "( ) PIS   (X) PASEP"
            ws.merge_range(row, 2, row, 3, texto_selecao, fmt['simple'])
            row += 1

            ws.write(row, 0, "CTPS Nº:", fmt['label'])
            ws.write(row, 1, docs.ctps_numero if docs and getattr(docs, "ctps_numero", None) else '', fmt['data_text'])
            ws.write(row, 2, "Série / UF:", fmt['label'])
            serie = docs.ctps_serie or '' if docs else ''
            uf_ctps = docs.ctps_uf or '' if docs else ''
            ws.write(row, 3, f"{serie} / {uf_ctps}".strip(), fmt['data_text'])
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

            # --- IV. DADOS TRABALHISTAS ---
            ws.merge_range(row, 0, row, 3, "IV. DADOS TRABALHISTAS E CONTRATUAIS", fmt['header']); row += 1
            
            ws.write(row, 0, "Data de Admissão:", fmt['label'])
            data_adm = ''
            if trab and getattr(trab, "data_admissao_contabilidade", None):
                data_adm = trab.data_admissao_contabilidade.strftime("%d/%m/%Y")
            ws.write(row, 1, data_adm, fmt['data'])
            
            ws.write(row, 2, "Função:", fmt['label'])
            ws.write(row, 3, trab.funcao if trab and getattr(trab, "funcao", None) else '', fmt['data'])
            row += 1

            ws.write(row, 0, "CBO:", fmt['label'])
            ws.write(row, 1, trab.cbo if trab and getattr(trab, "cbo", None) else '', fmt['data_text'])
            
            ws.write(row, 2, "Salário R$:", fmt['label'])
            salario_val = trab.salario if trab and getattr(trab, "salario", None) else 0
            ws.write(row, 3, salario_val, fmt['money'])
            row += 1

            ws.write(row, 0, "Insalubridade %:", fmt['label'])
            insal = trab.insalubridade if trab and getattr(trab, "insalubridade", None) else ''
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

            ws.merge_range(row, 0, row, 3, "Horário de trabalho:", fmt['header']); row += 1
            ws.write(row, 0, "Horário:", fmt['label'])
            ws.merge_range(row, 1, row, 3, trab.horario_trabalho if trab and getattr(trab, "horario_trabalho", None) else '', fmt['data'])
            row += 3

            # --- V. CHECKLIST DE DOCUMENTOS (NOVA SEÇÃO) ---
            ws.merge_range(row, 0, row, 3, "V. RELAÇÃO DE DOCUMENTOS A ANEXAR", fmt['header'])
            row += 1

            checklist_items = [
                "Carteira de Trabalho",
                "Foto 3x4",
                "Atestado Médico",
                "Certidão Forum de Antecedentes",
                "Cópia da Certidão de Nascimento dos filhos até 14 anos",
                "Cópia da Certidão de Nascimento e/ou Casamento do funcionário",
                "Cópia da Carteira de Vacinação dos filhos",
                "Declaração escola do filhos",
                "Cópia da CPF dos filhos",
                "Cópia da Cédula de Identidade",
                "Cópia do CPF",
                "Cópia do Titulo de Eleitor",
                "Cópia do Certificado Reservista"
            ]

            for item in checklist_items:
                texto_checklist = f"(   ) - {item}"
                # Mescla de A até D (0 a 3) para o texto caber bem
                ws.merge_range(row, 0, row, 3, texto_checklist, fmt['checklist_item'])
                row += 1

            wb.close()
            output.seek(0)
            return output

        except Exception as e:
            print(f"❌ Erro ao gerar planilha: {e}")
            raise e