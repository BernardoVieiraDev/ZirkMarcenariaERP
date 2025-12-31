import io
import xlsxwriter
from datetime import datetime
from django.db.models import Sum
from .models import LancamentoSocio, CategoriaSocio, Socio

class SocioExcelService:
    @staticmethod
    def gerar_planilha_anual(ano=None, socio_id=None):
        if not ano:
            ano = datetime.now().year

        # Define o Título e busca o nome do sócio se selecionado
        titulo_planilha = f"DESPESAS SÓCIOS - {ano}"
        if socio_id:
            try:
                socio_obj = Socio.objects.get(id=socio_id)
                titulo_planilha = f"DESPESAS - {socio_obj.nome.upper()} - {ano}"
            except Socio.DoesNotExist:
                pass

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(f"Relatório {ano}")

        # --- Formatação ---
        fmt_title = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        fmt_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1})
        fmt_group = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
        fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
        fmt_money_bold = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1, 'bold': True})
        fmt_text = workbook.add_format({'border': 1})

        # --- Cabeçalhos ---
        colunas = ["Categoria", "Média"] + [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"
        ] + ["Total Anual"]

        worksheet.merge_range('A1:O1', titulo_planilha, fmt_title)
        
        for idx, col in enumerate(colunas):
            worksheet.write(2, idx, col, fmt_header)

        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:O', 12)

        # --- 1. Buscar Dados (Com Filtro de Sócio) ---
        categorias = CategoriaSocio.objects.all().order_by('grupo', 'nome')
        
        # Query base
        qs = LancamentoSocio.objects.filter(data__year=ano)
        
        # AQUI ESTÁ A MÁGICA: Se tem sócio, filtra só ele
        if socio_id:
            qs = qs.filter(socio_id=socio_id)

        dados_raw = qs.values('categoria', 'data__month').annotate(total=Sum('valor'))

        dados_map = {}
        total_geral_ano = 0
        
        for d in dados_raw:
            c_id = d['categoria']
            mes = d['data__month']
            val = d['total']
            dados_map[(c_id, mes)] = val
            total_geral_ano += val

        # --- 2. Escrever Linhas ---
        row = 3
        ultimo_grupo = None

        for cat in categorias:
            if ultimo_grupo != cat.grupo:
                worksheet.merge_range(row, 0, row, 14, cat.get_grupo_display().upper(), fmt_group)
                row += 1
                ultimo_grupo = cat.grupo

            worksheet.write(row, 0, cat.nome, fmt_text)
            
            soma_linha = 0
            for mes in range(1, 13):
                valor = dados_map.get((cat.id, mes), 0)
                worksheet.write(row, mes + 1, valor, fmt_money)
                soma_linha += valor
            
            media = soma_linha / 12
            worksheet.write(row, 1, media, fmt_money)
            worksheet.write(row, 14, soma_linha, fmt_money_bold)
            row += 1

        # --- 3. Totais Gerais ---
        row += 1
        worksheet.write(row, 0, "TOTAL GERAL", fmt_header)
        letras_coluna = ['C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']
        
        worksheet.write_formula(row, 1, f'=AVERAGE(B4:B{row})', fmt_money_bold)
        for i, letra in enumerate(letras_coluna):
            idx_col = i + 2
            worksheet.write_formula(row, idx_col, f'=SUM({letra}4:{letra}{row})', fmt_money_bold)

        worksheet.write(row, 14, total_geral_ano, fmt_money_bold)

        workbook.close()
        output.seek(0)
        return output