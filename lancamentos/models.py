from django.db import models
<<<<<<< HEAD

# Create your models here.

from django.db import models
=======
>>>>>>> ad6a853 (atualização de projeto)
from django.utils import timezone
from decimal import Decimal

class Lancamento(models.Model):
    data = models.DateField(
        default=timezone.now,
        verbose_name="📅 Data",
        unique=True,
        help_text="Data do lançamento (apenas um por dia)"
    )
    pix = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="📱 PIX",
        help_text="Valor recebido via PIX"
    )
    dinheiro = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="💵 Dinheiro",
        help_text="Valor recebido em dinheiro"
    )
<<<<<<< HEAD
    cartao = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="💳 Cartão",
        help_text="Valor recebido via cartão"
=======
    cartao_debito = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="💳 Cartão Débito",
        help_text="Valor recebido via cartão de débito"
    )
    cartao_credito = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="🔄 Cartão Crédito",
        help_text="Valor recebido via cartão de crédito"
>>>>>>> ad6a853 (atualização de projeto)
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "💰 Lançamento"
        verbose_name_plural = "💰 Lançamentos"
        ordering = ['-data']

    def __str__(self):
        return f"Vendas do dia {self.data.strftime('%d/%m/%Y')} - Total: R$ {self.total_vendas:,.2f}"

    @property
    def total_vendas(self):
        """Total geral das vendas"""
<<<<<<< HEAD
        return self.pix + self.dinheiro + self.cartao

    @property
    def total_a_vista(self):
        """Crédito imediato (PIX + Dinheiro)"""
        return self.pix + self.dinheiro

    @property
    def total_a_receber(self):
        """Valor a receber (Cartão)"""
        return self.cartao
=======
        return self.pix + self.dinheiro + self.cartao_debito + self.cartao_credito

    @property
    def total_a_vista(self):
        """Crédito imediato (PIX + Dinheiro + Débito)"""
        return self.pix + self.dinheiro + self.cartao_debito

    @property
    def total_cartao(self):
        """Total dos cartões (Débito + Crédito)"""
        return self.cartao_debito + self.cartao_credito

    @property
    def total_credito(self):
        """Apenas cartão de crédito"""
        return self.cartao_credito
>>>>>>> ad6a853 (atualização de projeto)

    def get_resumo(self):
        """Retorna resumo formatado"""
        return f"""
        PIX: R$ {self.pix:,.2f}
        Dinheiro: R$ {self.dinheiro:,.2f}
<<<<<<< HEAD
        Cartão: R$ {self.cartao:,.2f}
        ────────────────
        Total: R$ {self.total_vendas:,.2f}
        À vista: R$ {self.total_a_vista:,.2f}
        A receber: R$ {self.total_a_receber:,.2f}
=======
        Cartão Débito: R$ {self.cartao_debito:,.2f}
        Cartão Crédito: R$ {self.cartao_credito:,.2f}
        ────────────────────────────────
        Total Vendas: R$ {self.total_vendas:,.2f}
        À vista (PIX+Dinheiro+Débito): R$ {self.total_a_vista:,.2f}
        Cartão Crédito: R$ {self.total_credito:,.2f}
>>>>>>> ad6a853 (atualização de projeto)
        """
    get_resumo.short_description = "📊 Resumo"