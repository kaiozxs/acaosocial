from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache


class UsuarioEmCache(ModelBackend):
    """Guarda o usuário logado por 60 segundos: evita uma ida ao banco a cada clique."""

    def get_user(self, user_id):
        chave = f"usuario_{user_id}"
        usuario = cache.get(chave)
        if usuario is None:
            usuario = super().get_user(user_id)
            if usuario is not None:
                cache.set(chave, usuario, 60)
        return usuario
