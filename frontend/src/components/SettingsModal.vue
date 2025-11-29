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

          <div class="is-flex is-justify-content-flex-end mb-4">
            <button class="button is-small reset-button" @click="resetScores">
              <span class="icon is-small">
                <i class="fas fa-undo"></i>
              </span>
              <span>Reset All</span>
            </button>
          </div>

          <h4 class="title is-6">Categories:</h4>
          <div v-for="(category, key) in localCategories" :key="key" class="box mb-3">
            <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
              <strong class="is-capitalized category-name">{{ formatCategoryName(key) }}</strong>
              <span class="tag score-tag">Score: {{ category.score }}</span>
            </div>

            <div class="slider-container mb-3">
              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                v-model.number="category.score"
                class="slider"
                @input="onScoreChange(key, $event)"
              />
              <div class="slider-labels">
                <span class="has-text-grey-light">0</span>
                <span class="has-text-grey-light">5</span>
                <span class="has-text-grey-light">10</span>
              </div>
            </div>

            <p class="is-size-7">{{ category.notes }}</p>
            <img
              v-if="category.img"
              :src="category.img"
              alt=""
              class="mt-2"
              style="max-width: 100%; height: auto"
            />
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
import { BIKE_INFRASTRUCTURE_DATA } from '@/data/bikeData'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

interface Props {
  dataField: string | null
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
  return BIKE_INFRASTRUCTURE_DATA[props.dataField as keyof typeof BIKE_INFRASTRUCTURE_DATA]
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
  if (parameterData.value?.categories) {
    localCategories.value = JSON.parse(JSON.stringify(parameterData.value.categories))

    // Emit reset events for all categories
    if (props.dataField) {
      Object.keys(localCategories.value).forEach((categoryKey) => {
        const originalScore = parameterData.value?.categories[categoryKey]?.score
        if (originalScore !== undefined) {
          emit('updateScore', props.dataField!, categoryKey, originalScore)
        }
      })
    }
  }
}

// Close modal
const closeModal = () => {
  emit('close')
}

// Handle Escape key press
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.dataField) {
    closeModal()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
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

.modal-card-body .box {
  background-color: v-bind('colors.light');
  border-left: 4px solid v-bind('colors.accent');
}

.category-name {
  color: v-bind('colors.dark');
}

.score-tag {
  background-color: v-bind('colors.info');
  color: white;
  font-weight: 600;
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

.learn-more-button {
  background-color: v-bind('colors.info');
  border-color: v-bind('colors.info');
}

.learn-more-button:hover {
  background-color: v-bind('colors.primary');
  border-color: v-bind('colors.primary');
}

/* Slider styles */
.slider-container {
  padding: 0.5rem 0;
}

.slider {
  width: 100%;
  height: 8px;
  border-radius: 5px;
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
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: v-bind('colors.primary');
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: v-bind('colors.primary');
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.slider::-moz-range-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
  font-size: 0.75rem;
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
