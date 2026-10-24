
import pygame
import random
import sys
import math

pygame.init()

# Configurações da tela
LARGURA = 800
ALTURA = 600
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Flappy Mouse")

relogio = pygame.time.Clock()

# Cores
AZUL = (95, 190, 255)
BRANCO = (255, 255, 255)
AMARELO = (255, 220, 50)
LARANJA = (255, 150, 30)
VERDE = (35, 180, 75)
VERDE_ESCURO = (20, 130, 50)
PRETO = (30, 30, 30)
VERMELHO = (240, 60, 60)

fonte = pygame.font.SysFont("Arial", 36, bold=True)
fonte_menor = pygame.font.SysFont("Arial", 22)

# Passarinho
passaro_x = 150.0
passaro_y = ALTURA / 2
raio = 16
velocidade_seguimento = 0.12

# Barreiras
LARGURA_BARREIRA = 80
ESPACO = 190
VELOCIDADE = 4

barreiras = []
pontuacao = 0
recorde = 0
game_over = False

def criar_barreira(x):
    margem = 70
    topo = random.randint(margem, ALTURA - ESPACO - margem)

    return {
        "x": float(x),
        "topo": topo,
        "passou": False
    }

def reiniciar():
    global passaro_x, passaro_y
    global barreiras, pontuacao, game_over

    passaro_x = 150.0
    passaro_y = ALTURA / 2
    barreiras = [criar_barreira(500), criar_barreira(900)]
    pontuacao = 0
    game_over = False

reiniciar()

# Loop principal
while True:
    relogio.tick(60)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Reiniciar usando somente o mouse
        if evento.type == pygame.MOUSEBUTTONDOWN and game_over:
            reiniciar()

    # Atualização do jogo
    if not game_over:
        # O pássaro segue o ponteiro suavemente
        mouse_x, mouse_y = pygame.mouse.get_pos()

        passaro_x += (mouse_x - passaro_x) * velocidade_seguimento
        passaro_y += (mouse_y - passaro_y) * velocidade_seguimento

        # Limitar o pássaro dentro da tela
        passaro_x = max(raio, min(LARGURA - raio, passaro_x))
        passaro_y = max(raio, min(ALTURA - raio, passaro_y))

        # Mover as barreiras
        for barreira in barreiras:
            barreira["x"] -= VELOCIDADE

            if (
                not barreira["passou"]
                and barreira["x"] + LARGURA_BARREIRA < passaro_x
            ):
                pontuacao += 1
                barreira["passou"] = True

        # Criar barreiras novas
        if barreiras[-1]["x"] < LARGURA - 300:
            barreiras.append(
                criar_barreira(barreiras[-1]["x"] + 400)
            )

        # Remover barreiras que saíram da tela
        barreiras = [
            b for b in barreiras
            if b["x"] + LARGURA_BARREIRA > 0
        ]

        # Colisão com as barreiras
        passaro = pygame.Rect(
            int(passaro_x - raio),
            int(passaro_y - raio),
            raio * 2,
            raio * 2
        )

        for barreira in barreiras:
            x = int(barreira["x"])
            topo = barreira["topo"]
            base = topo + ESPACO

            parte_superior = pygame.Rect(
                x, 0, LARGURA_BARREIRA, topo
            )

            parte_inferior = pygame.Rect(
                x, base, LARGURA_BARREIRA, ALTURA - base
            )

            if (
                passaro.colliderect(parte_superior)
                or passaro.colliderect(parte_inferior)
            ):
                game_over = True
                recorde = max(recorde, pontuacao)

        # Verificar os limites da tela
        if (
            passaro_x - raio <= 0
            or passaro_x + raio >= LARGURA
            or passaro_y - raio <= 0
            or passaro_y + raio >= ALTURA
        ):
            game_over = True
            recorde = max(recorde, pontuacao)

    # Desenhar o cenário
    TELA.fill(AZUL)

    # Nuvens decorativas
    pygame.draw.circle(TELA, BRANCO, (120, 90), 22)
    pygame.draw.circle(TELA, BRANCO, (145, 80), 28)
    pygame.draw.circle(TELA, BRANCO, (170, 92), 20)

    pygame.draw.circle(TELA, BRANCO, (570, 150), 20)
    pygame.draw.circle(TELA, BRANCO, (595, 138), 27)
    pygame.draw.circle(TELA, BRANCO, (620, 151), 19)

    # Desenhar barreiras
    for barreira in barreiras:
        x = int(barreira["x"])
        topo = barreira["topo"]
        base = topo + ESPACO

        # Parte superior
        pygame.draw.rect(
            TELA, VERDE,
            (x, 0, LARGURA_BARREIRA, topo)
        )
        pygame.draw.rect(
            TELA, VERDE_ESCURO,
            (x - 5, topo - 20, LARGURA_BARREIRA + 10, 20)
        )

        # Parte inferior
        pygame.draw.rect(
            TELA, VERDE,
            (x, base, LARGURA_BARREIRA, ALTURA - base)
        )
        pygame.draw.rect(
            TELA, VERDE_ESCURO,
            (x - 5, base, LARGURA_BARREIRA + 10, 20)
        )

    # Desenhar o pássaro
    px = int(passaro_x)
    py = int(passaro_y)

    pygame.draw.circle(TELA, LARANJA, (px, py + 3), raio)
    pygame.draw.circle(TELA, AMARELO, (px, py), raio)

    # Asa
    pygame.draw.ellipse(
        TELA, LARANJA,
        (px - 12, py - 3, 15, 11)
    )

    # Olho
    pygame.draw.circle(TELA, BRANCO, (px + 6, py - 6), 6)
    pygame.draw.circle(TELA, PRETO, (px + 8, py - 6), 3)

    # Bico
    pygame.draw.polygon(
        TELA, LARANJA,
        [(px + 13, py), (px + 24, py + 4), (px + 13, py + 7)]
    )

    # Pontuação
    texto = fonte.render(str(pontuacao), True, BRANCO)
    TELA.blit(
        texto,
        (LARGURA // 2 - texto.get_width() // 2, 25)
    )

    # Tela de derrota
    if game_over:
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        TELA.blit(overlay, (0, 0))

        titulo = fonte.render("GAME OVER", True, BRANCO)
        pontos = fonte_menor.render(
            f"Pontuação: {pontuacao}   Recorde: {recorde}",
            True, BRANCO
        )
        dica = fonte_menor.render(
            "Clique com o mouse para jogar novamente",
            True, BRANCO
        )

        TELA.blit(
            titulo,
            (LARGURA // 2 - titulo.get_width() // 2, 230)
        )
        TELA.blit(
            pontos,
            (LARGURA // 2 - pontos.get_width() // 2, 285)
        )
        TELA.blit(
            dica,
            (LARGURA // 2 - dica.get_width() // 2, 335)
        )

    pygame.display.flip()
    
