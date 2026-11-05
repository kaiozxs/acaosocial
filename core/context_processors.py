from django.conf import settings


def projeto(request):
    return {
        "PIX_CHAVE": settings.PIX_CHAVE,
        "PIX_FAVORECIDO": settings.PIX_FAVORECIDO,
        "WHATSAPP": settings.WHATSAPP,
        "WHATSAPP_EXIBIR": settings.WHATSAPP_EXIBIR,
        "INSTAGRAM_URL": settings.INSTAGRAM_URL,
        "INSTAGRAM_USUARIO": settings.INSTAGRAM_USUARIO,
    }
