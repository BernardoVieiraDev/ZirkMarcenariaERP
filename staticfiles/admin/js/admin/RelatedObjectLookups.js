import os
import requests
from django.conf import settings
from django.forms import modelformset_factory
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages # Importa o módulo de mensagens

from .forms import (DadosTrabalhistasForm, DocumentosFuncionarioForm,
                    EnderecoFuncionarioForm, FuncionarioForm)
from .models import (DadosTrabalhistas, DocumentosFuncionario,
                    EnderecoFuncionario, Funcionario)
from .services import \
    CadastroFuncionarioExcelService  # importe o service que criamos


def criar_funcionario(request):
    if request.method == 'POST':
        funcionario_form = FuncionarioForm(request.POST)
        endereco_form = EnderecoFuncionarioForm(request.POST)
        documentos_form = DocumentosFuncionarioForm(request.POST)
        dados_trabalhistas_form = DadosTrabalhistasForm(request.POST)

        if funcionario_form.is_valid() and endereco_form.is_valid() and documentos_form.is_valid() and dados_trabalhistas_form.is_valid():
            funcionario = funcionario_form.save()
            
            endereco = endereco_form.save(commit=False)
            endereco.funcionario = funcionario
            endereco.save()

            documentos = documentos_form.save(commit=False)
            documentos.funcionario = funcionario
            documentos.save()

            dados_trabalhistas = dados_trabalhistas_form.save(commit=False)
            dados_trabalhistas.funcionario = funcionario
            dados_trabalhistas.save()


            return redirect('funcionarios:funcionarios')
    else:
        funcionario_form = FuncionarioForm()
        endereco_form = EnderecoFuncionarioForm()
        documentos_form = DocumentosFuncionarioForm()
        dados_trabalhistas_form = DadosTrabalhistasForm()

    return render(request, 'core/funcionarios/form.html', {
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'documentos_form': documentos_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
        'title': 'Criar Novo Funcionário'
    })

def lista_funcionarios(request):
    qs = Funcionario.objects.all()
    return render(request, 'core/funcionarios/list.html', {'funcionarios': qs})

