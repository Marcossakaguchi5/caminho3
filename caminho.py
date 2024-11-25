import random
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from concurrent.futures import ThreadPoolExecutor
import matplotlib
import os
from matplotlib.animation import PillowWriter

matplotlib.use('TkAgg') 

LABIRINTO_TAMANHO = 10
TEMPERATURA_INICIAL = 100
TAXA_RESFRIAMENTO = 0.99
NUM_PARTICIPANTES = 5

PAREDE = -1
CAMINHO = 0
SAIDA = 2
ITEM = 3
ARMADILHA = 4

def adicionar_caminho_correto(labirinto):
    x, y = 0, 0
    while (x, y) != (LABIRINTO_TAMANHO - 1, LABIRINTO_TAMANHO - 1):
        labirinto[x, y] = CAMINHO
        if x < LABIRINTO_TAMANHO - 1:
            x += 1
        if y < LABIRINTO_TAMANHO - 1:
            y += 1
    labirinto[LABIRINTO_TAMANHO - 1, LABIRINTO_TAMANHO - 1] = SAIDA

def gerar_labirinto(tamanho):
    labirinto = np.random.choice([CAMINHO, PAREDE], size=(tamanho, tamanho), p=[0.7, 0.3])
    labirinto[0, 0] = CAMINHO
    labirinto[tamanho - 1, tamanho - 1] = SAIDA 
    adicionar_caminho_correto(labirinto)
    for _ in range(5):
        x, y = random.randint(0, tamanho - 1), random.randint(0, tamanho - 1)
        labirinto[x, y] = ITEM
    for _ in range(5):
        x, y = random.randint(0, tamanho - 1), random.randint(0, tamanho - 1)
        labirinto[x, y] = ARMADILHA
    return labirinto

def calcular_custo(labirinto, caminho):
    custo = 0
    pontos = 0
    
    for x, y in caminho:
        if labirinto[x, y] == PAREDE:
            custo += 3  # Custo maior para as paredes
        elif labirinto[x, y] == ARMADILHA:
            return float('inf')  # Armadilha mata o agente, custo infinito
        elif labirinto[x, y] == ITEM:
            pontos -= 5  # Itens descontam pontos
        custo += 1  # Cada passo tem custo 1
    
    return custo + pontos  # Retorna o custo total (incluindo itens)



def gerar_caminho(labirinto):
    caminho = [(0, 0)]  # Inicia na entrada
    pos_atual = (0, 0)
    
    while pos_atual != (LABIRINTO_TAMANHO - 1, LABIRINTO_TAMANHO - 1):  # Enquanto não chegar à saída
        x, y = pos_atual
        movimentos = [(x+1, y), (x, y+1), (x-1, y), (x, y-1)]  # Movimentos possíveis (direção: baixo, direita, cima, esquerda)
        movimentos = [(nx, ny) for nx, ny in movimentos if 0 <= nx < LABIRINTO_TAMANHO and 0 <= ny < LABIRINTO_TAMANHO]
        
        # Escolher aleatoriamente o próximo movimento
        pos_atual = random.choice(movimentos)
        caminho.append(pos_atual)
        
    return caminho

def tempera_simulada(labirinto):
    temperatura = TEMPERATURA_INICIAL
    melhor_caminho = gerar_caminho(labirinto)
    melhor_custo = calcular_custo(labirinto, melhor_caminho)
    historico_custos = [melhor_custo]
    
    while temperatura > 1: 
        novo_caminho = gerar_caminho(labirinto)
        novo_custo = calcular_custo(labirinto, novo_caminho)
        
        if novo_custo < melhor_custo or random.uniform(0, 1) < math.exp(-(novo_custo - melhor_custo) / temperatura):
            melhor_caminho = novo_caminho
            melhor_custo = novo_custo
        
        historico_custos.append(melhor_custo)
        temperatura *= TAXA_RESFRIAMENTO 
    
    return melhor_caminho, melhor_custo, historico_custos

def salvar_matriz_com_caminho(labirinto, caminho, nome_arquivo):
    labirinto_copia = labirinto.copy()
    for x, y in caminho:
        labirinto_copia[x, y] =x  
    np.savetxt(nome_arquivo, labirinto_copia, fmt='%d')


