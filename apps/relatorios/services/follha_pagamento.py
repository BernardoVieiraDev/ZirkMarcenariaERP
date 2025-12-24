import io
import xlsxwriter
from decimal import Decimal
from datetime import date

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
                'font_name': 'Calibri', 'font_size': 10, 'bg_color': '#FFFFCC', # Amarelo claro para destaque
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
    def gerar_relatorio_folha(pagamentos, workbook=None):
        """
        Recebe um QuerySet de FolhaPagamento e retorna um buffer Excel (se workbook=None).
        """
        # Controle para saber se devemos fechar o arquivo ao final (Modo Individual)
        output = None
        should_close = False

        if workbook is None:
            # 1. Cria o buffer em memória se não receber um workbook existente
            output = io.BytesIO()
            # 2. Inicializa o Workbook
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("Folha de Pagamento")
            fmt = FuncionarioFolhaExcelService._define_formats(workbook)

            # Cabeçalhos
            headers = [
                "Nome", 
                "Cargo",
                "Data Entrada", 
                "Salário Carteira", 
                "Salário Real", 
                "Adiantamento", 
                "1/3 Férias", 
                "Empreitadas", 
                "13º Salário", 
                "Vale", 
                "Horas Extras", 
                "Observações",
                "TOTAL"
            ]

            # Configurar largura das colunas
            ws.set_column('A:A', 30) # Nome#type: ignore
            ws.set_column('B:B', 20) # Cargo#type: ignore
            ws.set_column('C:C', 12) # Data Entrada#type: ignore
            ws.set_column('D:D', 15) # Salario CTPS#type: ignore
            ws.set_column('E:E', 15) # Salario Real#type: ignore
            ws.set_column('F:F', 15) # Adiantamento#type: ignore
            ws.set_column('G:G', 15) # 1/3 Ferias#type: ignore
            ws.set_column('H:H', 15) # Empreitadas#type: ignore
            ws.set_column('I:I', 15) # 13o#type: ignore
            ws.set_column('J:J', 12) # Vale#type: ignore
            ws.set_column('K:K', 15) # Extras#type: ignore
            ws.set_column('L:L', 30) # Obs#type: ignore
            ws.set_column('M:M', 18) # Total#type: ignore

            row = 0

            # --- TÍTULO NO TOPO ---
            ws.set_row(row, 25)
            ws.merge_range(row, 0, row, 12, "RELATÓRIO DE FOLHA DE PAGAMENTO / GASTOS COM PESSOAL", fmt['title'])
            row += 2 

            # Escrever Cabeçalho da Tabela
            for col_num, header in enumerate(headers):
                ws.write(row, col_num, header, fmt['header_table'])

            row += 1 
            
            # Acumuladores para o Total Geral
            total_geral = Decimal('0.00')

            # Iterar sobre os pagamentos (FolhaPagamento)
            for item in pagamentos:
                # Dados do Funcionario (via relação)
                func = item.funcionario
                
                # Tenta pegar dados trabalhistas de forma segura
                trabalhista = getattr(func, 'dados_trabalhistas', None)
                
                nome = func.nome
                cargo = trabalhista.funcao if trabalhista else "-"
                
                # Data de entrada: Prioridade Marcenaria, se não tiver, Contabilidade
                dt_entrada = None
                if trabalhista:
                    dt_entrada = trabalhista.data_admissao_marcenaria or trabalhista.data_admissao_contabilidade

                salario_ctps = trabalhista.salario if trabalhista else Decimal('0.00')

                # Dados da Folha (Model Novo)
                salario_real = item.salario_real
                adiantamento = item.adiantamento
                ferias_1_3 = item.ferias_terco
                empreitada = item.empreitada
                decimo = item.decimo_terceiro
                vale = item.vale
                extras = item.horas_extras_valor
                obs = item.observacoes or ""

                # Cálculo do Total por Funcionário (Linha)
                total_linha = (
                    salario_real + adiantamento + ferias_1_3 + 
                    empreitada + decimo + vale + extras
                )

                # Escrever na planilha
                ws.write(row, 0, nome, fmt['data_text'])
                ws.write(row, 1, cargo, fmt['data_text'])
                
                if dt_entrada:
                    ws.write(row, 2, dt_entrada, fmt['data_date'])
                else:
                    ws.write(row, 2, '-', fmt['data_date']) # Corrigido para data_date ou data_center

                ws.write(row, 3, salario_ctps, fmt['data_money'])
                ws.write(row, 4, salario_real, fmt['data_money'])
                ws.write(row, 5, adiantamento, fmt['data_money'])
                ws.write(row, 6, ferias_1_3, fmt['data_money'])
                ws.write(row, 7, empreitada, fmt['data_money'])
                ws.write(row, 8, decimo, fmt['data_money'])
                ws.write(row, 9, vale, fmt['data_money'])
                ws.write(row, 10, extras, fmt['data_money'])
                ws.write(row, 11, obs, fmt['data_text'])
                
                # Total da Linha com destaque
                ws.write(row, 12, total_linha, fmt['total_row_money'])

                total_geral += total_linha
                row += 1

            # --- LINHA DE TOTAL GERAL ---
            row += 1
            ws.merge_range(row, 0, row, 11, "CUSTO TOTAL COM FUNCIONÁRIOS:", fmt['total_label'])
            ws.write(row, 12, total_geral, fmt['total_final_money'])
            
            print(f"✅ Relatório de Folha gerado em memória.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de folha: {e}")
            raise e
        finally:
            # Só fecha e retorna se foi criado dentro deste método (Modo Individual)
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output