# %% [markdown]
# # CP2 - Sistema de Batalha RPG com POO
#
# | Integrante | RM |
# |---|---|
# | Arthur Zeferino | 570858 |
# | Israel Carneiro de Toledo | 573854 |
# | Giovanni Henrique Pereira Hessel | 570574 |
# | Suellen Pereira da Silva | 573862 |
#
# Execute as células de cima para baixo (Runtime > Run all). Usa apenas a biblioteca padrão do Python.

# %%
import random
import time
from abc import ABC, abstractmethod

PAUSA = 0.4            # segundos entre ações (0 = instantâneo)
VARIACAO_DANO = 0.10   # todo dano varia +-10%
MAX_RODADAS = 100      # evita batalhas infinitas
SEMENTE = None         # número fixo (ex: 42) repete a mesma batalha

if SEMENTE is not None:
    random.seed(SEMENTE)


def pausar(segundos=None):
    segundos = PAUSA if segundos is None else segundos
    if segundos > 0:
        time.sleep(segundos)


def barra(atual, maximo, tamanho=10):
    """Barra de vida/mana, ex: ██████░░░░"""
    cheio = round(tamanho * atual / maximo) if maximo else 0
    if atual > 0:
        cheio = max(1, cheio)  # vivo nunca mostra barra vazia
    return "█" * cheio + "░" * (tamanho - cheio)


# %% [markdown]
# ## 1. Classes base

