<template>
  <div class="box model-component">
    <h2 class="title is-4">Customize Weights</h2>
    <div class="content">
      <div class="calibration-container">
        <!-- Calibration bar -->
        <div class="calibration-bar" ref="barRef">
          <div
            v-for="(segment, index) in segments"
            :key="segment.fieldName"
            class="segment"
            :class="{ dimmed: activeView !== null && activeView !== index }"
            :style="{
              width: segment.value + '%',
              backgroundColor: segment.color,
            }"
          >
            <span class="segment-label"> {{ segment.displayName }} ({{ segment.value }}%) </span>
            <!-- Icons inside each segment -->
            <div class="segment-icons">
              <button
                class="icon-button"
                :class="{ active: activeView === index }"
                @click="toggleView(index)"
                :title="
                  activeView === index ? 'Show all categories' : 'Show only ' + segment.displayName
                "
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              </button>
              <button
                class="icon-button"
                @click="openSettings(index)"
                :title="'Settings for ' + segment.displayName"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
                  ></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Handles (only show when no view is active) -->
        <div v-if="activeView === null" class="handles">
          <div
            v-for="(segment, index) in segments.slice(0, -1)"
            :key="'handle-' + index"
            class="handle"
            :style="{ left: getCumulativeWidth(index) + '%' }"
            @mousedown="startDrag(index, $event)"
          >
            <div class="handle-grip">
              <div class="grip-line"></div>
              <div class="grip-line"></div>
              <div class="grip-line"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ModelWeights } from '@/types'
import { onMounted, onUnmounted, ref } from 'vue'

interface SegmentConfig {
  displayName: string
  fieldName: keyof ModelWeights
  dataField: string | null // Maps to model config field
  value: number
  color: string
}

// Props
interface Props {
  weights?: ModelWeights
}

const props = withDefaults(defineProps<Props>(), {
  weights: () => ({
    separation_level: 50,
    speed: 25,
    busyness: 25,
  }),
})

// Emit events
const emit = defineEmits<{
  weightsChanged: [weights: ModelWeights]
  openSettings: [dataField: string]
}>()

// Segment configuration with mapping to data fields
const segments = ref<SegmentConfig[]>([
  {
    displayName: 'Separation level',
    fieldName: 'separation_level',
    dataField: 'separation_level',
    value: props.weights.separation_level,
    color: '#3273dc',
  },
  {
    displayName: 'Speed',
    fieldName: 'speed',
    dataField: 'speed_limit',
    value: props.weights.speed,
    color: '#48c774',
  },
  {
    displayName: 'Busyness',
    fieldName: 'busyness',
    dataField: 'street_classification',
    value: props.weights.busyness,
    color: '#ffdd57',
  },
])

const barRef = ref<HTMLElement | null>(null)
const draggingIndex = ref<number | null>(null)
const activeView = ref<number | null>(null) // Track which view is active (null = all)

const snapToIncrement = (value: number, increment: number = 5): number => {
  return Math.round(value / increment) * increment
}

const getCumulativeWidth = (index: number): number => {
  return segments.value.slice(0, index + 1).reduce((sum, seg) => sum + seg.value, 0)
}

const emitWeightChanges = () => {
  // If a view is active, set other weights to 0 but keep visual slider positions
  if (activeView.value !== null) {
    const weights: ModelWeights = {
      separation_level: activeView.value === 0 ? 100 : 0,
      speed: activeView.value === 1 ? 100 : 0,
      busyness: activeView.value === 2 ? 100 : 0,
    }
    emit('weightsChanged', weights)
  } else {
    const weights: ModelWeights = {
      separation_level: segments.value[0]?.value ?? 0,
      speed: segments.value[1]?.value ?? 0,
      busyness: segments.value[2]?.value ?? 0,
    }
    emit('weightsChanged', weights)
  }
}

/**
 * Toggle view for a specific segment
 */
const toggleView = (index: number) => {
  if (activeView.value === index) {
    // If clicking the active view, turn it off (show all)
    activeView.value = null
  } else {
    // Set this as the active view
    activeView.value = index
  }
  emitWeightChanges()
}

/**
 * Open settings for a specific segment
 */
const openSettings = (index: number) => {
  const segment = segments.value[index]
  if (segment && segment.dataField) {
    emit('openSettings', segment.dataField)
  } else if (segment) {
    console.warn(`No data field mapped for ${segment.displayName}`)
  } else {
    console.warn(`No segment found at index ${index}`)
  }
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
  if (segments.value[index] && segments.value[index + 1]) {
    segments.value[index].value = newLeftValue
    segments.value[index + 1]!.value = newRightValue
  }
}

const handleMouseUp = () => {
  if (draggingIndex.value !== null) {
    draggingIndex.value = null
    // Emit the new weights when user finishes dragging
    emitWeightChanges()
  }
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)

  // Emit initial weights on mount
  emitWeightChanges()
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

/* Calibration bar */
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: filter 0.3s;
  position: relative;
  padding: 0.5rem;
}

.segment:hover {
  filter: brightness(1.1);
}

.segment.dimmed {
  filter: grayscale(100%) brightness(0.8);
  opacity: 0.5;
}

.segment-label {
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  white-space: nowrap;
}

.segment-icons {
  display: flex;
  gap: 0.35rem;
  margin-top: 0.25rem;
  pointer-events: all;
}

.icon-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  padding: 0.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: white;
}

.icon-button:hover {
  background-color: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.icon-button.active {
  background-color: rgba(255, 255, 255, 0.9);
  border-color: rgba(255, 255, 255, 1);
  color: #363636;
}

.icon-button.active:hover {
  background-color: rgba(255, 255, 255, 1);
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
  top: 50%;
  transform: translate(-50%, -50%);
  width: 32px;
  height: 80px;
  cursor: ew-resize;
  pointer-events: all;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.handle-grip {
  width: 24px;
  height: 48px;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  border: 2px solid #333;
  border-radius: 8px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  transition: all 0.2s;
}

.handle:hover .handle-grip {
  background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%);
  border-color: #000;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: scale(1.1);
}

.handle:active .handle-grip {
  background: linear-gradient(135deg, #e8e8e8 0%, #d0d0d0 100%);
  box-shadow:
    0 2px 6px rgba(0, 0, 0, 0.3),
    inset 0 1px 3px rgba(0, 0, 0, 0.2);
  transform: scale(1.05);
}

.grip-line {
  width: 12px;
  height: 2px;
  background-color: #666;
  border-radius: 1px;
}
</style>
