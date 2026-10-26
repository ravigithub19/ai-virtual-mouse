# 🚀 Guia Completo: Como Rodar o AI Virtual Mouse

Este guia detalha o passo a passo para configurar o ambiente, instalar as dependências corretas e executar qualquer uma das três versões do mouse virtual com inteligência artificial e visão computacional.

---
##
## 📋 Sumário
1. [Visão Geral dos Scripts](#-visão-geral-dos-scripts)
2. [Requisitos Importantes (Atenção ao Python)](#-requisitos-importantes)
3. [Passo a Passo de Instalação no Windows](#-passo-a-passo-de-instalação-no-windows)
4. [Como Inicializar o Sistema](#-como-inicializar-o-sistema)
5. [Guia de Gestos e Controles](#-guia-de-gestos-e-controles)
6. [Resolução de Problemas Frequentes (FAQ)](#-resolução-de-problemas-frequentes)

---

## 🎮 Visão Geral dos Scripts

O projeto conta com 3 versões diferentes, da mais simples até a mais avançada:

| Arquivo | Descrição | Biblioteca de Mouse |
| :--- | :--- | :--- |
| **`ironman_touchless_pro.py`** | **Interface Jarvis / Homem de Ferro**: HUD holográfico de reator Arc, gestos com a palma para alternar áreas de trabalho do Windows (`Win+Tab`, `Win+D`, etc.), zoom estendido com duas mãos e filtro anti-tremor One Euro. | `pyautogui` |
| **`mac_touchless_pro.py`** | **Modo MacBook / Apple Vision Pro**: Focado em produtividade diária, com trava magnética pré-clique (evita que o cursor deslize ao bater os dedos), rolagem natural com dois dedos e filtro de suavização de tremor. | `pyautogui` |
| **`AIVirtualMouse.py`** | **Versão Básica / Didática**: Script clássico simples para mover o cursor com o dedo indicador e clicar levantando o dedo médio. | `autopy` |

---

## ⚠️ Requisitos Importantes

### 1. Versão do Python: **3.10 ou 3.11 (Obrigatório)**
> [!IMPORTANT]
> **Não utilize o Python 3.13!** 
> A Google descontinuou a API `mediapipe.solutions` a partir da versão `0.10.30`. Como o Python 3.13 só possui pacotes do MediaPipe lançados a partir da versão `0.10.30`, tentar rodar o código com Python 3.13 causará o erro:  
> `AttributeError: module 'mediapipe' has no attribute 'solutions'`.  
> Por isso, **utilize o Python 3.11 ou 3.10**.

### 2. Hardware
* **Webcam** (integrada no notebook ou conectada via USB).

---

## 🛠️ Passo a Passo de Instalação no Windows

### 1. Instalar o Python 3.11 (se ainda não tiver)
Se você possui apenas o Python 3.13 ou não tem o Python instalado, instale o Python 3.11 pelo terminal:

```powershell
winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
```
*(Ou baixe pelo site oficial: [python.org/downloads/release/python-3119/](https://www.python.org/downloads/release/python-3119/)).*

---

### 2. Abrir o Terminal na Pasta do Projeto
Abra o **PowerShell** ou **Prompt de Comando** dentro do diretório do projeto:
```powershell
cd "C:\Users\Aluno 02\Desktop\ai-virtual-mouse"
```

---

### 3. Criar e Ativar um Ambiente Virtual (venv)
Criar um ambiente virtual isolado garante que as versões corretas das bibliotecas sejam utilizadas sem conflitos:

```powershell
# 1. Cria a venv usando o Python 3.11
py -3.11 -m venv venv

# 2. Ativa o ambiente virtual
.\venv\Scripts\Activate.ps1
```

> [!TIP]
> **Aviso de segurança no PowerShell?**  
> Se o PowerShell exibir o erro `PSSecurityException` ou informar que *a execução de scripts foi desabilitada neste sistema*, execute o comando abaixo e tente ativar novamente:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\venv\Scripts\Activate.ps1
> ```
> Quando a venv estiver ativa, você verá `(venv)` no início da linha de comando.

---

### 4. Instalar as Dependências

Com o `(venv)` ativo, instale as bibliotecas necessárias:

```powershell
pip install opencv-python mediapipe==0.10.14 pyautogui numpy
```

*(Opcional: Caso deseje rodar a versão básica `AIVirtualMouse.py`, instale também `pip install autopy`).*

---

## 🚀 Como Inicializar o Sistema

Certifique-se de que sua webcam está livre (não sendo usada pelo Teams, Zoom, Meet, etc.) e execute uma das opções:

### Opção 1: Versão Jarvis / Homem de Ferro (Mais Completa)
```powershell
python ironman_touchless_pro.py
```

### Opção 2: Versão MacBook Touchless Pro (Produtividade Limpa)
```powershell
python mac_touchless_pro.py
```

### Opção 3: Versão Clássica Básica
```powershell
python AIVirtualMouse.py
```

---

## 🖐️ Guia de Gestos e Controles

### 🔒 Segurança Biométrica (Opcional): Liberação por Pulseira Preta
> [!NOTE]
> **Por padrão, a obrigatoriedade da pulseira está DESATIVADA (`REQUIRE_WRISTBAND = False`), permitindo controle livre com qualquer mão.**
> - Caso queira reativar a restrição biométrica, basta alterar a variável `REQUIRE_WRISTBAND = True` no topo de `ironman_touchless_pro.py` ou `mac_touchless_pro.py`.
> - **Quando ativada (`REQUIRE_WRISTBAND = True`)**:
>   - O sistema escaneia em tempo real a região do pulso em busca de uma **pulseira, bracelete ou fita preta** (relógio, fita ou silicone).
>   - **Mão com pulseira**: Exibe o badge verde `LIBERADA [OK XX%]` e autoriza o controle do mouse e gestos.
>   - **Mão sem pulseira**: Exibe o aviso `ACESSO NEGADO: USE A PULSEIRA PRETA`.

### 🖱️ Versão Pro (`mac_touchless_pro.py` e `ironman_touchless_pro.py`):
* **Mover o Cursor**: Levante o dedo indicador e aponte para onde deseja mover. O sistema utiliza estabilização One Euro para eliminar qualquer tremor da mão.
* **Trava Magnética Pré-Clique**: Ao aproximar o polegar do indicador para clicar, o cursor trava automaticamente na posição para evitar que ele escorregue.
* **Clique com Botão Esquerdo**: Junte a ponta do **polegar com o indicador** (gesto de pinça rápida).
* **Duplo Clique**: Dê dois toques rápidos de pinça com o polegar e indicador.
* **Arrastar e Soltar (Drag & Drop)**: Una o polegar e o indicador e **segure por mais de 0.3 segundos**. O sistema ativará o modo de arrasto; abra os dedos para soltar o item.
* **Clique com Botão Direito**: Faça o gesto de pinça entre a ponta do **polegar e o dedo médio**.
* **Rolagem de Página (Scroll)**: Levante o **indicador e o dedo médio juntos** (com os outros dedos fechados) e mova para cima ou para baixo para rolar com inércia natural.

### ⚡ Gestos Especiais Exclusivos do Modo Jarvis (`ironman_touchless_pro.py`):
* **Alternar Área de Trabalho à Direita**: Deslize a palma aberta rapidamente para a **esquerda** (`Win + Ctrl + Seta Direita`).
* **Alternar Área de Trabalho à Esquerda**: Deslize a palma aberta rapidamente para a **direita** (`Win + Ctrl + Seta Esquerda`).
* **Visão de Tarefas (Task View)**: Deslize a palma aberta para **cima** (`Win + Tab`).
* **Mostrar Área de Trabalho / Minimizar Tudo**: Deslize a palma aberta para **baixo** (`Win + D`).
* **Zoom Holográfico Stark**: Faça pinça com **as duas mãos** e afaste-as ou aproxime-as para dar zoom (`Ctrl + Scroll`).
* **Escudo Repulsor**: Mostre as duas palmas abertas para a câmera.

### 🛑 Como Encerrar
Para sair do programa a qualquer momento, clique na janela de vídeo da câmera e pressione a tecla **`q`**.

---

## ❓ Resolução de Problemas Frequentes

### 1. `AttributeError: module 'mediapipe' has no attribute 'solutions'`
* **Causa**: Você está rodando com o Python 3.13 ou instalou uma versão do MediaPipe superior a `0.10.30`.
* **Solução**: Certifique-se de que o Python 3.11 está instalado e instale a versão com suporte:
  ```powershell
  pip uninstall -y mediapipe
  pip install mediapipe==0.10.14
  ```

### 2. A câmera não abre ou a tela fica preta
* Verifique se outros aplicativos (Teams, WhatsApp, Navegador, Discord) não estão utilizando a webcam.
* Se você tiver mais de uma câmera conectada ou placas de captura virtuais (OBS Virtual Cam, DroidCam, etc.), edite a linha da câmera no script ou utilize o `mac_touchless_pro.py` que já possui filtro automático de câmeras USB físicas.

### 3. O cursor se move de forma invertida
* Os scripts utilizam espelhamento de imagem (`cv2.flip(frame, 1)`) para agir como um espelho intuitivo. Mova sua mão confortavelmente dentro da área retangular marcada na tela.
