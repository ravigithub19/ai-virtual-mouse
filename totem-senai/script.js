/**
 * SENAI - Painel Digital Interativo
 * - Fundo Branco com Ondas Vermelhas Animadas (Canvas 60fps)
 * - Entrada Sequencial Palavra por Palavra (Staggered Words)
 * - Ciclo Automático de 20 Segundos
 * - Sem botões ou ícones poluindo a tela
 */

document.addEventListener("DOMContentLoaded", () => {
  // ==========================================
  // CONFIGURAÇÕES E ESTADO
  // ==========================================
  const DEFAULT_INTERVAL = 20000; // 20 segundos por tela
  let slideDuration = parseInt(localStorage.getItem("senai_slide_duration")) || DEFAULT_INTERVAL;
  let currentSlide = 0;
  let isPaused = false;
  let timerStartTime = Date.now();
  let timerElapsedBeforePause = 0;
  let timerRafId = null;

  // URLs padrão para QR Code
  const DEFAULT_URLS = {
    cursos: "https://www.sp.senai.br/cursos",
    card1: "https://www.sp.senai.br/cursos/tecnicos",
    card2: "https://www.sp.senai.br/cursos/livres",
    card3: "https://www.sp.senai.br/faculdade"
  };

  const ASSET_BASENAMES = {
    cursos: ["qr-cursos", "qrcode-cursos", "cursos"],
    card1: ["qr-1", "qr-tecnicos", "tecnicos"],
    card2: ["qr-2", "qr-livres", "livres"],
    card3: ["qr-3", "qr-faculdade", "faculdade"]
  };

  const EXTENSIONS = ["png", "jpg", "jpeg", "webp", "svg"];

  // Elementos do DOM
  const screens = document.querySelectorAll(".slide-screen");
  const timerBar = document.getElementById("timerBar");
  const settingsModal = document.getElementById("settingsModal");
  const btnCloseSettings = document.getElementById("btnCloseSettings");
  const btnSaveModal = document.getElementById("btnSaveModal");
  const btnResetDefaults = document.getElementById("btnResetDefaults");
  const timeButtons = document.querySelectorAll(".time-btn");

  const fileQrCursos = document.getElementById("fileQrCursos");
  const fileNameCursos = document.getElementById("fileNameCursos");
  const urlQrCursos = document.getElementById("urlQrCursos");
  const fileQrCard1 = document.getElementById("fileQrCard1");
  const fileQrCard2 = document.getElementById("fileQrCard2");
  const fileQrCard3 = document.getElementById("fileQrCard3");
  const urlQrCard1 = document.getElementById("urlQrCard1");
  const urlQrCard2 = document.getElementById("urlQrCard2");
  const urlQrCard3 = document.getElementById("urlQrCard3");

  // ==========================================
  // 1. ANIMAÇÃO DE ONDAS VERMELHAS EM FUNDO BRANCO
  // ==========================================
  const canvas = document.getElementById("waveCanvas");
  const ctx = canvas.getContext("2d");
  let width, height;

  function resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.resetTransform ? ctx.resetTransform() : ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
  }
  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  let waveStep = 0;

  // Configuração das camadas de ondas vermelhas superiores (menores, emoldurando o topo da tela)
  const topWaveLayers = [
    { fill: "rgba(227, 6, 19, 0.05)", length: 0.0025, amplitude: 40, speed: -0.011, offset: 1.1, baseY: 0.22 },
    { fill: "rgba(227, 6, 19, 0.10)", length: 0.0036, amplitude: 34, speed: 0.014, offset: 3.3, baseY: 0.17 },
    { fill: "rgba(227, 6, 19, 0.22)", length: 0.0030, amplitude: 28, speed: -0.016, offset: 0.7, baseY: 0.12 },
    { fill: "rgba(227, 6, 19, 0.55)", length: 0.0040, amplitude: 22, speed: 0.013, offset: 2.6, baseY: 0.075 },
    { fill: "#E30613",                length: 0.0032, amplitude: 15, speed: -0.015, offset: 4.2, baseY: 0.04 }
  ];

  // Configuração das camadas de ondas vermelhas inferiores
  const bottomWaveLayers = [
    { fill: "rgba(227, 6, 19, 0.05)", length: 0.0022, amplitude: 70, speed: 0.012, offset: 0, baseY: 0.62 },
    { fill: "rgba(227, 6, 19, 0.10)", length: 0.0035, amplitude: 60, speed: -0.015, offset: 2.1, baseY: 0.70 },
    { fill: "rgba(227, 6, 19, 0.22)", length: 0.0028, amplitude: 50, speed: 0.018, offset: 4.3, baseY: 0.78 },
    { fill: "rgba(227, 6, 19, 0.55)", length: 0.0042, amplitude: 38, speed: -0.014, offset: 1.5, baseY: 0.85 },
    { fill: "#E30613",                length: 0.0032, amplitude: 26, speed: 0.016, offset: 3.2, baseY: 0.92 }
  ];

  function drawWaves() {
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, width, height);

    waveStep += 0.015;

    // 1. Ondas Superiores (no topo da tela, proporção um pouco menor)
    topWaveLayers.forEach(layer => {
      ctx.beginPath();
      ctx.moveTo(0, 0);
      
      const baseHeight = height * layer.baseY;
      for (let x = 0; x <= width; x += 10) {
        const y = Math.sin(x * layer.length + waveStep * (layer.speed * 60) + layer.offset) * layer.amplitude + baseHeight;
        ctx.lineTo(x, y);
      }
      const endY = Math.sin(width * layer.length + waveStep * (layer.speed * 60) + layer.offset) * layer.amplitude + baseHeight;
      ctx.lineTo(width, endY);
      ctx.lineTo(width, 0);
      ctx.closePath();
      ctx.fillStyle = layer.fill;
      ctx.fill();
    });

    // 2. Ondas Inferiores (na parte de baixo da tela)
    bottomWaveLayers.forEach(layer => {
      ctx.beginPath();
      ctx.moveTo(0, height);
      
      const baseHeight = height * layer.baseY;
      for (let x = 0; x <= width; x += 10) {
        const y = Math.sin(x * layer.length + waveStep * (layer.speed * 60) + layer.offset) * layer.amplitude + baseHeight;
        ctx.lineTo(x, y);
      }
      const endY = Math.sin(width * layer.length + waveStep * (layer.speed * 60) + layer.offset) * layer.amplitude + baseHeight;
      ctx.lineTo(width, endY);
      ctx.lineTo(width, height);
      ctx.closePath();
      ctx.fillStyle = layer.fill;
      ctx.fill();
    });

    requestAnimationFrame(drawWaves);
  }
  drawWaves();

  // ==========================================
  // 2. ENTRADA SEQUENCIAL: PALAVRAS UMA DE CADA VEZ
  // ==========================================
  function setupWordStaggering() {
    const textEls = document.querySelectorAll(".stagger-words");
    textEls.forEach(el => {
      if (!el.dataset.rawText) {
        el.dataset.rawText = el.textContent.trim();
      }
      const words = el.dataset.rawText.split(/\s+/);
      const baseDelay = parseFloat(el.dataset.baseDelay || 0.1);
      
      el.innerHTML = words.map((word, idx) => {
        return `<span class="word-mask"><span class="word" style="--w-idx: ${idx}; --base-delay: ${baseDelay}s;">${word}</span></span>`;
      }).join(" ");
    });
  }
  setupWordStaggering();

  function triggerWordEntrance(screenElement) {
    const words = screenElement.querySelectorAll(".word");
    words.forEach(w => {
      w.style.animation = "none";
      void w.offsetHeight; // Força reflow do navegador
      w.style.animation = "";
    });
  }

  function triggerCardEntrance(screenElement) {
    const cards = screenElement.querySelectorAll(".qr-card");
    if (!cards.length) return;
    cards.forEach(card => {
      card.style.animation = "none";
      void card.offsetHeight; // Força reflow do navegador
      card.style.animation = "";
    });
  }

  // ==========================================
  // 3. GERENCIAMENTO DE QR CODES
  // ==========================================
  function findLocalImage(baseNames, onSuccess, onFail) {
    const candidatePaths = [];
    baseNames.forEach(base => {
      EXTENSIONS.forEach(ext => {
        candidatePaths.push(`assets/${base}.${ext}`);
      });
    });

    let index = 0;
    function tryNext() {
      if (index >= candidatePaths.length) {
        onFail();
        return;
      }
      const path = candidatePaths[index++];
      const img = new Image();
      img.onload = () => onSuccess(path);
      img.onerror = () => tryNext();
      img.src = path + "?v=" + Date.now();
    }
    tryNext();
  }

  function renderQR(key, imgId, dynamicId, size) {
    const imgEl = document.getElementById(imgId);
    const dynamicEl = document.getElementById(dynamicId);
    if (!imgEl || !dynamicEl) return;

    // 1. Checa upload salvo em localStorage
    const customDataUri = localStorage.getItem(`senai_custom_img_${key}`);
    if (customDataUri) {
      imgEl.src = customDataUri;
      imgEl.style.display = "block";
      dynamicEl.style.display = "none";
      return;
    }

    // 2. Busca na pasta assets/
    findLocalImage(
      ASSET_BASENAMES[key],
      (foundPath) => {
        imgEl.src = foundPath;
        imgEl.style.display = "block";
        dynamicEl.style.display = "none";
      },
      () => {
        // 3. Fallback QRCode.js
        imgEl.style.display = "none";
        dynamicEl.style.display = "flex";
        dynamicEl.innerHTML = "";

        const targetUrl = localStorage.getItem(`senai_url_${key}`) || DEFAULT_URLS[key];
        if (typeof QRCode !== "undefined") {
          new QRCode(dynamicEl, {
            text: targetUrl,
            width: size,
            height: size,
            colorDark: "#111111",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
          });
        }
      }
    );
  }

  function initQRCodes() {
    renderQR("cursos", "qrImgCursos", "qrDynamicCursos", 260);
  }

  // ==========================================
  // 4. TRANSIÇÃO DAS TELAS E CONTADOR DE 20 SEGUNDOS
  // ==========================================
  let isTransitioning = false;

  function prepareScreen3Entrance() {
    const screen3 = document.getElementById("screen3");
    const title = document.getElementById("screen3Title");
    if (!screen3 || !title) return;

    screen3.classList.remove("intro-animating");
    title.style.removeProperty("--center-delta-y");

    // Força reflow no navegador
    void screen3.offsetWidth;

    // Calcula o deslocamento exato da posição final do título até o centro exato da tela
    const rect = title.getBoundingClientRect();
    const screenCenterY = window.innerHeight / 2;
    const titleCenterY = rect.top + (rect.height / 2);
    const deltaY = Math.round(screenCenterY - titleCenterY);

    title.style.setProperty("--center-delta-y", `${deltaY}px`);
    screen3.classList.add("intro-animating");
  }

  function goToSlide(index) {
    if (isTransitioning) return;
    if (index < 0) index = screens.length - 1;
    if (index >= screens.length) index = 0;

    // Se estiver mudando para a Tela 3 (índice 2) a partir de outra tela
    if (index === 2 && currentSlide !== 2) {
      isTransitioning = true;
      const outgoingScreen = screens[currentSlide];
      const windOverlay = document.getElementById("windOverlay");

      // 1. Efeito de vento para a esquerda levando todas as palavras
      outgoingScreen.classList.add("wind-blowing-out");
      if (windOverlay) {
        windOverlay.classList.remove("active");
        void windOverlay.offsetWidth;
        windOverlay.classList.add("active");
      }

      // 2. Aguarda a rajada de vento tirar as palavras (650ms)
      setTimeout(() => {
        outgoingScreen.classList.remove("active", "wind-blowing-out");
        if (windOverlay) windOverlay.classList.remove("active");

        currentSlide = 2;
        screens.forEach((screen, idx) => {
          if (idx === 2) {
            screen.classList.add("active");
            prepareScreen3Entrance();
          } else {
            screen.classList.remove("active", "wind-blowing-out", "intro-animating");
          }
        });

        resetTimer();
        isTransitioning = false;
      }, 650);
      return;
    }

    // Transição normal para as outras telas (Tela 1 ou Tela 2)
    currentSlide = index;

    screens.forEach((screen, idx) => {
      screen.classList.remove("wind-blowing-out", "intro-animating");
      if (idx === currentSlide) {
        screen.classList.add("active");
        if (idx === 2) {
          prepareScreen3Entrance();
        } else {
          triggerWordEntrance(screen);
          triggerCardEntrance(screen);
        }
      } else {
        screen.classList.remove("active");
      }
    });

    resetTimer();
  }

  function nextSlide() {
    goToSlide(currentSlide + 1);
  }

  function prevSlide() {
    goToSlide(currentSlide - 1);
  }

  function resetTimer() {
    timerStartTime = Date.now();
    timerElapsedBeforePause = 0;
    updateTimerVisuals(0);
  }

  function updateTimerVisuals(elapsed) {
    const progressPercent = Math.min(100, (elapsed / slideDuration) * 100);
    if (timerBar) {
      timerBar.style.width = `${progressPercent}%`;
    }
  }

  function timerLoop() {
    if (!isPaused) {
      const elapsed = (Date.now() - timerStartTime) + timerElapsedBeforePause;
      updateTimerVisuals(elapsed);

      if (elapsed >= slideDuration) {
        nextSlide();
      }
    }
    timerRafId = requestAnimationFrame(timerLoop);
  }

  function togglePause() {
    isPaused = !isPaused;
    if (isPaused) {
      timerElapsedBeforePause += (Date.now() - timerStartTime);
    } else {
      timerStartTime = Date.now();
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) document.exitFullscreen();
    }
  }

  // ==========================================
  // 5. ATALHOS DE TECLADO (SILENCIOSOS)
  // ==========================================
  window.addEventListener("keydown", (e) => {
    if (settingsModal.style.display === "flex") {
      if (e.key === "Escape") closeSettings();
      return;
    }

    switch (e.key) {
      case "ArrowRight":
      case "PageDown":
        nextSlide();
        break;
      case "ArrowLeft":
      case "PageUp":
        prevSlide();
        break;
      case " ":
        e.preventDefault();
        togglePause();
        break;
      case "f":
      case "F":
        toggleFullscreen();
        break;
      case "s":
      case "S":
        openSettings();
        break;
    }
  });

  // Toque / Swipe em telas touch
  let touchStartX = 0;
  window.addEventListener("touchstart", (e) => {
    touchStartX = e.changedTouches[0].screenX;
  }, { passive: true });

  window.addEventListener("touchend", (e) => {
    const diff = e.changedTouches[0].screenX - touchStartX;
    if (Math.abs(diff) > 60) {
      if (diff < 0) nextSlide();
      else prevSlide();
    }
  }, { passive: true });

  // ==========================================
  // 6. MODAL DE CONFIGURAÇÃO (ABERTO VIA 'S')
  // ==========================================
  function openSettings() {
    urlQrCursos.value = localStorage.getItem("senai_url_cursos") || DEFAULT_URLS.cursos;
    urlQrCard1.value = localStorage.getItem("senai_url_card1") || DEFAULT_URLS.card1;
    urlQrCard2.value = localStorage.getItem("senai_url_card2") || DEFAULT_URLS.card2;
    urlQrCard3.value = localStorage.getItem("senai_url_card3") || DEFAULT_URLS.card3;

    timeButtons.forEach(btn => {
      if (parseInt(btn.dataset.time) === slideDuration) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    settingsModal.style.display = "flex";
  }

  function closeSettings() {
    settingsModal.style.display = "none";
  }

  function setupFileInput(inputElement, labelElement, storageKey, callback) {
    if (!inputElement) return;
    inputElement.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        if (labelElement) labelElement.textContent = file.name;
        const reader = new FileReader();
        reader.onload = (event) => {
          localStorage.setItem(storageKey, event.target.result);
          if (callback) callback();
        };
        reader.readAsDataURL(file);
      }
    });
  }

  setupFileInput(fileQrCursos, fileNameCursos, "senai_custom_img_cursos", () => {
    renderQR("cursos", "qrImgCursos", "qrDynamicCursos", 260);
  });
  setupFileInput(fileQrCard1, null, "senai_custom_img_card1", () => {
    renderQR("card1", "qrImgCard1", "qrDynamicCard1", 170);
  });
  setupFileInput(fileQrCard2, null, "senai_custom_img_card2", () => {
    renderQR("card2", "qrImgCard2", "qrDynamicCard2", 170);
  });
  setupFileInput(fileQrCard3, null, "senai_custom_img_card3", () => {
    renderQR("card3", "qrImgCard3", "qrDynamicCard3", 170);
  });

  timeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      timeButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      slideDuration = parseInt(btn.dataset.time);
      localStorage.setItem("senai_slide_duration", slideDuration);
      resetTimer();
    });
  });

  btnSaveModal.addEventListener("click", () => {
    if (urlQrCursos.value.trim()) localStorage.setItem("senai_url_cursos", urlQrCursos.value.trim());
    if (urlQrCard1.value.trim()) localStorage.setItem("senai_url_card1", urlQrCard1.value.trim());
    if (urlQrCard2.value.trim()) localStorage.setItem("senai_url_card2", urlQrCard2.value.trim());
    if (urlQrCard3.value.trim()) localStorage.setItem("senai_url_card3", urlQrCard3.value.trim());

    initQRCodes();
    closeSettings();
  });

  btnResetDefaults.addEventListener("click", () => {
    if (confirm("Deseja restaurar as configurações padrão?")) {
      localStorage.removeItem("senai_custom_img_cursos");
      localStorage.removeItem("senai_custom_img_card1");
      localStorage.removeItem("senai_custom_img_card2");
      localStorage.removeItem("senai_custom_img_card3");
      localStorage.removeItem("senai_url_cursos");
      localStorage.removeItem("senai_url_card1");
      localStorage.removeItem("senai_url_card2");
      localStorage.removeItem("senai_url_card3");
      localStorage.setItem("senai_slide_duration", DEFAULT_INTERVAL);
      slideDuration = DEFAULT_INTERVAL;
      
      initQRCodes();
      closeSettings();
      resetTimer();
    }
  });

  btnCloseSettings.addEventListener("click", closeSettings);
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) closeSettings();
  });

  // ==========================================
  // INICIALIZAÇÃO
  // ==========================================
  initQRCodes();
  goToSlide(0);
  timerRafId = requestAnimationFrame(timerLoop);
});
