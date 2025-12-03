<template>
  <div v-if="dataField" class="modal is-active">
    <div class="modal-background" @click="closeModal"></div>
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Settings: {{ displayName }}</p>
        <button class="delete" aria-label="close" @click="closeModal"></button>
      </header>
      <section class="modal-card-body">
        <div v-if="parameterData">
          <p class="mb-4">{{ parameterData.notes }}</p>

          <div class="is-flex is-justify-content-flex-end mb-3">
            <button class="button is-small reset-button" @click="resetScores">
              <span class="icon is-small">
                <i class="fas fa-undo"></i>
              </span>
              <span>Reset All</span>
            </button>
          </div>

          <!-- Compact Table-Style Categories -->
          <div class="categories-table">
            <div v-for="(category, key) in localCategories" :key="key" class="category-row">
              <div class="category-left">
                <strong class="category-name">{{ formatCategoryName(key) }}</strong>
                <p class="category-notes">{{ category.notes }}</p>
                <img v-if="category.img" :src="category.img" alt="" class="category-img" />
              </div>
              <div class="category-right">
                <div class="slider-control">
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.5"
                    v-model.number="category.score"
                    class="slider"
                    @input="onScoreChange(key, $event)"
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
              <i class="fas fa-external-link-alt"></i>
            </span>
            <span>Learn More on OpenStreetMap Wiki</span>
          </a>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BIKE_INFRASTRUCTURE_MODEL } from '@/data/bikeData'
import type { BikeInfrastructureModel } from '@/types'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

interface Props {
  dataField: string | null
  modelConfig: BikeInfrastructureModel
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  updateScore: [field: string, category: string, score: number]
}>()

// Color palette
const colors = {
  primary: '#BD1872',
  dark: '#232527',
  light: '#D4DCFF',
  accent: '#7D83FF',
  info: '#007FFF',
}

// Local state for categories with scores
const localCategories = ref<Record<string, any>>({})

// Computed property to get the parameter data
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

// Initialize local categories when dataField changes
watch(
  () => props.dataField,
  () => {
    if (parameterData.value?.categories) {
      localCategories.value = JSON.parse(JSON.stringify(parameterData.value.categories))
    }
  },
  { immediate: true },
)

// Helper function to format category names nicely
const formatCategoryName = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/-/g, ' ')
}

// Handle score changes
const onScoreChange = (categoryKey: string, event: Event) => {
  const target = event.target as HTMLInputElement
  const newScore = parseFloat(target.value)

  if (props.dataField) {
    emit('updateScore', props.dataField, categoryKey, newScore)
  }
}

// Reset all scores to original values
const resetScores = () => {
  if (!props.dataField) return

  const originalData =
    BIKE_INFRASTRUCTURE_MODEL[props.dataField as keyof typeof BIKE_INFRASTRUCTURE_MODEL]
  if (originalData?.categories) {
    localCategories.value = JSON.parse(JSON.stringify(originalData.categories))

    // Emit reset events for all categories
    Object.keys(localCategories.value).forEach((categoryKey) => {
      const originalScore = originalData.categories[categoryKey]?.score
      if (originalScore !== undefined) {
        emit('updateScore', props.dataField!, categoryKey, originalScore)
      }
    })
  }
}

// Close modal
const closeModal = () => {
  emit('close')
}

// Handle escape key
const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    closeModal()
  }
}

// Add/remove event listener
onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
.modal-card-head {
  background-color: v-bind('colors.primary');
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
  background-color: v-bind('colors.accent');
  color: white;
  border: none;
}

.reset-button:hover {
  background-color: v-bind('colors.primary');
  color: white;
}

/* Compact Table-Style Categories */
.categories-table {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.category-row {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background-color: white;
  transition: background-color 0.2s;
}

.category-row:last-child {
  border-bottom: none;
}

.category-row:hover {
  background-color: #f9fafb;
}

.category-left {
  flex: 1;
  padding-right: 1.5rem;
}

.category-name {
  display: block;
  color: v-bind('colors.dark');
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
  background: linear-gradient(
    to right,
    v-bind('colors.light') 0%,
    v-bind('colors.accent') 50%,
    v-bind('colors.info') 100%
  );
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: v-bind('colors.primary');
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
  background: v-bind('colors.primary');
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
  color: v-bind('colors.primary');
  font-size: 1rem;
  min-width: 2.5rem;
  text-align: right;
}

.learn-more-button {
  background-color: v-bind('colors.info');
  border-color: v-bind('colors.info');
}

.learn-more-button:hover {
  background-color: v-bind('colors.primary');
  border-color: v-bind('colors.primary');
}

/* Ensure modal appears above map */
.modal {
  z-index: 99999 !important;
}

.modal-background {
  z-index: 99998 !important;
  background-color: rgba(35, 37, 39, 0.7);
}

.modal-card {
  z-index: 100000 !important;
}
</style>
