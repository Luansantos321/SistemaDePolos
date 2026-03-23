"""
URL configuration for polo_escolar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from portal import views as portal_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),

    # Logout (opcional)
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Home do sistema
    path('home/', portal_views.home, name='home'),


   
    path('usuarios/', include('usuarios.urls')),
    path('escolas/', include('escolas.urls')),
    path('core/', include('core.urls')),
    path('', include('portal.urls')), 
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
