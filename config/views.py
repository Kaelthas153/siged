from django.shortcuts import render


def csrf_failure(request, reason=''):
    # No se muestran detalles internos ni el token de la solicitud.
    return render(request, 'csrf_failure.html', status=403)
