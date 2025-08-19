from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Lancamento

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = [
        'data_formatada', 
        'pix_formatado', 
        'dinheiro_formatado', 
        'cartao_formatado',
        'total_vendas_formatado',
        'status_pagamento'
    ]
    list_filter = ['data', 'created_at']
    search_fields = ['data']
    date_hierarchy = 'data'
    ordering = ['-data']
    
    fieldsets = (
        ('📅 Informações da Data', {
            'fields': ('data',)
        }),
        ('💰 Vendas do Dia', {
            'fields': ('pix', 'dinheiro', 'cartao'),
            'description': 'Informe os valores recebidos em cada forma de pagamento'
        }),
        ('📊 Resumo Automático', {
            'fields': ('get_resumo_display',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['get_resumo_display', 'created_at', 'updated_at']

    def formatar_valor(self, valor):
        """Função auxiliar para formatar valores monetários"""
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    def get_resumo_display(self, obj):
        if obj.pk:
            data_str = obj.data.strftime('%d/%m/%Y')
            pix_str = self.formatar_valor(obj.pix)
            dinheiro_str = self.formatar_valor(obj.dinheiro)
            cartao_str = self.formatar_valor(obj.cartao)
            total_str = self.formatar_valor(obj.total_vendas)
            vista_str = self.formatar_valor(obj.total_a_vista)
            receber_str = self.formatar_valor(obj.total_a_receber)
            
            html = f"""
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace;">
                    <strong>📊 RESUMO VENDAS - {data_str}</strong><br><br>
                    💰 <strong>VENDAS DO DIA:</strong><br>
                    📱 PIX: {pix_str}<br>
                    💵 Dinheiro: {dinheiro_str}<br>
                    💳 Cartão: {cartao_str}<br>
                    <hr style="margin: 10px 0;">
                    📊 <strong>RESUMO:</strong><br>
                    🔢 Total Vendas: <strong>{total_str}</strong><br>
                    ├─ 💸 À vista (PIX+Dinheiro): <strong>{vista_str}</strong> → Crédito imediato<br>
                    └─ 💳 Cartão: <strong>{receber_str}</strong> → A receber
                </div>
            """
            return format_html(html)
        return "Salve o lançamento para ver o resumo"
    
    get_resumo_display.short_description = "📊 Resumo Detalhado"

    def data_formatada(self, obj):
        data_str = obj.data.strftime('%d/%m/%Y')
        return format_html('<strong>📅 {}</strong>', data_str)
    data_formatada.short_description = "Data"
    data_formatada.admin_order_field = 'data'

    def pix_formatado(self, obj):
        valor_str = self.formatar_valor(obj.pix)
        return format_html('<span style="color: #28a745;">📱 {}</span>', valor_str)
    pix_formatado.short_description = "PIX"
    pix_formatado.admin_order_field = 'pix'

    def dinheiro_formatado(self, obj):
        valor_str = self.formatar_valor(obj.dinheiro)
        return format_html('<span style="color: #17a2b8;">💵 {}</span>', valor_str)
    dinheiro_formatado.short_description = "Dinheiro"
    dinheiro_formatado.admin_order_field = 'dinheiro'

    def cartao_formatado(self, obj):
        valor_str = self.formatar_valor(obj.cartao)
        return format_html('<span style="color: #ffc107;">💳 {}</span>', valor_str)
    cartao_formatado.short_description = "Cartão"
    cartao_formatado.admin_order_field = 'cartao'

    def total_vendas_formatado(self, obj):
        valor_str = self.formatar_valor(obj.total_vendas)
        return format_html('<strong style="color: #dc3545;">🔢 {}</strong>', valor_str)
    total_vendas_formatado.short_description = "Total Vendas"

    def status_pagamento(self, obj):
        if obj.total_a_vista > obj.total_a_receber:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ Majoritariamente à vista</span>')
        elif obj.total_a_receber > obj.total_a_vista:
            return format_html('<span style="color: #ffc107; font-weight: bold;">⏳ Majoritariamente a receber</span>')
        else:
            return format_html('<span style="color: #17a2b8; font-weight: bold;">⚖️ Equilibrado</span>')
    status_pagamento.short_description = "Status"

    def changelist_view(self, request, extra_context=None):
        # Adicionar estatísticas ao topo da lista
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
            stats = qs.aggregate(
                total_pix=Sum('pix'),
                total_dinheiro=Sum('dinheiro'),
                total_cartao=Sum('cartao')
            )
            
            total_geral = (stats['total_pix'] or 0) + (stats['total_dinheiro'] or 0) + (stats['total_cartao'] or 0)
            total_a_vista = (stats['total_pix'] or 0) + (stats['total_dinheiro'] or 0)
            
            response.context_data['summary'] = {
                'total_pix': stats['total_pix'] or 0,
                'total_dinheiro': stats['total_dinheiro'] or 0,
                'total_cartao': stats['total_cartao'] or 0,
                'total_geral': total_geral,
                'total_a_vista': total_a_vista,
                'count': qs.count()
            }
        except:
            pass
            
        return response

# Customizar o título do admin
admin.site.site_header = "💰 Sistema de Lançamentos"
admin.site.site_title = "Vendas Admin"
admin.site.index_title = "Gerenciamento de Vendas"