def editar_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    try:
        endereco = funcionario.endereco #type: ignore
    except EnderecoFuncionario.DoesNotExist:
        endereco = EnderecoFuncionario(funcionario=funcionario)

    try:
        documentos = funcionario.documentos #type: ignore
    except DocumentosFuncionario.DoesNotExist:
        documentos = DocumentosFuncionario(funcionario=funcionario)

    try:
        dados_trabalhistas = funcionario.dados_trabalhistas #type: ignore
    except DadosTrabalhistas.DoesNotExist:
        dados_trabalhistas = DadosTrabalhistas(funcionario=funcionario)

    if request.method == 'POST':
        # Criando forms apenas para campos editáveis
        funcionario_form = FuncionarioForm(request.POST, instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(request.POST, instance=endereco)
        dados_trabalhistas_form = DadosTrabalhistasForm(request.POST, instance=dados_trabalhistas)
        # Se quiser permitir edição de documentos sensíveis, descomente:
        # documentos_form = DocumentosFuncionarioForm(request.POST, instance=documentos)

        if funcionario_form.is_valid() and endereco_form.is_valid() and dados_trabalhistas_form.is_valid():
            funcionario_form.save()
            endereco_form.save()
            dados_trabalhistas_form.save()
            # documentos_form.save()  # só se estiver editando documentos

            return redirect('funcionarios:funcionarios')
    else:
        funcionario_form = FuncionarioForm(instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(instance=endereco)
        dados_trabalhistas_form = DadosTrabalhistasForm(instance=dados_trabalhistas)
        # documentos_form = DocumentosFuncionarioForm(instance=documentos)

    return render(request, 'core/funcionarios/form.html', {
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
        # 'documentos_form': documentos_form,  # incluir se for editável
        'title': 'Editar Funcionário'
    })
def deletar_funcionario(request, pk):
    obj = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('funcionarios:funcionarios')
    return render(request, 'core/funcionarios/delete.html', {'object': obj})

def gerar_excel_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)

    # Caminho temporário para salvar o arquivo. Usamos MEDIA_ROOT para garantir que o Django gerencie o caminho.
    caminho_temp = os.path.join(settings.MEDIA_ROOT, 'temp', f'Cadastro_{funcionario.nome}_{pk}.xlsx')
    
    # Garante que o diretório exista
    os.makedirs(os.path.dirname(caminho_temp), exist_ok=True)

    # Gera o Excel (agora usando o método correto e tratando o retorno)
    sucesso = CadastroFuncionarioExcelService.gerar_cadastro(funcionario, caminho_arquivo=caminho_temp)

    if sucesso and os.path.exists(caminho_temp):
        nome_arquivo = f'Cadastro_Admissao_{funcionario.nome}.xlsx'
        try:
            # Retorna o arquivo para download
            response = FileResponse(open(caminho_temp, 'rb'), as_attachment=True, filename=nome_arquivo)
            return response
        finally:
            # Tenta remover o arquivo temporário após o envio
            try:
                os.remove(caminho_temp)
            except OSError as e:
                print(f"Erro ao remover arquivo temporário {caminho_temp}: {e}")
    
    messages.error(request, "Erro fatal ao gerar o arquivo Excel.")
    return redirect('funcionarios:lista_funcionarios') # Redireciona para a lista em caso de falha

def buscar_endereco_por_cep(request):
    cep = request.GET.get('cep', '').replace('-', '')
    if len(cep) != 8:
        return JsonResponse({'error': 'CEP inválido'}, status=400)

    url = f'https://viacep.com.br/ws/{cep}/json/'

    try:
        response = requests.get(url)
        data = response.json()
        if 'erro' in data:
            return JsonResponse({'error': 'CEP não encontrado'}, status=404)
        return JsonResponse({
            'endereco': data.get('logradouro', ''),
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'uf': data.get('uf', ''),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
/*global SelectBox, interpolate*/
// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.
'use strict';
{
    const $ = django.jQuery;
    let popupIndex = 0;
    const relatedWindows = [];

    function dismissChildPopups() {
        relatedWindows.forEach(function(win) {
            if(!win.closed) {
                win.dismissChildPopups();
                win.close();    
            }
        });
    }

    function setPopupIndex() {
        if(document.getElementsByName("_popup").length > 0) {
            const index = window.name.lastIndexOf("__") + 2;
            popupIndex = parseInt(window.name.substring(index));   
        } else {
            popupIndex = 0;
        }
    }

    function addPopupIndex(name) {
        return name + "__" + (popupIndex + 1);
    }

    function removePopupIndex(name) {
        return name.replace(new RegExp("__" + (popupIndex + 1) + "$"), '');
    }

    function showAdminPopup(triggeringLink, name_regexp, add_popup) {
        const name = addPopupIndex(triggeringLink.id.replace(name_regexp, ''));
        const href = new URL(triggeringLink.href);
        if (add_popup) {
            href.searchParams.set('_popup', 1);
        }
        const win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        relatedWindows.push(win);
        win.focus();
        return false;
    }

    function showRelatedObjectLookupPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^lookup_/, true);
    }

    function dismissRelatedLookupPopup(win, chosenId) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
            elem.value += ',' + chosenId;
        } else {
            elem.value = chosenId;
        }
        $(elem).trigger('change');
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function showRelatedObjectPopup(triggeringLink) {
        return showAdminPopup(triggeringLink, /^(change|add|delete)_/, false);
    }

    function updateRelatedObjectLinks(triggeringLink) {
        const $this = $(triggeringLink);
        const siblings = $this.nextAll('.view-related, .change-related, .delete-related');
        if (!siblings.length) {
            return;
        }
        const value = $this.val();
        if (value) {
            siblings.each(function() {
                const elm = $(this);
                elm.attr('href', elm.attr('data-href-template').replace('__fk__', value));
                elm.removeAttr('aria-disabled');
            });
        } else {
            siblings.removeAttr('href');
            siblings.attr('aria-disabled', true);
        }
    }

    function updateRelatedSelectsOptions(currentSelect, win, objId, newRepr, newId, skipIds = []) {
        // After create/edit a model from the options next to the current
        // select (+ or :pencil:) update ForeignKey PK of the rest of selects
        // in the page.

        const path = win.location.pathname;
        // Extract the model from the popup url '.../<model>/add/' or
        // '.../<model>/<id>/change/' depending the action (add or change).
        const modelName = path.split('/')[path.split('/').length - (objId ? 4 : 3)];
        // Select elements with a specific model reference and context of "available-source".
        const selectsRelated = document.querySelectorAll(`[data-model-ref="${modelName}"] [data-context="available-source"]`);

        selectsRelated.forEach(function(select) {
            if (currentSelect === select || skipIds && skipIds.includes(select.id)) {
                return;
            }

            let option = select.querySelector(`option[value="${objId}"]`);

            if (!option) {
                option = new Option(newRepr, newId);
                select.options.add(option);
                // Update SelectBox cache for related fields.
                if (window.SelectBox !== undefined && !SelectBox.cache[currentSelect.id]) {
                    SelectBox.add_to_cache(select.id, option);
                    SelectBox.redisplay(select.id);
                }
                return;
            }

            option.textContent = newRepr;
            option.value = newId;
        });
    }

    function dismissAddRelatedObjectPopup(win, newId, newRepr) {
        const name = removePopupIndex(win.name);
        const elem = document.getElementById(name);
        if (elem) {
            const elemName = elem.nodeName.toUpperCase();
            if (elemName === 'SELECT') {
                elem.options[elem.options.length] = new Option(newRepr, newId, true, true);
                updateRelatedSelectsOptions(elem, win, null, newRepr, newId);
            } else if (elemName === 'INPUT') {
                if (elem.classList.contains('vManyToManyRawIdAdminField') && elem.value) {
                    elem.value += ',' + newId;
                } else {
                    elem.value = newId;
                }
            }
            // Trigger a change event to update related links if required.
            $(elem).trigger('change');
        } else {
            const toId = name + "_to";
            const toElem = document.getElementById(toId);
            const o = new Option(newRepr, newId);
            SelectBox.add_to_cache(toId, o);
            SelectBox.redisplay(toId);
            if (toElem && toElem.nodeName.toUpperCase() === 'SELECT') {
                const skipIds = [name + "_from"];
                updateRelatedSelectsOptions(toElem, win, null, newRepr, newId, skipIds);
            }
        }
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function dismissChangeRelatedObjectPopup(win, objId, newRepr, newId) {
        const id = removePopupIndex(win.name.replace(/^edit_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = $(selectsSelector);
        selects.find('option').each(function() {
            if (this.value === objId) {
                this.textContent = newRepr;
                this.value = newId;
            }
        }).trigger('change');
        updateRelatedSelectsOptions(selects[0], win, objId, newRepr, newId);
        selects.next().find('.select2-selection__rendered').each(function() {
            // The element can have a clear button as a child.
            // Use the lastChild to modify only the displayed value.
            this.lastChild.textContent = newRepr;
            this.title = newRepr;
        });
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    function dismissDeleteRelatedObjectPopup(win, objId) {
        const id = removePopupIndex(win.name.replace(/^delete_/, ''));
        const selectsSelector = interpolate('#%s, #%s_from, #%s_to', [id, id, id]);
        const selects = $(selectsSelector);
        selects.find('option').each(function() {
            if (this.value === objId) {
                $(this).remove();
            }
        }).trigger('change');
        const index = relatedWindows.indexOf(win);
        if (index > -1) {
            relatedWindows.splice(index, 1);
        }
        win.close();
    }

    window.showRelatedObjectLookupPopup = showRelatedObjectLookupPopup;
    window.dismissRelatedLookupPopup = dismissRelatedLookupPopup;
    window.showRelatedObjectPopup = showRelatedObjectPopup;
    window.updateRelatedObjectLinks = updateRelatedObjectLinks;
    window.dismissAddRelatedObjectPopup = dismissAddRelatedObjectPopup;
    window.dismissChangeRelatedObjectPopup = dismissChangeRelatedObjectPopup;
    window.dismissDeleteRelatedObjectPopup = dismissDeleteRelatedObjectPopup;
    window.dismissChildPopups = dismissChildPopups;
    window.relatedWindows = relatedWindows;

    // Kept for backward compatibility
    window.showAddAnotherPopup = showRelatedObjectPopup;
    window.dismissAddAnotherPopup = dismissAddRelatedObjectPopup;

    window.addEventListener('unload', function(evt) {
        window.dismissChildPopups();
    });

    $(document).ready(function() {
        setPopupIndex();
        $("a[data-popup-opener]").on('click', function(event) {
            event.preventDefault();
            opener.dismissRelatedLookupPopup(window, $(this).data("popup-opener"));
        });
        $('body').on('click', '.related-widget-wrapper-link[data-popup="yes"]', function(e) {
            e.preventDefault();
            if (this.href) {
                const event = $.Event('django:show-related', {href: this.href});
                $(this).trigger(event);
                if (!event.isDefaultPrevented()) {
                    showRelatedObjectPopup(this);
                }
            }
        });
        $('body').on('change', '.related-widget-wrapper select', function(e) {
            const event = $.Event('django:update-related');
            $(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                updateRelatedObjectLinks(this);
            }
        });
        $('.related-widget-wrapper select').trigger('change');
        $('body').on('click', '.related-lookup', function(e) {
            e.preventDefault();
            const event = $.Event('django:lookup-related');
            $(this).trigger(event);
            if (!event.isDefaultPrevented()) {
                showRelatedObjectLookupPopup(this);
            }
        });
    });
}
