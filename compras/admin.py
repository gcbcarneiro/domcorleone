from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Fornecedor, CartaoCredito, Compra, ParcelaCompra

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'contato', 'total_compras', 'ativo_status']
    list_filter = ['ativo', 'created_at']
    search_fields = ['nome', 'contato']
    
    def formatar_valor(self, valor):
        if valor:
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "R$ 0,00"

    def total_compras(self, obj):
        total = obj.compra_set.aggregate(total=Sum('valor_total'))['total']
        return self.formatar_valor(total or 0)
    total_compras.short_description = "Total Compras"

    def ativo_status(self, obj):
        if obj.ativo:
            return format_html('<span style="color: #28a745;">✅ Ativo</span>')
        return format_html('<span style="color: #dc3545;">❌ Inativo</span>')
    ativo_status.short_description = "Status"

@admin.register(CartaoCredito)
class CartaoCreditoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'limite_formatado', 'vencimento_fatura', 'total_usado', 'ativo_status']
    list_filter = ['ativo', 'vencimento_fatura']
    
    def formatar_valor(self, valor):
        if valor:
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return "R$ 0,00"

    def limite_formatado(self, obj):
        return self.formatar_valor(obj.limite)
    limite_formatado.short_description = "Limite"

    def total_usado(self, obj):
        # Total usado nos últimos 30 dias (aproximação do período da fatura)
        data_limite = timezone.now().date() - timedelta(days=30)
        total = obj.compra_set.filter(
            data_compra__gte=data_limite
        ).aggregate(total=Sum('valor_total'))['total']
        return self.formatar_valor(total or 0)
    total_usado.short_description = "Usado (30 dias)"

    def ativo_status(self, obj):
        if obj.ativo:
            return format_html('<span style="color: #28a745;">✅ Ativo</span>')
        return format_html('<span style="color: #dc3545;">❌ Inativo</span>')
    ativo_status.short_description = "Status"

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = [
        'data_formatada',
        'fornecedor',
        'descricao_resumo', 
        'valor_formatado',
        'forma_pagamento_display',
        'status_pagamento_display'
    ]
    list_filter = [
        'forma_pagamento', 
        'data_compra', 
        'fornecedor',
        'cartao_credito'
    ]
    search_fields = ['fornecedor__nome', 'descricao']
    date_hierarchy = 'data_compra'
    ordering = ['-data_compra', '-created_at']
    
    fieldsets = (
        ('🛒 Informações da Compra', {
            'fields': ('fornecedor', 'descricao', 'valor_total', 'data_compra')
        }),
        ('💳 Forma de Pagamento', {
            'fields': ('forma_pagamento', 'cartao_credito', 'parcelas'),
            'description': 'Para Dinheiro/PIX/Débito: sai do saldo imediatamente. Para Crédito: selecione cartão e parcelas.'
        }),
        ('📋 Informações Adicionais', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('📊 Resumo da Compra', {
            'fields': ('get_resumo_display',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['get_resumo_display']

    def formatar_valor(self, valor):
        """Função auxiliar para formatar valores monetários"""
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Filtrar apenas fornecedores ativos
        form.base_fields['fornecedor'].queryset = Fornecedor.objects.filter(ativo=True)
        
        # Filtrar apenas cartões ativos
        form.base_fields['cartao_credito'].queryset = CartaoCredito.objects.filter(ativo=True)
        
        return form

    def get_resumo_display(self, obj):
        if obj.pk:
            data_str = obj.data_compra.strftime('%d/%m/%Y')
            valor_str = self.formatar_valor(obj.valor_total)
            
            # Informações de pagamento
            pagamento_info = ""
            if obj.forma_pagamento == 'credito':
                valor_parcela_str = self.formatar_valor(obj.valor_parcela)
                pagamento_info = f"""
                    💳 Cartão: {obj.cartao_credito.nome}<br>
                    🔄 Parcelas: {obj.parcelas}x de {valor_parcela_str}<br>
                """
            
            html = f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace;">
                    <strong>🛒 RESUMO DA COMPRA - {data_str}</strong><br><br>
                    🏪 <strong>Fornecedor:</strong> {obj.fornecedor.nome}<br>
                    📝 <strong>Descrição:</strong> {obj.descricao}<br>
                    💰 <strong>Valor Total:</strong> {valor_str}<br>
                    💳 <strong>Forma de Pagamento:</strong> {obj.get_forma_pagamento_display()}<br>
                    {pagamento_info}
                    <hr style="margin: 10px 0;">
                    📊 <strong>STATUS:</strong> {obj.status_pagamento}<br>
                    {'✅ <strong>Saldo debitado imediatamente</strong>' if obj.sai_saldo_imediato else '⏳ <strong>Valor será debitado conforme vencimento das parcelas</strong>'}
                </div>
            """
            return format_html(html)
        return "Salve a compra para ver o resumo"
    
    get_resumo_display.short_description = "📊 Resumo Detalhado"

    def data_formatada(self, obj):
        data_str = obj.data_compra.strftime('%d/%m/%Y')
        return format_html('<strong>📅 {}</strong>', data_str)
    data_formatada.short_description = "Data"
    data_formatada.admin_order_field = 'data_compra'

    def descricao_resumo(self, obj):
        if len(obj.descricao) > 50:
            return obj.descricao[:50] + "..."
        return obj.descricao
    descricao_resumo.short_description = "Descrição"

    def valor_formatado(self, obj):
        valor_str = self.formatar_valor(obj.valor_total)
        return format_html('<strong style="color: #dc3545;">💰 {}</strong>', valor_str)
    valor_formatado.short_description = "Valor"
    valor_formatado.admin_order_field = 'valor_total'

    def forma_pagamento_display(self, obj):
        cores = {
            'dinheiro': '#28a745',
            'pix': '#17a2b8', 
            'debito': '#ffc107',
            'credito': '#dc3545'
        }
        cor = cores.get(obj.forma_pagamento, '#6c757d')
        
        if obj.forma_pagamento == 'credito':
            texto = f"{obj.get_forma_pagamento_display()} ({obj.cartao_credito.nome})"
        else:
            texto = obj.get_forma_pagamento_display()
            
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', cor, texto)
    forma_pagamento_display.short_description = "Pagamento"

    def status_pagamento_display(self, obj):
        if obj.sai_saldo_imediato:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ Pago</span>')
        else:
            return format_html('<span style="color: #ffc107; font-weight: bold;">🔄 {}x</span>', obj.parcelas)
    status_pagamento_display.short_description = "Status"

    class Media:
        js = ('admin/js/compras.js',)  # Para funcionalidades JS futuras

# Customizar títulos do admin (apenas se não foi feito antes)
if not hasattr(admin.site, '_customizado'):
    admin.site.site_header = "💰 Sistema de Gestão Financeira"
    admin.site.site_title = "Gestão Admin"
    admin.site.index_title = "Painel de Controle"
    admin.site._customizado = True