import { ref } from 'vue'

export function useGridPanZoom() {
  const panX = ref(0)
  const panY = ref(0)
  const zoomEscala = ref(1)

  let toqueUnico = null
  let pinchInicial = null

  function distanciaEntreToques(t1, t2) {
    return Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY)
  }

  function pontoMedioToques(t1, t2) {
    return {
      x: (t1.clientX + t2.clientX) / 2,
      y: (t1.clientY + t2.clientY) / 2
    }
  }

  function iniciarToquePanZoom(e) {
    if (e.touches.length === 2) {
      toqueUnico = null
      const dist = distanciaEntreToques(e.touches[0], e.touches[1])
      const meio = pontoMedioToques(e.touches[0], e.touches[1])
      pinchInicial = {
        dist,
        escala: zoomEscala.value,
        panX: panX.value,
        panY: panY.value,
        meioX: meio.x,
        meioY: meio.y
      }
    } else if (e.touches.length === 1) {
      pinchInicial = null
      const t = e.touches[0]
      toqueUnico = {
        startX: t.clientX,
        startY: t.clientY,
        lastX: t.clientX,
        lastY: t.clientY,
        panXInicial: panX.value,
        panYInicial: panY.value,
        moveu: false
      }
    }
  }

  function moverToquePanZoom(e) {
    if (e.touches.length === 2 && pinchInicial) {
      const novaDist = distanciaEntreToques(e.touches[0], e.touches[1])
      const novoMeio = pontoMedioToques(e.touches[0], e.touches[1])
      const fator = novaDist / pinchInicial.dist
      zoomEscala.value = Math.min(2.5, Math.max(0.45, pinchInicial.escala * fator))
      panX.value = pinchInicial.panX + (novoMeio.x - pinchInicial.meioX)
      panY.value = pinchInicial.panY + (novoMeio.y - pinchInicial.meioY)
    } else if (e.touches.length === 1 && toqueUnico) {
      const t = e.touches[0]
      toqueUnico.lastX = t.clientX
      toqueUnico.lastY = t.clientY
      const dx = t.clientX - toqueUnico.startX
      const dy = t.clientY - toqueUnico.startY

      if (Math.hypot(dx, dy) > 7) {
        toqueUnico.moveu = true
        panX.value = toqueUnico.panXInicial + dx
        panY.value = toqueUnico.panYInicial + dy
      }
    }
  }

  function finalizarToquePanZoom(e, aoTocarCelulaSemArrastar) {
    if (e.touches.length < 2) pinchInicial = null
    if (e.touches.length === 0 && toqueUnico) {
      if (!toqueUnico.moveu && typeof aoTocarCelulaSemArrastar === 'function') {
        const el = document.elementFromPoint(toqueUnico.lastX, toqueUnico.lastY)
        const celulaEl = el?.closest('[data-coord]')
        if (celulaEl) {
          const [cx, cy] = celulaEl.getAttribute('data-coord').split(',').map(Number)
          aoTocarCelulaSemArrastar(cx, cy)
        }
      }
      toqueUnico = null
    }
  }

  function resetarCameraGrid() {
    panX.value = 0
    panY.value = 0
    zoomEscala.value = 1
  }

  return {
    panX,
    panY,
    zoomEscala,
    iniciarToquePanZoom,
    moverToquePanZoom,
    finalizarToquePanZoom,
    resetarCameraGrid
  }
}
