import io
import xlsxwriter
from decimal import Decimal
from datetime import date
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

            # --- ANÁLISE PRÉVIA PARA COLUNAS DINÂMICAS ---
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

            # Função auxiliar para checar se deve mostrar (True se valor > 0)
            def check_show(key):
                val = agregados.get(key)
                return val is not None and val > 0

            # Definição das colunas: (Título, Chave_Dados, Formato, Largura, Mostrar?)
            colunas_definicao = [
                # Colunas Fixas
                ("Nome", "nome", 'data_text', 30, True),
                ("Cargo", "cargo", 'data_text', 20, True),
                ("Data Entrada", "dt_entrada", 'data_date', 12, True),
                
                # Alteração aqui: Removido "Salário Carteira" e renomeado "Salário Real" para "Salário"
                ("Salário", "salario_real", 'data_money', 15, True),
                
                # Colunas Dinâmicas
                ("Adiantamento", "adiantamento", 'data_money', 15, check_show('sum_adiantamento')),
                ("Valor Férias", "val_ferias", 'data_money', 15, check_show('sum_val_ferias')),
                ("1/3 Férias", "ferias_terco", 'data_money', 15, check_show('sum_ferias_terco')),
                ("Empreitadas", "empreitada", 'data_money', 15, check_show('sum_empreitada')),
                ("13º Salário", "decimo", 'data_money', 15, check_show('sum_decimo')),
                ("Vale", "vale", 'data_money', 12, check_show('sum_vale')),
                ("Horas Extras", "extras", 'data_money', 15, check_show('sum_extras')),
                
                # Colunas Finais Fixas
                ("Observações", "obs", 'data_text', 30, True),
                ("TOTAL", "total_linha", 'total_row_money', 18, True),
            ]

            # Filtra apenas as colunas que devem ser exibidas
            colunas_ativas = [c for c in colunas_definicao if c[4]]
            num_cols = len(colunas_ativas)

            row = 0

            # --- TÍTULO NO TOPO (Mesclado dinamicamente) ---
            ws.set_row(row, 25)
            if num_cols > 1:
                ws.merge_range(row, 0, row, num_cols - 1, "RELATÓRIO DE FOLHA DE PAGAMENTO / GASTOS COM PESSOAL", fmt['title'])
            else:
                ws.write(row, 0, "RELATÓRIO DE FOLHA DE PAGAMENTO", fmt['title'])
            row += 2 

            # --- CABEÇALHO DA TABELA ---
            for col_idx, (titulo, _, _, largura, _) in enumerate(colunas_ativas):
                # Ajusta largura da coluna
                tipo_coluna = chr(65 + col_idx) # A, B, C...
                ws.set_column(f'{tipo_coluna}:{tipo_coluna}', largura)
                ws.write(row, col_idx, titulo, fmt['header_table'])

            row += 1 
            
            total_geral = Decimal('0.00')

            # --- ITERAÇÃO DOS DADOS ---
            for item in pagamentos:
                func = item.funcionario
                trabalhista = getattr(func, 'dados_trabalhistas', None)
                
                # Prepara dicionário de dados da linha
                dados_linha = {
                    'nome': func.nome,
                    'cargo': trabalhista.funcao if trabalhista else "-",
                    'dt_entrada': (trabalhista.data_admissao_marcenaria or trabalhista.data_admissao_contabilidade) if trabalhista else None,
                    # 'salario_ctps': removido pois não é mais usado
                    'salario_real': item.salario_real,
                    'adiantamento': item.adiantamento,
                    'val_ferias': item.val_ferias,
                    'ferias_terco': item.ferias_terco,
                    'empreitada': item.empreitada,
                    'decimo': item.decimo_terceiro,
                    'vale': item.vale,
                    'extras': item.horas_extras_valor,
                    'obs': item.observacoes or "",
                }

                # Cálculo Total
                total_linha = (
                    dados_linha['salario_real'] + dados_linha['adiantamento'] + 
                    dados_linha['val_ferias'] + dados_linha['ferias_terco'] + 
                    dados_linha['empreitada'] + dados_linha['decimo'] + 
                    dados_linha['vale'] + dados_linha['extras']
                )
                dados_linha['total_linha'] = total_linha
                
                # Escreve as colunas ativas
                for col_idx, (_, chave, formato, _, _) in enumerate(colunas_ativas):
                    valor = dados_linha.get(chave)
                    
                    if formato == 'data_date':
                        ws.write(row, col_idx, valor if valor else '-', fmt[formato])
                    else:
                        ws.write(row, col_idx, valor, fmt[formato])

                total_geral += total_linha
                row += 1

            # --- LINHA DE TOTAL GERAL ---
            row += 1
            if num_cols > 2:
                ws.merge_range(row, 0, row, num_cols - 2, "CUSTO TOTAL COM FUNCIONÁRIOS:", fmt['total_label'])
                ws.write(row, num_cols - 1, total_geral, fmt['total_final_money'])
            else:
                ws.write(row, 0, "TOTAL GERAL:", fmt['total_label'])
                ws.write(row, 1, total_geral, fmt['total_final_money'])
            
            print(f"✅ Relatório de Folha gerado com {num_cols} colunas dinâmicas.")

        except Exception as e:
            print(f"❌ Erro ao gerar relatório de folha: {e}")
            raise e
        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output
                
    @staticmethod
    def gerar_relatorio_decimo(pagamentos, workbook=None):
        import xlsxwriter
        import io
        from decimal import Decimal

        output = None
        should_close = False

        if workbook is None:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            should_close = True
        
        try:
            ws = workbook.add_worksheet("13º Salário")
            # Tenta pegar formatos existentes ou define novos se não existirem
            try:
                fmt = FuncionarioFolhaExcelService._define_formats(workbook)
            except:
                # Fallback simples caso _define_formats não seja estático ou acessível
                fmt = {
                    'title': workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}),
                    'header_table': workbook.add_format({'bold': True, 'bg_color': '#CCCCCC', 'border': 1}),
                    'data_text': workbook.add_format({'border': 1}),
                    'data_money': workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1}),
                    'total_label': workbook.add_format({'bold': True, 'align': 'right'}),
                    'total_final_money': workbook.add_format({'bold': True, 'num_format': 'R$ #,##0.00', 'bg_color': '#FFFF00', 'border': 1}),
                }

            colunas = [
                ("Nome", 40),
                ("Cargo", 25),
                ("Salário Base", 18),
                ("13º a Receber", 18),
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
                trabalhista = getattr(func, 'dados_trabalhistas', None)
                cargo = trabalhista.funcao if trabalhista else "-"
                
                ws.write(row, 0, func.nome, fmt.get('data_text'))
                ws.write(row, 1, cargo, fmt.get('data_text'))
                ws.write(row, 2, item.salario_real, fmt.get('data_money'))
                ws.write(row, 3, item.decimo_terceiro, fmt.get('data_money'))
                
                total_geral += item.decimo_terceiro
                row += 1

            row += 1
            ws.write(row, 2, "TOTAL:", fmt.get('total_label'))
            ws.write(row, 3, total_geral, fmt.get('total_final_money'))

        finally:
            if should_close and workbook:
                workbook.close()
                if output:
                    output.seek(0)
                    return output