from django.conf import settings


def projeto(request):
    return {
        "PIX_CHAVE": settings.PIX_CHAVE,
        "PIX_COPIA_COLA": settings.PIX_COPIA_COLA,
        "PIX_FAVORECIDO": settings.PIX_FAVORECIDO,
        "WHATSAPP": settings.WHATSAPP,
        "WHATSAPP_EXIBIR": settings.WHATSAPP_EXIBIR,
        "INSTAGRAM_CT_URL": settings.INSTAGRAM_CT_URL,
        "INSTAGRAM_CT_USUARIO": settings.INSTAGRAM_CT_USUARIO,
        "INSTAGRAM_URL": settings.INSTAGRAM_URL,
        "INSTAGRAM_USUARIO": settings.INSTAGRAM_USUARIO,
    }
