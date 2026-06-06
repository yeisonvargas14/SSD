from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from apps.convocatorias.models import Convocatoria
from apps.usuarios.models import LogAccion


def home(request):
    # Obtener la convocatoria activa actual (o la más reciente si no hay activa)
    convocatoria = Convocatoria.objects.filter(activa=True).first()
    if not convocatoria:
        convocatoria = Convocatoria.objects.order_by('-fecha_inicio').first()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        mensaje = request.POST.get('mensaje')

        if nombre and correo and mensaje:
            # Lógica de envío de correo
            subject = f'Contacto BecasUni: Mensaje de {nombre}'
            message_body = f'Nombre: {nombre}\nCorreo: {correo}\n\nMensaje:\n{mensaje}'
            
            try:
                send_mail(
                    subject,
                    message_body,
                    settings.DEFAULT_FROM_EMAIL or 'no-reply@becasuni.edu.co',
                    [settings.EMAIL_HOST_USER or 'admin@becasuni.edu.co'],
                    fail_silently=False,
                )
                
                # Registrar en log si el usuario está autenticado
                user_log = request.user if request.user.is_authenticated else None
                LogAccion.objects.create(
                    usuario=user_log,
                    accion='otro',
                    detalles={'tipo': 'contacto_landing', 'nombre': nombre, 'email': correo}
                )

                messages.success(request, '¡Gracias! Tu mensaje ha sido enviado correctamente al administrador.')
            except Exception as e:
                messages.error(request, f'Hubo un problema al enviar tu mensaje: {str(e)}')
            
            return redirect('landing:home')
        else:
            messages.warning(request, 'Por favor, completa todos los campos del formulario.')

    # Fechas por defecto si no hay convocatoria en base de datos
    cronograma = []
    if convocatoria:
        cronograma = [
            {'evento': 'Apertura de Convocatoria', 'fecha': convocatoria.fecha_inicio},
            {'evento': 'Cierre de Inscripciones', 'fecha': convocatoria.fecha_fin},
            {'evento': 'Evaluación de Solicitudes', 'fecha': convocatoria.fecha_fin + timezone.timedelta(days=7)},
            {'evento': 'Publicación de Resultados', 'fecha': convocatoria.fecha_fin + timezone.timedelta(days=12)},
        ]
    else:
        hoy = timezone.now().date()
        cronograma = [
            {'evento': 'Apertura de Convocatoria', 'fecha': hoy},
            {'evento': 'Cierre de Inscripciones', 'fecha': hoy + timezone.timedelta(days=30)},
            {'evento': 'Evaluación de Solicitudes', 'fecha': hoy + timezone.timedelta(days=37)},
            {'evento': 'Publicación de Resultados', 'fecha': hoy + timezone.timedelta(days=42)},
        ]

    context = {
        'convocatoria': convocatoria,
        'cronograma': cronograma,
    }
    return render(request, 'landing/home.html', context)
