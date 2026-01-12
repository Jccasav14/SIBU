<template>
  <div class="cal">
    <div class="calTop">
      <div class="left">
        <h2 class="title">{{ title }}</h2>
        <p class="sub">{{ subtitle }}</p>
      </div>

      <div class="actions">
        <button class="ghost" @click="$emit('prev')">‹</button>
        <button class="ghost" @click="$emit('today')">Hoy</button>
        <button class="ghost" @click="$emit('next')">›</button>
      </div>
    </div>

    <div class="grid">
      <div class="head">
        <div class="timeCol"></div>
        <div v-for="d in days" :key="d.key" class="dayHead">
          <div class="dow">{{ d.dow }}</div>
          <div class="date">{{ d.date }}</div>
        </div>
      </div>

      <div class="body">
        <div v-for="t in times" :key="t" class="row">
          <div class="timeCol">{{ t }}</div>

          <div
            v-for="d in days"
            :key="d.key + '-' + t"
            class="cell"
            @click="$emit('cellClick', { dayKey: d.key, time: t, blocks: blocksFor(d.key, t) })"
          >
            <div class="stack">
              <template v-if="blocksFor(d.key, t).length === 1">
                <div
                  class="block"
                  :class="blocksFor(d.key, t)[0].kind"
                  @click.stop="$emit('blockClick', blocksFor(d.key, t)[0].raw)"
                >
                  <div class="bTitle">{{ blocksFor(d.key, t)[0].title }}</div>
                  <div class="bLabel">{{ blocksFor(d.key, t)[0].label }}</div>
                  <div class="bSub">{{ blocksFor(d.key, t)[0].sub }}</div>
                </div>
              </template>

              <template v-else-if="blocksFor(d.key, t).length > 1">
                <div class="block booked multi">
                  <div class="bTitle">
                    {{ blocksFor(d.key, t).some(b => b.kind === 'booked') ? 'Ocupado' : 'Disponible' }}
                    · {{ blocksFor(d.key, t).length }}
                  </div>
                  <div class="bSub">Varios profesionales</div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div class="legend">
        <span class="dot open"></span><span>Disponible</span>
        <span class="dot booked"></span><span>Ocupado</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Agenda' },
  subtitle: { type: String, default: '' },
  weekStart: { type: Date, required: true },
  slots: { type: Array, default: () => [] }, // {id, starts_at, ends_at, is_booked, area, location, professional_email}
  appointmentsBySlotId: { type: Object, default: () => ({}) }, // { [slotId]: appointment }
  startHour: { type: Number, default: 7 },
  endHour: { type: Number, default: 19 },
  stepMinutes: { type: Number, default: 30 },
})

const days = computed(() => {
  const out = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(props.weekStart)
    d.setDate(d.getDate() + i)
    out.push({
      key: toKey(d.toISOString()),
      dow: d.toLocaleDateString('es-EC', { weekday: 'short' }),
      date: d.toLocaleDateString('es-EC', { day: '2-digit', month: 'short' }),
    })
  }
  return out
})

const times = computed(() => {
  const out = []
  const base = new Date()
  base.setHours(props.startHour, 0, 0, 0)
  const end = new Date()
  end.setHours(props.endHour, 0, 0, 0)

  for (let d = new Date(base); d <= end; d = new Date(d.getTime() + props.stepMinutes * 60 * 1000)) {
    out.push(toHM(d.toISOString()))
  }
  return out
})

function toKey(dateStr) {
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

function toHM(dateStr) {
  const d = new Date(dateStr)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

function blocksFor(dayKey, time) {
  const blocks = []

  for (const s of props.slots || []) {
    const dk = toKey(s.starts_at)
    if (dk !== dayKey) continue

    const start = toHM(s.starts_at)
    if (start !== time) continue

    const appt = props.appointmentsBySlotId?.[s.id] || null

    blocks.push({
      key: `slot-${s.id}`,
      kind: s.is_booked ? 'booked' : 'open',
      title: s.is_booked ? 'Ocupado' : 'Disponible',
      label: s.is_booked ? (appt?.student_id ? `Cita · ${appt.student_id}` : 'Ocupado') : 'Disponible',
      sub: s.area ? String(s.area).replaceAll('_', ' ') : '',
      raw: { slot: s, appointment: appt },
    })
  }

  return blocks
}
</script>

<style scoped>
.cal{ width:100%; }
.calTop{
  display:flex; align-items:flex-end; justify-content:space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.title{ font-size: 18px; margin:0; }
.sub{ margin:4px 0 0; color:#6b7280; font-size: 12px; }
.actions{ display:flex; gap:8px; }

.ghost{
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor:pointer;
}

.grid{
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  overflow:hidden;
  background:#fff;
}

.head, .row{
  display:grid;
  grid-template-columns: 90px repeat(7, 1fr);
}
.head{
  background:#f8fafc;
  border-bottom:1px solid #e5e7eb;
}
.timeCol{
  padding: 10px 12px;
  color:#6b7280;
  font-size:12px;
}
.dayHead{
  padding: 10px 12px;
  border-left:1px solid #e5e7eb;
}
.dow{ font-size:12px; color:#6b7280; text-transform:capitalize; }
.date{ font-size: 13px; font-weight:700; }

.body .row{
  border-bottom:1px solid #f1f5f9;
}
.body .row:last-child{ border-bottom:none; }

.cell{
  min-height: 56px;
  border-left:1px solid #f1f5f9;
  padding: 6px;
  cursor:pointer;
}
.cell:hover{ background:#f8fafc; }

.stack{ display:flex; flex-direction:column; gap:6px; height:100%; }

.block{
  border-radius: 12px;
  padding: 8px 10px;
  border: 1px solid transparent;
  line-height: 1.1;
}
.block.open{
  background: rgba(6,182,212,.10);
  border-color: rgba(6,182,212,.25);
}
.block.booked{
  background: rgba(239,68,68,.10);
  border-color: rgba(239,68,68,.25);
}
.block.multi{ text-align:center; }

.bTitle{ font-weight:800; font-size: 13px; }
.bLabel{ margin-top: 3px; font-size: 12px; font-weight:700; }
.bSub{ margin-top: 2px; font-size: 11px; color:#6b7280; text-transform:uppercase; }

.legend{
  display:flex;
  align-items:center;
  gap: 8px;
  padding: 10px 12px;
  color:#6b7280;
  font-size: 12px;
  border-top:1px solid #e5e7eb;
}
.dot{ width:10px; height:10px; border-radius: 50%; display:inline-block; }
.dot.open{ background:#06b6d4; }
.dot.booked{ background:#ef4444; }

@media (max-width: 980px){
  .head, .row{ grid-template-columns: 70px repeat(7, 180px); }
  .grid{ overflow:auto; }
}
</style>
