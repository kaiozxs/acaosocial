from datetime import date

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
    nome = models.CharField(max_length=80)
    publico = models.CharField("Público", max_length=80, help_text="Ex.: Adultos, Jovens, Adolescentes")
    dias = models.CharField(max_length=80, help_text="Ex.: Seg / Qua / Sex")
    horario = models.CharField("Horário", max_length=40, help_text="Ex.: 19h às 20h30")
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "nome"]

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
    grau = models.PositiveSmallIntegerField(default=0, help_text="0 a 4 listras")
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
    grau = models.PositiveSmallIntegerField(default=0)
    data = models.DateField(default=date.today)
    observacao = models.CharField("Observação", max_length=200, blank=True)

    class Meta:
        ordering = ["-data", "-id"]
        verbose_name = "graduação"
        verbose_name_plural = "graduações"

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
