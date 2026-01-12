// Utilidades de formateo (Backend enums -> UI en español)

export function normalizeEnum(value) {
  if (value == null) return ''
  const s = String(value)
  // Admite formatos tipo "CasePriority.MEDIUM" o "AccessPermission.READ"
  const parts = s.split('.')
  return (parts[parts.length - 1] || '').trim()
}

export function formatPriority(value) {
  const v = normalizeEnum(value)
  const map = {
    LOW: 'Baja',
    MEDIUM: 'Media',
    HIGH: 'Alta'
  }
  return map[v] || v || ''
}

export function formatStatus(value) {
  const v = normalizeEnum(value)
  const map = {
    OPEN: 'Abierto',
    IN_PROGRESS: 'En atención',
    RESOLVED: 'Resuelto',
    CLOSED: 'Cerrado'
  }
  return map[v] || v || ''
}

export function formatPermission(value) {
  const v = normalizeEnum(value)
  const map = {
    READ: 'Solo lectura',
    WRITE: 'Edición permitida'
  }
  return map[v] || v || ''
}

export function formatArea(value) {
  if (value == null) return ''
  const v = String(value)
  // Soporta valores del backend en español o inglés
  const map = {
    'SOCIAL_WORK': 'Trabajo Social',
    'SOCIAL': 'Trabajo Social',
    'Social work': 'Trabajo Social',
    'PSYCHOLOGY': 'Psicología',
    'PSY': 'Psicología',
    'Psychology': 'Psicología',
    'MEDICAL': 'Médica',
    'Medical': 'Médica',
    'GENERAL': 'General',
    'General': 'General',
    'LEGAL': 'Legal',
    'Legal': 'Legal'
  }
  return map[v] || v
}

function pickChangedKeys(obj = {}) {
  return Object.keys(obj).filter((k) => obj[k] !== undefined && obj[k] !== null)
}

export function formatTimelineEvent(evt = {}) {
  const type = normalizeEnum(evt.type || evt.event)
  const data = evt.data || {}

  if (type === 'CREATED') {
    const parts = []
    if (data.student_id) parts.push(`Estudiante: ${data.student_id}`)
    if (data.owner_area) parts.push(`Área: ${formatArea(data.owner_area)}`)
    if (data.priority) parts.push(`Prioridad: ${formatPriority(data.priority)}`)
    return {
      title: 'Caso creado',
      message: parts.length ? `Se registró el caso. ${parts.join(' • ')}` : 'Se registró el caso.'
    }
  }

  if (type === 'SHARED') {
    const who = data.user_id ? `con ${data.user_id}` : (data.area ? `con el área ${formatArea(data.area)}` : '')
    const perm = data.permission ? `Permiso: ${formatPermission(data.permission)}` : ''
    const msg = [who ? `Compartido ${who}` : 'Caso compartido', perm].filter(Boolean).join(' • ')
    return { title: 'Caso compartido', message: msg || 'Caso compartido.' }
  }

  if (type === 'ASSIGNED') {
    const to = data.professional_id || data.assigned_professional_id
    return {
      title: 'Caso asignado',
      message: to ? `Asignado a ${to}.` : 'Se asignó el caso.'
    }
  }

  if (type === 'STATUS_CHANGED') {
    const to = data.to || data.status || data.new_status
    return {
      title: 'Estado actualizado',
      message: to ? `Nuevo estado: ${formatStatus(to)}.` : 'Se actualizó el estado.'
    }
  }

  if (type === 'NOTE_ADDED') {
    return { title: 'Nota agregada', message: 'Se agregó una nota al caso.' }
  }

  if (type === 'UPDATED') {
    const keys = pickChangedKeys(data)
    // Ocultamos campos técnicos
    const ignore = new Set(['id', 'case_id', 'note_id'])
    const readable = keys.filter((k) => !ignore.has(k))
    if (!readable.length) return { title: 'Caso actualizado', message: 'Se actualizaron datos del caso.' }
    const labels = {
      title: 'título',
      description: 'descripción',
      priority: 'prioridad',
      status: 'estado',
      owner_area: 'área'
    }
    const list = readable
      .map((k) => labels[k] || k)
      .slice(0, 4)
      .join(', ')
    return { title: 'Caso actualizado', message: `Se actualizaron: ${list}.` }
  }

  // Fallback humanizado (sin JSON)
  return {
    title: type ? type.replaceAll('_', ' ') : 'Evento',
    message: 'Se registró un evento en el historial.'
  }
}
