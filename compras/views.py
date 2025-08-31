from django.shortcuts import render

# Create your views here.

# compras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Fornecedor, CartaoCredito, Compra
from lancamentos.models import Lancamento

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Estatísticas gerais
    hoje = timezone.now().date()
    mes_atual = hoje.replace(day=1)
    
    # Lançamentos do mês
    lancamentos_mes = Lancamento.objects.filter(data__gte=mes_atual)
    total_vendas_mes = sum(l.total_vendas for l in lancamentos_mes)
    total_vista_mes = sum(l.total_a_vista for l in lancamentos_mes)
    total_credito_mes = sum(l.total_credito for l in lancamentos_mes)
    
    # Compras do mês
    compras_mes = Compra.objects.filter(data_compra__gte=mes_atual)
    total_compras_mes = compras_mes.aggregate(total=Sum('valor_total'))['total'] or 0
    
    # Últimas movimentações
    ultimos_lancamentos = Lancamento.objects.all()[:5]
    ultimas_compras = Compra.objects.all()[:5]
    
    context = {
        'total_vendas_mes': total_vendas_mes,
        'total_vista_mes': total_vista_mes,
        'total_credito_mes': total_credito_mes,
        'total_compras_mes': total_compras_mes,
        'ultimos_lancamentos': ultimos_lancamentos,
        'ultimas_compras': ultimas_compras,
        'mes_atual': mes_atual.strftime('%B %Y'),
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def lancamentos_list(request):
    lancamentos = Lancamento.objects.all()
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if data_inicio:
        lancamentos = lancamentos.filter(data__gte=data_inicio)
    if data_fim:
        lancamentos = lancamentos.filter(data__lte=data_fim)
    
    # Estatísticas
    stats = lancamentos.aggregate(
        total_pix=Sum('pix'),
        total_dinheiro=Sum('dinheiro'),
        total_debito=Sum('cartao_debito'),
        total_credito=Sum('cartao_credito')
    )
    
    total_geral = (stats['total_pix'] or 0) + (stats['total_dinheiro'] or 0) + (stats['total_debito'] or 0) + (stats['total_credito'] or 0)
    total_vista = (stats['total_pix'] or 0) + (stats['total_dinheiro'] or 0) + (stats['total_debito'] or 0)
    
    # Paginação
    paginator = Paginator(lancamentos, 15)
    page = request.GET.get('page')
    lancamentos_page = paginator.get_page(page)
    
    context = {
        'lancamentos': lancamentos_page,
        'stats': {
            'total_pix': stats['total_pix'] or 0,
            'total_dinheiro': stats['total_dinheiro'] or 0,
            'total_debito': stats['total_debito'] or 0,
            'total_credito': stats['total_credito'] or 0,
            'total_geral': total_geral,
            'total_vista': total_vista,
            'count': lancamentos.count()
        },
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim
        }
    }
    
    return render(request, 'lancamentos/list.html', context)

@login_required
def lancamento_create(request):
    if request.method == 'POST':
        try:
            data = request.POST.get('data')
            if data:
                data = datetime.strptime(data, '%Y-%m-%d').date()
            else:
                data = timezone.now().date()
            
            lancamento = Lancamento.objects.create(
                data=data,
                pix=float(request.POST.get('pix', 0) or 0),
                dinheiro=float(request.POST.get('dinheiro', 0) or 0),
                cartao_debito=float(request.POST.get('cartao_debito', 0) or 0),
                cartao_credito=float(request.POST.get('cartao_credito', 0) or 0)
            )
            
            messages.success(request, 'Lançamento criado com sucesso!')
            return redirect('lancamentos_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar lançamento: {str(e)}')
    
    return render(request, 'lancamentos/form.html', {
        'title': 'Novo Lançamento',
        'action': 'create'
    })

@login_required
def lancamento_edit(request, pk):
    lancamento = get_object_or_404(Lancamento, pk=pk)
    
    if request.method == 'POST':
        try:
            data = request.POST.get('data')
            if data:
                lancamento.data = datetime.strptime(data, '%Y-%m-%d').date()
            
            lancamento.pix = float(request.POST.get('pix', 0) or 0)
            lancamento.dinheiro = float(request.POST.get('dinheiro', 0) or 0)
            lancamento.cartao_debito = float(request.POST.get('cartao_debito', 0) or 0)
            lancamento.cartao_credito = float(request.POST.get('cartao_credito', 0) or 0)
            lancamento.save()
            
            messages.success(request, 'Lançamento atualizado com sucesso!')
            return redirect('lancamentos_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar lançamento: {str(e)}')
    
    return render(request, 'lancamentos/form.html', {
        'title': 'Editar Lançamento',
        'action': 'edit',
        'lancamento': lancamento
    })

@login_required
def lancamento_delete(request, pk):
    if request.method == 'POST':
        lancamento = get_object_or_404(Lancamento, pk=pk)
        lancamento.delete()
        messages.success(request, 'Lançamento excluído com sucesso!')
    
    return redirect('lancamentos_list')

