<template>
  <div class="modal" :class="{ 'is-active': isActive }">
    <div class="modal-background" @click="closeModal"></div>
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Separation Level</p>
        <button class="delete" aria-label="close" @click="closeModal"></button>
      </header>
      <section class="modal-card-body">
        <div v-for="(value, key) in settings" :key="key" class="field mb-5">
          <label class="label is-capitalized">
            {{ formatLabel(key) }}
          </label>
          <div class="columns is-vcentered is-mobile">
            <div class="column">
              <input
                type="range"
                class="slider is-fullwidth"
                min="0"
                max="10"
                step="0.5"
                v-model.number="settings[key]"
              />
            </div>
            <div class="column is-narrow">
              <input
                type="number"
                class="input is-small"
                style="width: 70px"
                min="0"
                max="10"
                step="0.5"
                v-model.number="settings[key]"
              />
            </div>
          </div>
        </div>
      </section>
      <footer class="modal-card-foot">
        <div class="buttons">
          <button class="button is-success" @click="saveSettings">Save</button>
          <button class="button" @click="resetDefaults">Reset to Defaults</button>
          <button class="button" @click="closeModal">Cancel</button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface SeparationLevelSettings {
  none: number
  shared_lane: number
  share_busway: number
  lane: number
  lane_buffered: number
  track: number
  separate: number
}

interface Props {
  modelValue: boolean
  initialSettings?: SeparationLevelSettings
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', settings: SeparationLevelSettings): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  initialSettings: () => ({
    none: 0,
    shared_lane: 2,
    share_busway: 5,
    lane: 7,
    lane_buffered: 7.5,
    track: 8,
    separate: 10,
  }),
})

const emit = defineEmits<Emits>()

const isActive = ref(props.modelValue)
const settings = ref<SeparationLevelSettings>({ ...props.initialSettings })

const defaultSettings: SeparationLevelSettings = {
  none: 0,
  shared_lane: 2,
  share_busway: 5,
  lane: 7,
  lane_buffered: 7.5,
  track: 8,
  separate: 10,
}

watch(
  () => props.modelValue,
  (newValue) => {
    isActive.value = newValue
    if (newValue) {
      settings.value = { ...props.initialSettings }
    }
  },
)

const formatLabel = (key: string): string => {
  return key.replace(/_/g, ' ')
}

const closeModal = () => {
  emit('update:modelValue', false)
}

const saveSettings = () => {
  emit('save', { ...settings.value })
  closeModal()
}

const resetDefaults = () => {
  settings.value = { ...defaultSettings }
}
</script>

<style scoped>
.modal {
  z-index: 2000;
}

.modal-background {
  z-index: 2000;
}

.modal-card {
  max-width: 600px;
  width: 90vw;
  z-index: 2001;
}

.label {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.is-capitalized {
  text-transform: capitalize;
}

.slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 8px;
  border-radius: 5px;
  background: #d3d3d3;
  outline: none;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.slider:hover {
  opacity: 1;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #00d1b2;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #00d1b2;
  cursor: pointer;
  border: none;
}

.modal-card-foot {
  justify-content: flex-start;
}
</style>
