from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache


class UsuarioEmCache(ModelBackend):
    """Login sem diferenciar maiúscula de minúscula (o celular costuma capitalizar a primeira letra)
    e usuário em cache por 60 segundos: evita uma ida ao banco a cada clique."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None
        usuario = get_user_model().objects.filter(username__iexact=str(username).strip()).first()
        if usuario and usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None

    def get_user(self, user_id):
        chave = f"usuario_{user_id}"
        usuario = cache.get(chave)
        if usuario is None:
            usuario = super().get_user(user_id)
            if usuario is not None:
                cache.set(chave, usuario, 60)
        return usuario
