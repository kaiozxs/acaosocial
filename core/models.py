from datetime import date

from django.core.validators import MaxValueValidator
from django.db import models


class Faixa(models.TextChoices):
    BRANCA = "branca", "Branca"
    CINZA = "cinza", "Cinza (kids)"
    AMARELA = "amarela", "Amarela (kids)"
    LARANJA = "laranja", "Laranja (kids)"
    VERDE = "verde", "Verde (kids)"
    AZUL = "azul", "Azul"
    ROXA = "roxa", "Roxa"
    MARROM = "marrom", "Marrom"
    PRETA = "preta", "Preta"


class Turma(models.Model):
    class Modalidade(models.TextChoices):
        JIU = "jiu-jitsu", "Jiu-jitsu"
        MUAY = "muay-thai", "Muay thai"
        LUTA = "luta-livre", "Luta livre"

    nome = models.CharField(max_length=80, help_text="Ex.: Jiu-jitsu adulto noite")
    modalidade = models.CharField(max_length=12, choices=Modalidade.choices, default=Modalidade.JIU)
    publico = models.CharField("Público", max_length=80, help_text="Ex.: Adultos, Jovens, Adolescentes")
    dias = models.CharField(max_length=80, help_text="Ex.: Seg / Qua / Sex")
    horario = models.CharField("Horário", max_length=40, help_text="Ex.: 19h às 20h30")
    ordem = models.PositiveSmallIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["ordem", "id"]

    def save(self, *args, **kwargs):
        if not self.pk and not self.ordem:
            ultimo = Turma.objects.order_by("-ordem").values_list("ordem", flat=True).first() or 0
            self.ordem = ultimo + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.dias} {self.horario})"


class Aluno(models.Model):
    class Status(models.TextChoices):
        ATIVA = "ativa", "Matrícula ativa"
        TRANCADA = "trancada", "Trancada"
        CANCELADA = "cancelada", "Cancelada"

    nome = models.CharField(max_length=120)
    nascimento = models.DateField("Data de nascimento")
    telefone = models.CharField(max_length=20, blank=True)
    responsavel = models.CharField("Responsável", max_length=120, blank=True, help_text="Obrigatório para menores")
    foto = models.ImageField(upload_to="alunos/", blank=True)
    turma = models.ForeignKey(Turma, null=True, blank=True, on_delete=models.SET_NULL)
    faixa = models.CharField(max_length=10, choices=Faixa.choices, default=Faixa.BRANCA)
    grau = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(4)], help_text="0 a 4 graus")
    inicio = models.DateField("Início dos treinos", default=date.today)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ATIVA)
    observacoes = models.TextField("Observações", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def idade(self):
        hoje = date.today()
        return hoje.year - self.nascimento.year - ((hoje.month, hoje.day) < (self.nascimento.month, self.nascimento.day))

    @property
    def categoria(self):
        i = self.idade
        if i < 13:
            return "Kids"
        if i < 15:
            return "Jovem"
        if i < 18:
            return "Adolescente"
        return "Adulto"


class Graduacao(models.Model):
    """Histórico de trocas de faixa/grau: ajuda o professor a saber quem está perto de graduar."""

    aluno = models.ForeignKey(Aluno, related_name="graduacoes", on_delete=models.CASCADE)
    faixa = models.CharField(max_length=10, choices=Faixa.choices)
    grau = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(4)], help_text="0 a 4 graus")
    data = models.DateField(default=date.today)
    observacao = models.CharField("Observação", max_length=200, blank=True)

    class Meta:
        ordering = ["-data", "-id"]
        verbose_name = "troca de faixa"
        verbose_name_plural = "trocas de faixa"

    def __str__(self):
        return f"{self.aluno} → {self.get_faixa_display()} {self.grau}º grau"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # mantém a faixa atual do aluno sincronizada com a graduação mais recente
        ultima = self.aluno.graduacoes.first()
        if ultima:
            Aluno.objects.filter(pk=self.aluno_id).update(faixa=ultima.faixa, grau=ultima.grau)


class Presenca(models.Model):
    aluno = models.ForeignKey(Aluno, related_name="presencas", on_delete=models.CASCADE)
    data = models.DateField(default=date.today)

    class Meta:
        ordering = ["-data"]
        unique_together = ("aluno", "data")
        verbose_name_plural = "presenças"

    def __str__(self):
        return f"{self.aluno} — {self.data:%d/%m/%Y}"


class Interessado(models.Model):
    """Pessoas que preencheram 'quero treinar' no site público."""

    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20)
    idade = models.PositiveSmallIntegerField(null=True, blank=True)
    mensagem = models.TextField(blank=True)
    contatado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name_plural = "interessados"

    def __str__(self):
        return self.nome


class Doacao(models.Model):
    """Doações recebidas (Pix ou outras) para o controle financeiro do projeto."""

    class Forma(models.TextChoices):
        PIX = "pix", "Pix"
        DINHEIRO = "dinheiro", "Dinheiro"
        OUTRA = "outra", "Outra"

    doador = models.CharField(max_length=120, blank=True, help_text="Deixe em branco se for anônimo")
    valor = models.DecimalField(max_digits=9, decimal_places=2)
    data = models.DateField(default=date.today)
    forma = models.CharField(max_length=10, choices=Forma.choices, default=Forma.PIX)
    observacao = models.CharField("Observação", max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "doação"
        verbose_name_plural = "doações"

    def __str__(self):
        return f"{self.doador or 'Anônimo'} — R$ {self.valor}"


class Assinatura(models.Model):
    """Assinatura do professor usada nos certificados (um único registro)."""

    nome = models.CharField("Nome do professor", max_length=120, default="Melino José")
    titulo = models.CharField("Título abaixo do nome", max_length=160,
                              default="Faixa preta 1º grau de Jiu-Jitsu")
    imagem = models.TextField(blank=True, editable=False)  # PNG transparente em base64

    class Meta:
        verbose_name = "assinatura do professor"
        verbose_name_plural = "assinatura do professor"

    def __str__(self):
        return self.nome


# ---- limpa o cache do painel sempre que algo muda (o painel guarda os números por alguns segundos) ----
from django.core.cache import cache  # noqa: E402
from django.db.models.signals import post_delete, post_save  # noqa: E402


def _limpa_cache(sender, **kwargs):
    cache.clear()


for _m in (Aluno, Interessado, Doacao, Presenca, Graduacao, Turma, Assinatura):
    post_save.connect(_limpa_cache, sender=_m, dispatch_uid=f"limpa_{_m.__name__}_s")
    post_delete.connect(_limpa_cache, sender=_m, dispatch_uid=f"limpa_{_m.__name__}_d")
