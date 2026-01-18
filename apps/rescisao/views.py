from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import RescisaoForm
from .models import Rescisao
from .services import RescisaoExcelService


class RescisaoListView(LoginRequiredMixin, ListView):
    model = Rescisao
    template_name = 'core/rescisao/list.html'
    context_object_name = 'rescisoes'
    ordering = ['-data_demissao']

class RescisaoCreateView(LoginRequiredMixin, CreateView):
    model = Rescisao
    form_class = RescisaoForm
    template_name = 'core/rescisao/form_modal.html'
    success_url = reverse_lazy('rescisao:rescisao_list')

    def form_valid(self, form):
        messages.success(self.request, "Rescisão calculada e salva com sucesso!")
        return super().form_valid(form)

class RescisaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Rescisao
    form_class = RescisaoForm
    template_name = 'core/rescisao/form_modal.html'
    success_url = reverse_lazy('rescisao:rescisao_list')

    def form_valid(self, form):
        messages.success(self.request, "Rescisão atualizada com sucesso!")
        return super().form_valid(form)

class RescisaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Rescisao
    template_name = 'core/rescisao/delete_modal.html'
    success_url = reverse_lazy('rescisao:rescisao_list')

    def form_valid(self, form):
        messages.success(self.request, "Rescisão excluída com sucesso.")
        return super().form_valid(form)

@login_required
def gerar_excel_rescisao(request, pk):
    rescisao = Rescisao.objects.get(pk=pk)
    
    excel_file = RescisaoExcelService.gerar_termo_rescisao(rescisao)
    
    filename = f"Rescisao_{rescisao.funcionario.nome.replace(' ', '_')}.xlsx"
    
    response = HttpResponse(
        excel_file,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response