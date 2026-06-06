const FALLBACK_THEME = {
  text: '#475569',
  textStrong: '#0f172a',
  border: '#d7dfeb',
  gridLine: '#e2e8f0',
  panel: '#ffffff',
  primary: '#2563eb',
  success: '#0f766e',
  warning: '#b45309',
  danger: '#b83280',
  info: '#475569',
  tooltipBg: '#ffffff',
  tooltipBorder: '#d7dfeb'
}

export function readChartTheme() {
  if (typeof globalThis.document === 'undefined' || typeof globalThis.getComputedStyle === 'undefined') {
    return { ...FALLBACK_THEME }
  }

  const styles = globalThis.getComputedStyle(globalThis.document.documentElement)
  const readToken = (name, fallback) => styles.getPropertyValue(name).trim() || fallback

  return {
    text: readToken('--text-secondary', FALLBACK_THEME.text),
    textStrong: readToken('--text-primary', FALLBACK_THEME.textStrong),
    border: readToken('--border-subtle', FALLBACK_THEME.border),
    gridLine: readToken('--border', FALLBACK_THEME.gridLine),
    panel: readToken('--surface-panel', FALLBACK_THEME.panel),
    primary: readToken('--brand-primary', FALLBACK_THEME.primary),
    success: readToken('--status-success', FALLBACK_THEME.success),
    warning: readToken('--status-warning', FALLBACK_THEME.warning),
    danger: readToken('--status-danger', FALLBACK_THEME.danger),
    info: readToken('--status-info', FALLBACK_THEME.info),
    tooltipBg: readToken('--surface-panel', FALLBACK_THEME.tooltipBg),
    tooltipBorder: readToken('--border-subtle', FALLBACK_THEME.tooltipBorder)
  }
}
