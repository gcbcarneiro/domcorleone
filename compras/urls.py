# compras/urls.py - CRIAR ESTE ARQUIVO NOVO
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Lançamentos
    path('lancamentos/', views.lancamentos_list, name='lancamentos_list'),
    path('lancamentos/novo/', views.lancamento_create, name='lancamento_create'),
    path('lancamentos/<int:pk>/editar/', views.lancamento_edit, name='lancamento_edit'),
    path('lancamentos/<int:pk>/excluir/', views.lancamento_delete, name='lancamento_delete'),
    
    # Compras
    path('compras/', views.compras_list, name='compras_list'),
    path('compras/nova/', views.compra_create, name='compra_create'),
    path('compras/<int:pk>/', views.compra_detail, name='compra_detail'),
    path('compras/<int:pk>/editar/', views.compra_edit, name='compra_edit'),
    path('compras/<int:pk>/excluir/', views.compra_delete, name='compra_delete'),
    
    # APIs
    path('api/cartoes/', views.api_cartoes, name='api_cartoes'),
]