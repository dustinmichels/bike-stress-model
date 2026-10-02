<script setup lang="ts">
import { Car, ExternalLink, Gauge, RotateCcw, Settings, Shield } from '@lucide/vue'
import { BIKE_INFRASTRUCTURE_MODEL } from '@/data/bikeData'
import { MAX_SCORE } from '@/utils/colorScale'
import type { BikeInfrastructureModel } from '@/types'
import { computed, onMounted, onUnmounted } from 'vue'

interface Props {
  dataField: string | null
  modelConfig: BikeInfrastructureModel
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  updateScore: [field: string, category: string, score: number]
}>()

const getFieldIcon = (field: string | null) => {
  if (field === 'separation_level') return Shield
  if (field === 'speed_limit') return Gauge
  if (field === 'street_classification') return Car
  return Settings
}


// Computed property to get the parameter data directly from props
const parameterData = computed(() => {
  if (!props.dataField) return null
  return props.modelConfig[props.dataField as keyof BikeInfrastructureModel]
})

// Computed property for display name
const displayName = computed(() => {
  if (!props.dataField) return ''
  const displayNames: Record<string, string> = {
    separation_level: 'Separation Level',
    speed_limit: 'Speed Limit',
    street_classification: 'Street Classification (Busyness)',
  }
  return displayNames[props.dataField] || props.dataField
})

// Helper function to format category names nicely
const formatCategoryName = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/-/g, ' ')
}

// Function to get color based on score (0 = green, MAX_SCORE = red)
const getScoreColor = (score: number): string => {
  const normalized = score / MAX_SCORE
  const r = Math.round(34 + (239 - 34) * normalized)
  const g = Math.round(197 + (68 - 197) * normalized)
  const b = Math.round(94 + (68 - 94) * normalized)
  return `rgb(${r}, ${g}, ${b})`
}

// Function to get slider style with dynamic thumb color
const getSliderStyle = (score: number) => {
  const thumbColor = getScoreColor(score)
  return {
    '--thumb-color': thumbColor,
  }
}

// Handle score changes
const onScoreChange = (categoryKey: string, event: Event) => {
  const target = event.target as HTMLInputElement
  const newScore = parseFloat(target.value)
  if (props.dataField && !isNaN(newScore)) {
    emit('updateScore', props.dataField, categoryKey, newScore)
  }
}

// Reset all scores for the active field to original default values
const resetScores = () => {
  if (!props.dataField) return
  const originalData =
    BIKE_INFRASTRUCTURE_MODEL[props.dataField as keyof typeof BIKE_INFRASTRUCTURE_MODEL]
  if (originalData?.categories) {
    for (const [categoryKey, category] of Object.entries(originalData.categories)) {
      emit('updateScore', props.dataField, categoryKey, category.score)
    }
  }
}

const closeModal = () => {
  emit('close')
}

const handleEscape = (event: KeyboardEvent) => {
  if (event.key !== 'Escape' || !props.dataField) return
  closeModal()
}

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="dataField" class="modal is-active">
      <div class="modal-background" @click="closeModal"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title is-flex is-align-items-center">
            <component :is="getFieldIcon(dataField)" :size="20" class="mr-2" />
            <span>Settings: {{ displayName }}</span>
          </p>
          <button class="delete" aria-label="close" @click="closeModal"></button>
        </header>
        <section class="modal-card-body">
          <div v-if="parameterData">
            <p class="mb-4">{{ parameterData.notes }}</p>

            <div class="is-flex is-justify-content-flex-end mb-3">
              <button class="button is-small reset-button" @click="resetScores">
                <span class="icon is-small">
                  <RotateCcw :size="14" />
                </span>
                <span>Reset All</span>
              </button>
            </div>

            <!-- Compact Table-Style Categories -->
            <div class="categories-table">
              <div
                v-for="(category, key) in parameterData.categories"
                :key="key"
                class="category-row"
              >
                <div class="category-left">
                  <strong class="category-name">{{ formatCategoryName(String(key)) }}</strong>
                  <p class="category-notes">{{ category.notes }}</p>
                  <img v-if="category.img" :src="category.img" alt="" class="category-img" />
                </div>
                <div class="category-right">
                  <div class="slider-control">
                    <input
                      type="range"
                      min="0"
                      :max="MAX_SCORE"
                      step="0.5"
                      :value="category.score"
                      class="slider"
                      :style="getSliderStyle(category.score)"
                      @input="onScoreChange(String(key), $event)"
                    />
                    <span class="score-value">{{ category.score.toFixed(1) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <a
              v-if="parameterData.link"
              :href="parameterData.link"
              target="_blank"
              class="button is-link is-small mt-4 learn-more-button"
            >
              <span class="icon is-small">
                <ExternalLink :size="14" />
              </span>
              <span>Learn More on OpenStreetMap Wiki</span>
            </a>
          </div>
        </section>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-card-head {
  background-color: #3273dc;
  border-bottom: none;
}

.modal-card-title {
  color: white;
}

.delete {
  background-color: rgba(255, 255, 255, 0.3);
}

.delete:hover {
  background-color: rgba(255, 255, 255, 0.5);
}

.modal-card-body {
  background-color: white;
}

.reset-button {
  background-color: #3273dc;
  color: white;
  border: none;
}

.reset-button:hover {
  background-color: #2366d1;
  color: white;
}

/* Compact Table-Style Categories */
.categories-table {
  border: 1px solid #dbdbdb;
  border-radius: 6px;
  overflow: hidden;
}

.category-row {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #dbdbdb;
  background-color: white;
  transition: background-color 0.2s;
}

.category-row:last-child {
  border-bottom: none;
}

.category-row:hover {
  background-color: #f5f5f5;
}

.category-left {
  flex: 1;
  padding-right: 1.5rem;
}

.category-name {
  display: block;
  color: #363636;
  font-size: 0.95rem;
  text-transform: capitalize;
  margin-bottom: 0.25rem;
}

.category-notes {
  font-size: 0.8rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.3;
}

.category-img {
  max-width: 150px;
  height: auto;
  margin-top: 0.5rem;
  border-radius: 4px;
}

.category-right {
  width: 220px;
  flex-shrink: 0;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, #e5e7eb 0%, #9ca3af 50%, #6b7280 100%);
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--thumb-color, #3273dc);
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--thumb-color, #3273dc);
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.score-value {
  font-weight: 600;
  color: #363636;
  font-size: 1rem;
  min-width: 2.5rem;
  text-align: right;
}

.learn-more-button {
  background-color: #3273dc;
  border-color: #3273dc;
}

.learn-more-button:hover {
  background-color: #2366d1;
  border-color: #2366d1;
}

/* Ensure modal appears above map */
.modal {
  z-index: 99999 !important;
}

.modal-background {
  z-index: 99998 !important;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-card {
  z-index: 100000 !important;
}
</style>