# %%
class Combatente(ABC):
    """Base comum a heróis e monstros: atributos obrigatórios e regras gerais
    (dano, defesa, veneno, regeneração de MP)."""

    CHANCE_CRITICO = 0.05
    MULT_CRITICO = 1.5
    REGEN_MP = 2  # MP recuperado no início de cada turno

    def __init__(self, nome, hp, mp, speed, atk, matk, defense, mdefense):
        self.nome = nome
        self.hp = hp
        self.max_hp = hp
        self.mp = mp
        self.max_mp = mp
        self.speed = speed
        self.atk = atk              # ataque físico
        self.matk = matk            # ataque mágico
        self.defense = defense      # defesa física
        self.mdefense = mdefense    # defesa mágica
        self.defendendo = False     # True = recebe metade do dano
        self.veneno_turnos = 0

    def esta_vivo(self):
        return self.hp > 0

    def resetar(self):
        """Restaura HP, MP e status para reaproveitar o objeto em outra batalha."""
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.defendendo = False
        self.veneno_turnos = 0

    def receber_dano(self, dano):
        """Aplica o dano (mínimo 1, para a batalha sempre terminar)."""
        dano = max(1, int(dano))
        if self.defendendo:
            dano = max(1, dano // 2)
        self.hp = max(0, self.hp - dano)
        return dano

    def _golpear(self, alvo, dano_bruto, descricao):
        """Dano = (ataque - defesa) com variação aleatória e chance de crítico."""
        dano = max(1, dano_bruto)
        dano *= random.uniform(1 - VARIACAO_DANO, 1 + VARIACAO_DANO)
        if random.random() < self.CHANCE_CRITICO:
            print("   *** ACERTO CRÍTICO! ***")
            dano *= self.MULT_CRITICO
        defendia = alvo.defendendo
        causado = alvo.receber_dano(dano)
        extra = " (amortecido pela defesa)" if defendia else ""
        print(f"   -> {causado} de dano {descricao}{extra}! "
              f"(HP de {alvo.nome}: {alvo.hp}/{alvo.max_hp})")
        return causado

    def defender(self):
        """Dano pela metade até o próximo turno e +5 MP."""
        self.defendendo = True
        self.mp = min(self.max_mp, self.mp + 5)
        print(f"🛡️  {self.nome} assume postura defensiva (dano pela metade e +5 MP).")

    def iniciar_turno(self):
        """Remove a defesa, regenera MP e aplica veneno (5% do HP máximo).
        Retorna False se o combatente morreu por veneno."""
        self.defendendo = False
        self.mp = min(self.max_mp, self.mp + self.REGEN_MP)
        if self.veneno_turnos > 0:
            dano = max(1, self.max_hp // 20)
            self.hp = max(0, self.hp - dano)
            self.veneno_turnos -= 1
            print(f"   ☠ {self.nome} sofre {dano} de veneno! (HP: {self.hp}/{self.max_hp})")
            if not self.esta_vivo():
                print(f"   ☠️  {self.nome} sucumbiu ao veneno!")
        return self.esta_vivo()

    @abstractmethod
    def atacar(self, alvo):
        """Cada classe filha implementa seu ataque (polimorfismo)."""

    def __str__(self):
        return f"{self.nome} [HP {self.hp}/{self.max_hp} | MP {self.mp}/{self.max_mp}]"

    def linha_status(self):
        marcas = ""
        if not self.esta_vivo():
            marcas = " ✝"
        else:
            if self.defendendo:
                marcas += " 🛡️"
            if self.veneno_turnos > 0:
                marcas += f" ☠({self.veneno_turnos})"
        return (f"{self.nome:<20} HP [{barra(self.hp, self.max_hp)}] "
                f"{self.hp:>3}/{self.max_hp:<3} | MP {self.mp:>3}/{self.max_mp:<3} "
                f"| SPD {self.speed:>2}{marcas}")


class Personagem(Combatente):
    """Classe pai dos heróis. Define ataque e habilidade padrão."""

    NOME_HABILIDADE = "Golpe Focado"
    CUSTO_HABILIDADE = 10
    AOE = False  # True = a habilidade atinge todos os inimigos

    def atacar(self, alvo):
        print(f"{self.nome} realiza um ataque físico básico em {alvo.nome}!")
        self._golpear(alvo, self.atk - alvo.defense, "físico")

    def pode_usar_habilidade(self):
        return self.mp >= self.CUSTO_HABILIDADE

    def habilidade_especial(self, alvo, inimigos):
        self.mp -= self.CUSTO_HABILIDADE
        print(f"{self.nome} usa '{self.NOME_HABILIDADE}' em {alvo.nome}!")
        self._golpear(alvo, int(self.atk * 1.5) - alvo.defense, "físico")


class Monstro(Combatente):
    """Classe pai dos inimigos. A IA usa o ataque (físico ou mágico) que causa mais dano."""

    CUSTO_MAGIA = 10

    def __init__(self, nome, hp, mp, speed, atk, matk, defense, mdefense, regen_hp=0):
        super().__init__(nome, hp, mp, speed, atk, matk, defense, mdefense)
        self.regen_hp = regen_hp  # vida regenerada por turno

    def iniciar_turno(self):
        vivo = super().iniciar_turno()
        if vivo and self.regen_hp > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen_hp)
            print(f"   ✚ {self.nome} regenera {self.regen_hp} de HP.")
        return vivo

    def atacar(self, alvo):
        dano_fisico = self.atk - alvo.defense
        dano_magico = self.matk - alvo.mdefense

        if self.mp >= self.CUSTO_MAGIA and dano_magico > dano_fisico:
            self.mp -= self.CUSTO_MAGIA
            print(f"{self.nome} conjura uma habilidade sombria em {alvo.nome}!")
            self._golpear(alvo, dano_magico, "mágico")
        else:
            print(f"{self.nome} morde/ataca fisicamente {alvo.nome}!")
            self._golpear(alvo, dano_fisico, "físico")

    def escolher_alvo(self, herois):
        """50% foca o herói com menos HP, 50% escolhe aleatoriamente."""
        vivos = [h for h in herois if h.esta_vivo()]
        if random.random() < 0.5:
            return min(vivos, key=lambda h: h.hp)
        return random.choice(vivos)

    def agir(self, herois):
        """Com menos de 25% de HP, tem 30% de chance de se defender."""
        if self.hp < self.max_hp * 0.25 and random.random() < 0.3:
            self.defender()
        else:
            self.atacar(self.escolher_alvo(herois))


# %% [markdown]
# ## 2. Classes jogáveis

# %%
class Guerreiro(Personagem):
    """Alto HP e defesa. Ataque mais forte com HP abaixo de 30% (fúria)."""

    NOME_HABILIDADE = "Investida Brutal"
    CUSTO_HABILIDADE = 10

    def __init__(self, nome):
        super().__init__(nome, hp=150, mp=20, speed=10,
                         atk=25, matk=5, defense=15, mdefense=8)

    def atacar(self, alvo):
        furia = self.hp <= self.max_hp * 0.3
        mult = 1.5 if furia else 1.3
        titulo = "entra em FÚRIA e usa" if furia else "usa"
        print(f"[{self.nome} - Guerreiro] {titulo} 'Golpe Demolidor' em {alvo.nome}!")
        self._golpear(alvo, int(self.atk * mult) - alvo.defense, "físico devastador")

    def habilidade_especial(self, alvo, inimigos):
        self.mp -= self.CUSTO_HABILIDADE
        print(f"[{self.nome} - Guerreiro] avança com '{self.NOME_HABILIDADE}' em {alvo.nome}!")
        self._golpear(alvo, int(self.atk * 1.8) - alvo.defense, "físico brutal")
        recuo = max(1, self.max_hp // 20)
        self.hp = max(1, self.hp - recuo)  # o recuo nunca mata
        print(f"   (recuo: {self.nome} perde {recuo} de HP)")


class Mago(Personagem):
    """Pouco HP e defesa física; muito MP e dano mágico. Habilidade em área."""

    NOME_HABILIDADE = "Chuva de Meteoros"
    CUSTO_HABILIDADE = 40
    AOE = True
    CUSTO_BOLA_DE_FOGO = 15

    def __init__(self, nome):
        super().__init__(nome, hp=80, mp=100, speed=12,
                         atk=8, matk=35, defense=6, mdefense=20)

    def atacar(self, alvo):
        if self.mp >= self.CUSTO_BOLA_DE_FOGO:
            self.mp -= self.CUSTO_BOLA_DE_FOGO
            print(f"[{self.nome} - Mago] conjura 'Bola de Fogo' em {alvo.nome}! (MP: {self.mp})")
            self._golpear(alvo, self.matk - alvo.mdefense, "mágico de fogo")
        else:
            # Sem mana: golpe fraco de cajado, mas recupera um pouco de MP
            self.mp = min(self.max_mp, self.mp + 5)
            print(f"[{self.nome} - Mago] sem mana, golpeia com o cajado e se concentra (+5 MP)!")
            self._golpear(alvo, self.atk - alvo.defense, "físico")

    def habilidade_especial(self, alvo, inimigos):
        self.mp -= self.CUSTO_HABILIDADE
        print(f"[{self.nome} - Mago] invoca '{self.NOME_HABILIDADE}' sobre todos os inimigos!")
        for inimigo in inimigos:
            if inimigo.esta_vivo():
                self._golpear(inimigo, int(self.matk * 0.7) - inimigo.mdefense, "mágico em área")


class Arqueiro(Personagem):
    """Muito rápido, ignora 30% da defesa do alvo e tem 25% de chance de crítico."""

    NOME_HABILIDADE = "Flecha Envenenada"
    CUSTO_HABILIDADE = 15
    CHANCE_CRITICO = 0.25

    def __init__(self, nome):
        super().__init__(nome, hp=110, mp=40, speed=18,
                         atk=20, matk=10, defense=10, mdefense=10)

    def atacar(self, alvo):
        print(f"[{self.nome} - Arqueiro] dispara um 'Tiro Certeiro' em {alvo.nome}!")
        defesa_reduzida = int(alvo.defense * 0.7)
        self._golpear(alvo, self.atk - defesa_reduzida, "perfurante")

    def habilidade_especial(self, alvo, inimigos):
        self.mp -= self.CUSTO_HABILIDADE
        print(f"[{self.nome} - Arqueiro] atira uma '{self.NOME_HABILIDADE}' em {alvo.nome}!")
        self._golpear(alvo, self.atk - int(alvo.defense * 0.7), "perfurante")
        if alvo.esta_vivo():
            alvo.veneno_turnos = 3
            print(f"   ☠ {alvo.nome} foi envenenado por 3 turnos!")


# %% [markdown]
# ## 3. Ações, IA e controle manual

# %%
def ler_inteiro(mensagem, minimo, maximo, padrao):
    """Lê uma opção com validação. Enter vazio (ou sem teclado) usa o padrão."""
    while True:
        try:
            texto = input(mensagem).strip()
        except EOFError:
            return padrao
        if texto == "":
            return padrao
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        print("Opção inválida, tente novamente.")


def escolher_alvo_manual(inimigos):
    vivos = [i for i in inimigos if i.esta_vivo()]
    if len(vivos) == 1:
        return vivos[0]
    print("Escolha o alvo:")
    for n, inimigo in enumerate(vivos, 1):
        print(f"  {n}) {inimigo}")
    return vivos[ler_inteiro("Alvo: ", 1, len(vivos), 1) - 1]


def escolher_acao_manual(heroi, inimigos):
    """Menu do jogador. Retorna (acao, alvo)."""
    print(f"\n>>> Vez de {heroi}")
    print("  1) Atacar")
    aviso = "" if heroi.pode_usar_habilidade() else "  [MP insuficiente]"
    print(f"  2) {heroi.NOME_HABILIDADE} (custa {heroi.CUSTO_HABILIDADE} MP){aviso}")
    print("  3) Defender")
    while True:
        opcao = ler_inteiro("Ação: ", 1, 3, 1)
        if opcao == 2 and not heroi.pode_usar_habilidade():
            print("MP insuficiente!")
            continue
        break
    if opcao == 3:
        return "defender", None
    if opcao == 2 and heroi.AOE:
        return "habilidade", next(i for i in inimigos if i.esta_vivo())
    return ("habilidade" if opcao == 2 else "atacar"), escolher_alvo_manual(inimigos)


def escolher_acao_auto(heroi, inimigos):
    """IA dos heróis: foca o inimigo mais fraco, usa área só contra 2+ alvos
    e se defende às vezes quando o HP está abaixo de 25%."""
    vivos = [i for i in inimigos if i.esta_vivo()]
    alvo = min(vivos, key=lambda m: m.hp)

    if heroi.hp < heroi.max_hp * 0.25 and random.random() < 0.4:
        return "defender", None
    if heroi.pode_usar_habilidade():
        if heroi.AOE and len(vivos) >= 2:
            return "habilidade", alvo
        if not heroi.AOE and random.random() < 0.5:
            return "habilidade", alvo
    return "atacar", alvo


def executar_acao(heroi, acao, alvo, inimigos):
    if acao == "defender":
        heroi.defender()
    elif acao == "habilidade":
        heroi.habilidade_especial(alvo, inimigos)
    else:
        heroi.atacar(alvo)


def anunciar_mortes(antes):
    for combatente in antes:
        if not combatente.esta_vivo():
            print(f"   ☠️  {combatente.nome} foi derrotado!")


def mostrar_status(herois, monstros):
    print("Heróis:")
    for h in herois:
        print("  " + h.linha_status())
    print("Monstros:")
    for m in monstros:
        print("  " + m.linha_status())
    print()


def executar_rodada(herois, monstros, manual=False):
    """Todos os vivos agem em ordem decrescente de speed.
    Empate: heróis primeiro; persistindo, desempate aleatório."""
    fila = sorted(
        (c for c in herois + monstros if c.esta_vivo()),
        key=lambda c: (c.speed, isinstance(c, Personagem), random.random()),
        reverse=True,
    )
    for ator in fila:
        if not ator.esta_vivo():
            continue  # morreu antes de agir nesta rodada
        eh_heroi = ator in herois
        inimigos = monstros if eh_heroi else herois
        if not any(i.esta_vivo() for i in inimigos):
            break
        if not ator.iniciar_turno():
            continue  # morreu de veneno

        vivos_antes = [i for i in inimigos if i.esta_vivo()]
        if eh_heroi:
            if manual:
                acao, alvo = escolher_acao_manual(ator, inimigos)
            else:
                acao, alvo = escolher_acao_auto(ator, inimigos)
            executar_acao(ator, acao, alvo, inimigos)
        else:
            ator.agir(herois)
        anunciar_mortes(vivos_antes)
        pausar()


# %% [markdown]
# ## 4. Batalhas 1v1 e 3v3

# %%
def batalha_1v1(heroi, monstro, manual=False):
    """Combate por turnos entre um herói e um monstro. A speed decide quem
    começa (empate: o herói). Retorna o vencedor."""
    print("\n" + "=" * 60)
    print(f"  BATALHA 1v1: {heroi.nome} vs {monstro.nome}")
    print("=" * 60)

    primeiro = heroi if heroi.speed >= monstro.speed else monstro
    segundo = monstro if primeiro is heroi else heroi
    print(f"{primeiro.nome} (SPD {primeiro.speed}) age antes de "
          f"{segundo.nome} (SPD {segundo.speed})!")

    rodada = 1
    while heroi.esta_vivo() and monstro.esta_vivo() and rodada <= MAX_RODADAS:
        print(f"\n--- Turno {rodada} ---")
        mostrar_status([heroi], [monstro])
        executar_rodada([heroi], [monstro], manual)
        rodada += 1

    vencedor = heroi if heroi.esta_vivo() else monstro
    print("\n" + "=" * 60)
    print(f"🏆 FIM DE BATALHA! Vencedor: {vencedor.nome} (HP {vencedor.hp}/{vencedor.max_hp})")
    print("=" * 60 + "\n")
    return vencedor


def batalha_3v3(herois, monstros, manual=False):
    """Combate em equipe. Termina quando todos de um time têm hp <= 0.
    Retorna 'herois', 'monstros' ou 'empate' (se atingir MAX_RODADAS)."""
    print("\n" + "=" * 60)
    print("                BATALHA EM EQUIPE 3v3")
    print("=" * 60)

    rodada = 1
    while (any(h.esta_vivo() for h in herois)
           and any(m.esta_vivo() for m in monstros)
           and rodada <= MAX_RODADAS):
        print(f"\n--- RODADA {rodada} ---")
        mostrar_status(herois, monstros)
        executar_rodada(herois, monstros, manual)
        rodada += 1

    herois_vivos = any(h.esta_vivo() for h in herois)
    monstros_vivos = any(m.esta_vivo() for m in monstros)
    print("\n" + "=" * 60)
    if herois_vivos and not monstros_vivos:
        resultado = "herois"
        print("🏆 VITÓRIA DOS HERÓIS! A equipe de monstros foi dizimada.")
    elif monstros_vivos and not herois_vivos:
        resultado = "monstros"
        print("☠️  DERROTA! Os monstros venceram os defensores.")
    else:
        resultado = "empate"
        print("⚖️  EMPATE! A batalha excedeu o limite de rodadas.")
    print("=" * 60 + "\n")
    return resultado


# %% [markdown]
# ## 5. Execução
# Com `MODO_MANUAL = True`, um menu pede a ação e o alvo de cada herói.

# %%
MODO_MANUAL = False

if __name__ == "__main__":
    guerreiro = Guerreiro("Kael")
    mago = Mago("Lyra")
    arqueiro = Arqueiro("Thorne")

    orc = Monstro("Grumak, o Orc", hp=150, mp=10, speed=9,
                  atk=27, matk=0, defense=12, mdefense=5)
    goblin = Monstro("Zilch, Goblin Xamã", hp=90, mp=40, speed=13,
                     atk=12, matk=27, defense=5, mdefense=15)
    troll = Monstro("Brutus, o Troll", hp=240, mp=0, speed=5,
                    atk=32, matk=0, defense=10, mdefense=4, regen_hp=6)

    herois = [guerreiro, mago, arqueiro]
    monstros = [orc, goblin, troll]

    batalha_1v1(guerreiro, orc, manual=MODO_MANUAL)

    for combatente in herois + monstros:
        combatente.resetar()

    pausar(1)
    batalha_3v3(herois, monstros, manual=MODO_MANUAL)