@login_required
def compras_list(request):
    compras = Compra.objects.select_related('fornecedor', 'cartao_credito').all()
    
    # Filtros
    fornecedor_id = request.GET.get('fornecedor')
    forma_pagamento = request.GET.get('forma_pagamento')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    search = request.GET.get('search')
    
    if fornecedor_id:
        compras = compras.filter(fornecedor_id=fornecedor_id)
    if forma_pagamento:
        compras = compras.filter(forma_pagamento=forma_pagamento)
    if data_inicio:
        compras = compras.filter(data_compra__gte=data_inicio)
    if data_fim:
        compras = compras.filter(data_compra__lte=data_fim)
    if search:
        compras = compras.filter(
            Q(descricao__icontains=search) | 
            Q(fornecedor__nome__icontains=search)
        )
    
    # Estatísticas
    total_compras = compras.aggregate(total=Sum('valor_total'))['total'] or 0
    total_vista = compras.filter(forma_pagamento__in=['dinheiro', 'pix', 'debito']).aggregate(total=Sum('valor_total'))['total'] or 0
    total_credito = compras.filter(forma_pagamento='credito').aggregate(total=Sum('valor_total'))['total'] or 0
    
    # Paginação
    paginator = Paginator(compras, 15)
    page = request.GET.get('page')
    compras_page = paginator.get_page(page)
    
    # Dados para filtros
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'compras': compras_page,
        'fornecedores': fornecedores,
        'stats': {
            'total_compras': total_compras,
            'total_vista': total_vista,
            'total_credito': total_credito,
            'count': compras.count()
        },
        'filtros': {
            'fornecedor_id': int(fornecedor_id) if fornecedor_id else None,
            'forma_pagamento': forma_pagamento,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'search': search
        },
        'FORMA_PAGAMENTO_CHOICES': Compra.FORMA_PAGAMENTO_CHOICES
    }
    
    return render(request, 'compras/list.html', context)

@login_required
def compra_create(request):
    if request.method == 'POST':
        try:
            data_compra = request.POST.get('data_compra')
            if data_compra:
                data_compra = datetime.strptime(data_compra, '%Y-%m-%d').date()
            else:
                data_compra = timezone.now().date()
            
            compra = Compra(
                fornecedor_id=request.POST.get('fornecedor'),
                descricao=request.POST.get('descricao'),
                valor_total=float(request.POST.get('valor_total')),
                data_compra=data_compra,
                forma_pagamento=request.POST.get('forma_pagamento'),
                observacoes=request.POST.get('observacoes', '')
            )
            
            if compra.forma_pagamento == 'credito':
                compra.cartao_credito_id = request.POST.get('cartao_credito')
                compra.parcelas = int(request.POST.get('parcelas', 1))
            
            compra.save()
            
            messages.success(request, 'Compra criada com sucesso!')
            return redirect('compras_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar compra: {str(e)}')
    
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('nome')
    cartoes = CartaoCredito.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'title': 'Nova Compra',
        'action': 'create',
        'fornecedores': fornecedores,
        'cartoes': cartoes,
        'FORMA_PAGAMENTO_CHOICES': Compra.FORMA_PAGAMENTO_CHOICES,
        'PARCELAS_CHOICES': Compra.PARCELAS_CHOICES
    }
    
    return render(request, 'compras/form.html', context)

@login_required
def compra_edit(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    
    if request.method == 'POST':
        try:
            data_compra = request.POST.get('data_compra')
            if data_compra:
                compra.data_compra = datetime.strptime(data_compra, '%Y-%m-%d').date()
            
            compra.fornecedor_id = request.POST.get('fornecedor')
            compra.descricao = request.POST.get('descricao')
            compra.valor_total = float(request.POST.get('valor_total'))
            compra.forma_pagamento = request.POST.get('forma_pagamento')
            compra.observacoes = request.POST.get('observacoes', '')
            
            if compra.forma_pagamento == 'credito':
                compra.cartao_credito_id = request.POST.get('cartao_credito')
                compra.parcelas = int(request.POST.get('parcelas', 1))
            else:
                compra.cartao_credito = None
                compra.parcelas = 1
            
            compra.save()
            
            messages.success(request, 'Compra atualizada com sucesso!')
            return redirect('compras_list')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar compra: {str(e)}')
    
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('nome')
    cartoes = CartaoCredito.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'title': 'Editar Compra',
        'action': 'edit',
        'compra': compra,
        'fornecedores': fornecedores,
        'cartoes': cartoes,
        'FORMA_PAGAMENTO_CHOICES': Compra.FORMA_PAGAMENTO_CHOICES,
        'PARCELAS_CHOICES': Compra.PARCELAS_CHOICES
    }
    
    return render(request, 'compras/form.html', context)

@login_required
def compra_delete(request, pk):
    if request.method == 'POST':
        compra = get_object_or_404(Compra, pk=pk)
        compra.delete()
        messages.success(request, 'Compra excluída com sucesso!')
    
    return redirect('compras_list')

@login_required
def compra_detail(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    return render(request, 'compras/detail.html', {'compra': compra})

# APIs para dados dinâmicos
@login_required
def api_cartoes(request):
    cartoes = CartaoCredito.objects.filter(ativo=True).values('id', 'nome')
    return JsonResponse(list(cartoes), safe=False)