<template>
  <div class="box about-component">
    <!-- Title and City Selector -->
    <div class="header-row">
      <h2 class="title is-4">Bike Safety Map</h2>
      <div class="field">
        <div class="control">
          <div class="select">
            <select :value="currCity" @change="handleCityChange">
              <option v-for="city in cities" :key="city" :value="city">{{ city }}, MA, USA</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="content">
      <p>
        This map shows a composite safety score for each segment of the cycling network in
        <span class="has-background-info-light px-2 py-1" style="border-radius: 4px"
          >{{ currCity }}, MA</span
        >. The model is targeted towards the needs of children and other vulnerable riders.
      </p>

      <p class="mb-4">The score takes into account:</p>
      <ul>
        <li>the level of separation of the biking infrastructure</li>
        <li>the busyness of the street</li>
        <li>the speed on the street</li>
      </ul>

      <p class="mt-4">
        The parameters are customizable, so they can be fine-tuned to the needs and preferences of
        parents and their children.
      </p>

      <hr class="my-5" />

      <p class="has-text-grey"><strong>Created by:</strong> Dustin Michels</p>
      <p>
        <a
          href="https://github.com/dustinmichels/bike-stress-model"
          target="_blank"
          rel="noopener noreferrer"
          class="button is-small is-light"
        >
          <span class="icon">
            <i class="fab fa-github"></i>
          </span>
          <span>View on GitHub</span>
        </a>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
// Props
interface Props {
  cities: string[]
  currCity: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:currCity': [value: string]
}>()

// Handle city change
const handleCityChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  emit('update:currCity', target.value)
}
</script>

<style scoped>
.about-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.title {
  margin-bottom: 0;
}

.header-row .field {
  margin-bottom: 0;
}

.content {
  flex: 1;
}
</style>
