<template>
  <div class="box model-component">
    <h2 class="title is-4">MODEL</h2>
    <div class="content">
      <div class="calibration-container">
        <div class="calibration-bar" ref="barRef">
          <div
            v-for="(segment, index) in segments"
            :key="segment.name"
            class="segment"
            :style="{
              width: segment.value + '%',
              backgroundColor: segment.color,
            }"
          >
            <span class="segment-label"> {{ segment.name }} ({{ segment.value }}%) </span>
          </div>
        </div>
        <div class="handles">
          <div
            v-for="(segment, index) in segments.slice(0, -1)"
            :key="'handle-' + index"
            class="handle"
            :style="{ left: getCumulativeWidth(index) + '%' }"
            @mousedown="startDrag(index, $event)"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

interface Segment {
  name: string
  value: number
  color: string
}

const segments = ref<Segment[]>([
  { name: 'Separation level', value: 50, color: '#3273dc' },
  { name: 'Speed', value: 25, color: '#48c774' },
  { name: 'Busyness', value: 25, color: '#ffdd57' },
])

const barRef = ref<HTMLElement | null>(null)
const draggingIndex = ref<number | null>(null)

const snapToIncrement = (value: number, increment: number = 5): number => {
  return Math.round(value / increment) * increment
}

const getCumulativeWidth = (index: number): number => {
  return segments.value.slice(0, index + 1).reduce((sum, seg) => sum + seg.value, 0)
}

const startDrag = (index: number, event: MouseEvent) => {
  event.preventDefault()
  draggingIndex.value = index
}

const handleMouseMove = (event: MouseEvent) => {
  if (draggingIndex.value === null || !barRef.value) return

  const rect = barRef.value.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const percentage = Math.max(0, Math.min(100, (mouseX / rect.width) * 100))

  const index = draggingIndex.value

  // Calculate the cumulative position where this handle should be
  const prevTotal = index > 0 ? getCumulativeWidth(index - 1) : 0

  // The new cumulative position is the mouse percentage, snapped to 5%
  const newCumulative = snapToIncrement(percentage)

  // Calculate what the left segment should be
  const newLeftValue = Math.max(5, Math.min(95, newCumulative - prevTotal))

  // Calculate what the right segment should be
  const nextTotal = index < segments.value.length - 2 ? getCumulativeWidth(index + 1) : 100
  const newRightValue = Math.max(5, nextTotal - (prevTotal + newLeftValue))

  // Update both segments
  segments.value[index].value = newLeftValue
  segments.value[index + 1].value = newRightValue
}

const handleMouseUp = () => {
  draggingIndex.value = null
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped>
.model-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.title {
  margin-bottom: 1rem;
}

.content {
  flex: 1;
  display: flex;
  align-items: center;
}

.calibration-container {
  width: 100%;
  position: relative;
}

.calibration-bar {
  display: flex;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  user-select: none;
}

.segment {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter 0.2s;
  position: relative;
}

.segment:hover {
  filter: brightness(1.1);
}

.segment-label {
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  white-space: nowrap;
}

.handles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  pointer-events: none;
}

.handle {
  position: absolute;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  cursor: ew-resize;
  pointer-events: all;
  transform: translateX(-2px);
  transition: background-color 0.2s;
}

.handle:hover {
  background-color: rgba(255, 255, 255, 1);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}
</style>