def animar_labirintos(labirinto, melhores_caminhos, nome_arquivo):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xticks(np.arange(-0.5, LABIRINTO_TAMANHO, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, LABIRINTO_TAMANHO, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    # Definindo as cores desejadas
    cmap = matplotlib.colors.ListedColormap(["white", "black", "blue", "yellow", "red"])
    bounds = [-1.5, -0.5, 0.5, 2.5, 3.5, 4.5]  
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(labirinto, cmap=cmap, norm=norm)

    participantes_caminhos = [ax.plot([], [], marker='o', markersize=6, label=f'Participante {i+1}')[0]
                              for i in range(len(melhores_caminhos))]
    
    participantes_cabeças = [ax.plot([], [], marker='o', markersize=10, color="blue", label=f'Cabeça {i+1}')[0]
                             for i in range(len(melhores_caminhos))]

    def atualizar_quadro(frame):
        for i, caminho in enumerate(melhores_caminhos):
            if frame < len(caminho):
                x, y = zip(*caminho[:frame+1])
                participantes_caminhos[i].set_data(y, x)
                participantes_cabeças[i].set_data(y[-1], x[-1]) 
        return participantes_caminhos + participantes_cabeças

    total_frames = max(len(caminho) for caminho in melhores_caminhos)
    anim = animation.FuncAnimation(fig, atualizar_quadro, frames=total_frames, interval=200, blit=True)

    # Salvar o GIF
    writer = PillowWriter(fps=5)
    anim.save(nome_arquivo, writer=writer)

def salvar_todos_os_caminhos(labirinto, melhores_caminhos, nome_arquivo):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_xticks(np.arange(-0.5, LABIRINTO_TAMANHO, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, LABIRINTO_TAMANHO, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    # Definindo as cores desejadas
    cmap = matplotlib.colors.ListedColormap(["white", "black", "blue", "yellow", "red"])
    bounds = [-1.5, -0.5, 0.5, 2.5, 3.5, 4.5]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(labirinto, cmap=cmap, norm=norm)

    # Desenhar os caminhos sobrepostos
    participantes_caminhos = [ax.plot([], [], marker='o', markersize=6, label=f'Participante {i+1}')[0]
                              for i in range(len(melhores_caminhos))]
    
    def atualizar_quadro(frame):
        for i, caminho in enumerate(melhores_caminhos):
            if frame < len(caminho):
                x, y = zip(*caminho[:frame+1])
                participantes_caminhos[i].set_data(y, x)
        return participantes_caminhos

    total_frames = max(len(caminho) for caminho in melhores_caminhos)
    anim = animation.FuncAnimation(fig, atualizar_quadro, frames=total_frames, interval=200, blit=True)

    writer = PillowWriter(fps=5)
    anim.save(nome_arquivo, writer=writer)






labirinto = gerar_labirinto(LABIRINTO_TAMANHO)

# Processar caminhos com multithreading
with ThreadPoolExecutor() as executor:
    resultados = list(executor.map(lambda _: tempera_simulada(labirinto), range(NUM_PARTICIPANTES)))

# Ordenar resultados e exibir melhores caminhos
resultados.sort(key=lambda x: x[1])  
melhores_caminhos = [r[0] for r in resultados]

# Salvar as matrizes dos melhores caminhos
if not os.path.exists("matrix"):
    os.makedirs("matrix")

for i, caminho in enumerate(melhores_caminhos):
    nome_arquivo = f"matrix/caminho_participante_{i+1}.txt"
    salvar_matriz_com_caminho(labirinto, caminho, nome_arquivo)
    print(f"Labirinto com caminho do participante {i+1} salvo em: {nome_arquivo}")

# Salvar a animação de cada participante individualmente
for i, caminho in enumerate(melhores_caminhos):
    nome_arquivo_gif = f"matrix/caminho_participante_{i+1}.gif"
    animar_labirintos(labirinto, [caminho], nome_arquivo_gif)
    print(f"GIF do caminho do participante {i+1} salvo em: {nome_arquivo_gif}")

# Salvar a junção de todos os caminhos sobrepostos
salvar_todos_os_caminhos(labirinto, melhores_caminhos, "todos_os_caminhos_sobrepostos.gif")
print("GIF com todos os caminhos sobrepostos salvo em: todos_os_caminhos_sobrepostos.gif")

# Exibir os custos
for i, (_, custo, historico) in enumerate(resultados):
    print(f"Participante {i+1}: Custo = {custo}")
