from django.db import models

# Create your models here.

from django.db import models
from django.utils import timezone
from decimal import Decimal

class Fornecedor(models.Model):
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome do Fornecedor",
        help_text="Nome ou razão social do fornecedor"
    )
    contato = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contato",
        help_text="Telefone, email ou pessoa de contato"
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
        help_text="Informações adicionais sobre o fornecedor"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Fornecedor ativo para novas compras"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "🏪 Fornecedor"
        verbose_name_plural = "🏪 Fornecedores"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class CartaoCredito(models.Model):
    nome = models.CharField(
        max_length=50,
        verbose_name="Nome do Cartão",
        help_text="Ex: Santander, Nubank, Itaú"
    )
    limite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Limite",
        help_text="Limite do cartão (opcional)"
    )
    vencimento_fatura = models.IntegerField(
        choices=[(i, f"Dia {i}") for i in range(1, 32)],
        default=10,
        verbose_name="Vencimento da Fatura",
        help_text="Dia do mês que vence a fatura"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )

    class Meta:
        verbose_name = "💳 Cartão de Crédito"
        verbose_name_plural = "💳 Cartões de Crédito"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Compra(models.Model):
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', '💵 Dinheiro'),
        ('pix', '📱 PIX'),
        ('debito', '💳 Débito'),
        ('credito', '🔄 Crédito'),
    ]

    PARCELAS_CHOICES = [
        (1, '1x à vista'),
        (2, '2x sem juros'),
        (3, '3x sem juros'),
        (4, '4x sem juros'),
        (5, '5x sem juros'),
        (6, '6x sem juros'),
        (7, '7x sem juros'),
        (8, '8x sem juros'),
        (9, '9x sem juros'),
        (10, '10x sem juros'),
        (11, '11x sem juros'),
        (12, '12x sem juros'),
    ]

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        verbose_name="🏪 Fornecedor",
        help_text="Selecione o fornecedor"
    )
    descricao = models.CharField(
        max_length=200,
        verbose_name="📝 Descrição",
        help_text="Descrição dos itens comprados"
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="💰 Valor Total",
        help_text="Valor total da compra"
    )
    data_compra = models.DateField(
        default=timezone.now,
        verbose_name="📅 Data da Compra"
    )
    forma_pagamento = models.CharField(
        max_length=10,
        choices=FORMA_PAGAMENTO_CHOICES,
        default='dinheiro',
        verbose_name="💳 Forma de Pagamento"
    )
    
    # Campos específicos para crédito
    cartao_credito = models.ForeignKey(
        CartaoCredito,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="💳 Cartão de Crédito",
        help_text="Obrigatório apenas para pagamento no crédito"
    )
    parcelas = models.IntegerField(
        choices=PARCELAS_CHOICES,
        default=1,
        verbose_name="🔄 Parcelas",
        help_text="Número de parcelas (apenas para crédito)"
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name="📋 Observações",
        help_text="Informações adicionais sobre a compra"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "🛒 Compra"
        verbose_name_plural = "🛒 Compras"
        ordering = ['-data_compra', '-created_at']

    def __str__(self):
        return f"{self.fornecedor.nome} - {self.descricao[:50]} - R$ {self.valor_total}"

    @property
    def sai_saldo_imediato(self):
        """Verifica se o pagamento sai do saldo imediatamente"""
        return self.forma_pagamento in ['dinheiro', 'pix', 'debito']

    @property
    def valor_parcela(self):
        """Calcula o valor de cada parcela"""
        if self.forma_pagamento == 'credito' and self.parcelas > 1:
            return self.valor_total / self.parcelas
        return self.valor_total

    @property
    def status_pagamento(self):
        """Retorna status do pagamento"""
        if self.sai_saldo_imediato:
            return "✅ Pago (saldo imediato)"
        else:
            return f"⏳ Parcelado em {self.parcelas}x"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validar cartão de crédito obrigatório para forma de pagamento crédito
        if self.forma_pagamento == 'credito' and not self.cartao_credito:
            raise ValidationError({
                'cartao_credito': 'Cartão de crédito é obrigatório para pagamento no crédito.'
            })
        
        # Limpar cartão e parcelas se não for crédito
        if self.forma_pagamento != 'credito':
            self.cartao_credito = None
            self.parcelas = 1

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class ParcelaCompra(models.Model):
    """Model para controlar parcelas de compras no crédito"""
    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name='parcelas_detalhadas'
    )
    numero_parcela = models.IntegerField(verbose_name="Nº Parcela")
    valor_parcela = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor da Parcela"
    )
    data_vencimento = models.DateField(verbose_name="Data Vencimento")
    paga = models.BooleanField(default=False, verbose_name="Paga")
    data_pagamento = models.DateField(blank=True, null=True, verbose_name="Data Pagamento")

    class Meta:
        verbose_name = "📅 Parcela"
        verbose_name_plural = "📅 Parcelas"
        ordering = ['compra', 'numero_parcela']
        unique_together = ['compra', 'numero_parcela']

    def __str__(self):
        status = "✅" if self.paga else "⏳"
        return f"{status} {self.compra.fornecedor.nome} - Parcela {self.numero_parcela}/{self.compra.parcelas}"