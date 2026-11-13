from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

LIMITE_USUARIO = 5      # erros seguidos para o mesmo usuário vindo do mesmo IP
LIMITE_IP = 20          # erros seguidos vindos do mesmo IP (qualquer usuário)
BLOQUEIO_MINUTOS = 15


def _ip(request):
    if request is None:
        return "?"
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (xff.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "?"))[:60]


def _chaves(username, ip):
    return [(f"u|{username.lower()[:80]}|{ip}", LIMITE_USUARIO), (f"ip|{ip}", LIMITE_IP)]


def _bloqueado(chaves):
    from core.models import TentativaLogin
    agora = timezone.now()
    return TentativaLogin.objects.filter(chave__in=[c for c, _ in chaves], bloqueado_ate__gt=agora).exists()


def _registrar_falha(chaves):
    from core.models import TentativaLogin
    agora = timezone.now()
    for chave, limite in chaves:
        t, _ = TentativaLogin.objects.get_or_create(chave=chave)
        if t.bloqueado_ate and t.bloqueado_ate <= agora:
            t.falhas, t.bloqueado_ate = 0, None  # o bloqueio passou: começa de novo
        t.falhas += 1
        if t.falhas >= limite:
            t.bloqueado_ate = agora + timedelta(minutes=BLOQUEIO_MINUTOS)
        t.save()


def _limpar(username, ip):
    from core.models import TentativaLogin
    TentativaLogin.objects.filter(chave=_chaves(username, ip)[0][0]).delete()


class UsuarioEmCache(ModelBackend):
    """Login sem diferenciar maiúscula de minúscula (o celular costuma capitalizar a primeira letra)
    e usuário em cache por 60 segundos: evita uma ida ao banco a cada clique."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if username is None or password is None:
            return None
        username = str(username).strip()
        ip = _ip(request)
        chaves = _chaves(username, ip)
        try:
            if _bloqueado(chaves):
                return None  # muitos erros seguidos: nem confere a senha
        except Exception:
            pass  # se o controle falhar, o login continua funcionando
        usuario = get_user_model().objects.filter(username__iexact=username).first()
        if usuario is None:
            get_user_model()().set_password(password)  # gasta o mesmo tempo, para não revelar quais usuários existem
        elif usuario.check_password(password) and self.user_can_authenticate(usuario):
            try:
                _limpar(username, ip)
            except Exception:
                pass
            return usuario
        try:
            _registrar_falha(chaves)
        except Exception:
            pass
        return None

    def get_user(self, user_id):
        chave = f"usuario_{user_id}"
        usuario = cache.get(chave)
        if usuario is None:
            usuario = super().get_user(user_id)
            if usuario is not None:
                cache.set(chave, usuario, 60)
        return usuario
