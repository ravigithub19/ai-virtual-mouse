# AI Virtual Mouse — Edição SENAI (Alcance de Tela Inteira)

Sistema moderno de controle de mouse sem contato (Touchless Mouse) por Visão Computacional em tempo real, desenvolvido com a identidade visual do **SENAI** e interface em **CustomTkinter**.

---

## 🚀 Como Iniciar

Execute no terminal dentro da pasta do projeto:

```powershell
python main_gui.py
```

*Ou dê um duplo clique no arquivo [`iniciar_interface.bat`](file:///c:/Users/Aluno/Repositorios/ai-virtual-mouse/iniciar_interface.bat).*

---

## ✨ Principais Destaques da Nova Interface

### 🖥️ Controle Real por Toda a Tela (100% de Alcance)
- O mouse virtual **não fica restrito a uma área pequena**: ele controla diretamente a tela inteira do computador (1920x1080) desde o primeiro segundo.
- Mapeamento calibrado com margens adaptativas (`margin_x=85`, `margin_y=65`) permitindo alcançar os 4 cantos da tela e o centro com movimentos confortáveis da mão sobre a mesa, sem cansar o braço.

### 📷 Seleção Automática de Webcam USB
- **Detecção Inteligente**: Identifica automaticamente webcams externas conectadas via USB (ex: *Logitech C922 Pro Stream Webcam*) e dá prioridade absoluta a elas sobre a câmera integrada do notebook ou câmeras virtuais.
- **Seletor de Câmeras em Tempo Real**: Menu suspenso moderno diretamente acima da visão da câmera para alternar entre dispositivos a qualquer momento sem travar a interface.

### 🎨 Visual Moderno & Tema SENAI
- **Interface Dark Mode Contemporânea**: Construída com **CustomTkinter**, cantos arredondados (`corner_radius`), sombras suaves e acabamento refinado.
- **Logo Oficial do SENAI**: Integrada com proporção e resolução preservadas no topo.
- **Identidade Visual**: Acentos marcantes no clássico Vermelho SENAI (`#e30613`).
- **Layout Limpo e Despoluído**: Sem logs de terminal, sem sliders matemáticos complexos e sem excesso de botões que poluem a tela.

### 🎯 Teste de Alcance da Tela Inteira (4 Cantos + Centro)
- Arena interativa que valida o alcance total do monitor:
  - ↖️ Canto Superior Esquerdo
  - ↗️ Canto Superior Direito
  - ↙️ Canto Inferior Esquerdo
  - ↘️ Canto Inferior Direito
  - 🎯 Centro da Tela
- Ao levar o cursor e clicar em cada um, o alvo confirma o alcance (`✓`). Ao completar todos, celebra os 100% de cobertura!

### 🗖 Modo Flutuante / Widget Compacto
- Permite encolher o aplicativo em um clique para uma mini-barra discreta no canto da tela, liberando o monitor para você navegar no Google Chrome, YouTube, jogos ou qualquer programa do Windows com as mãos livres!

---

## 🖐️ Guia de Gestos

| Gesto | Ação | Como Fazer |
| :--- | :--- | :--- |
| **Mover Cursor** | Navegação por toda a tela | Aponte com o dedo indicador naturalmente |
| **Clique Esquerdo** | Clicar em qualquer botão | Junte o polegar e o indicador (pinça firme) |
| **Duplo Clique** | Abrir pastas e programas | Dois toques rápidos de pinça |
| **Arrastar e Soltar** | Mover janelas e ícones | Segure a pinça fechada por mais de 0.3s |
| **Rolagem (Scroll)** | Rolar páginas e feeds | Levante os dedos indicador e médio juntos |
