from django.views.generic import TemplateView

class DocsIndexView(TemplateView):
    template_name = "core/docs/index.html"

class DocsRHView(TemplateView):
    template_name = "core/docs/rh.html"

class DocsFinanceiroView(TemplateView):
    template_name = "core/docs/financeiro.html"

class DocsComercialView(TemplateView):
    template_name = "core/docs/comercial.html"

class DocsRelatoriosView(TemplateView):
    template_name = "core/docs/relatorios.html"