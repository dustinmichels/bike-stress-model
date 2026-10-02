<template>
  <div class="box about-component">
    <!-- Title -->
    <div class="header-row">
      <h2 class="title is-4 is-flex is-align-items-center">
        <Bike :size="24" class="mr-2 has-text-primary" />
        <span>Bike Safety Map</span>
      </h2>
    </div>

    <div class="content">
      <p>
        This map shows a composite safety score for each segment of the cycling network in
        <span class="city-select-inline-wrapper"
          ><span class="city-select-wrapper">
            <select
              :value="currCity"
              @change="handleCityChange"
              class="city-select"
              aria-label="Select city"
            >
              <option v-for="city in cities" :key="city" :value="city">{{ city }}, MA</option>
            </select>
            <span class="city-select-arrow" aria-hidden="true">
              <ChevronDown :size="14" />
            </span> </span
          >.</span
        >
        The model is targeted towards the needs of children and other vulnerable riders.
      </p>

      <p class="mb-4">The score takes into account:</p>
      <ul class="factors-list">
        <li>
          <span class="icon is-small has-text-info mr-2">
            <Shield :size="16" />
          </span>
          <span>the level of separation of the biking infrastructure</span>
        </li>
        <li>
          <span class="icon is-small has-text-warning mr-2">
            <Car :size="16" />
          </span>
          <span>the busyness of the street</span>
        </li>
        <li>
          <span class="icon is-small has-text-success mr-2">
            <Gauge :size="16" />
          </span>
          <span>the speed on the street</span>
        </li>
      </ul>

      <p class="mt-4">
        The parameters are customizable, so they can be fine-tuned to the needs and preferences of
        parents and their children.
      </p>

      <hr class="my-5" />

      <div class="level is-mobile">
        <div class="level-left">
          <div class="level-item">
            <div class="created-by">
              <span class="has-text-grey-light">Created by</span>
              <a
                href="https://dustinmichels.com/"
                target="_blank"
                rel="noopener noreferrer"
                class="has-text-link is-inline-flex is-align-items-center"
              >
                <span>Dustin Michels</span>
                <ExternalLink :size="12" class="ml-1" />
              </a>
            </div>
          </div>
        </div>
        <div class="level-right">
          <div class="level-item">
            <a
              href="https://github.com/dustinmichels/bike-stress-model"
              target="_blank"
              rel="noopener noreferrer"
              class="button is-small is-light"
            >
              <span class="icon">
                <GitBranch :size="16" />
              </span>
              <span>View on GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bike, Car, ChevronDown, ExternalLink, Gauge, GitBranch, Shield } from '@lucide/vue'

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

.content {
  flex: 1;
}

.created-by {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.created-by a {
  text-decoration: none;
  font-weight: 500;
}

.created-by a:hover {
  text-decoration: underline;
}
.factors-list {
  list-style: none;
  margin-left: 0 !important;
  padding-left: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.factors-list li {
  display: flex;
  align-items: center;
}

/* Mobile responsiveness */
@media screen and (max-width: 768px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    width: 100%;
  }

  .title {
    font-size: 1.25rem;
  }

  .about-component {
    height: auto;
  }

  .content {
    font-size: 0.9rem;
  }

  .created-by {
    font-size: 0.85rem;
  }
}

.city-select-inline-wrapper {
  white-space: nowrap;
}

.city-select-wrapper {
  display: inline-flex;
  align-items: center;
  position: relative;
  vertical-align: baseline;
}

.city-select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-color: var(--bulma-info-light, #eef6fc);
  color: var(--bulma-info-dark, #1d4ed8);
  font-weight: 600;
  font-size: 0.95em;
  font-family: inherit;
  border: 1px solid rgba(62, 142, 208, 0.3);
  border-radius: 4px;
  padding: 0.1rem 1.35rem 0.1rem 0.45rem;
  cursor: pointer;
  line-height: inherit;
  vertical-align: middle;
  transition:
    background-color 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.city-select:hover {
  background-color: #dbeafe;
  border-color: rgba(62, 142, 208, 0.6);
}

.city-select:focus {
  outline: none;
  border-color: var(--bulma-info, #3e8ed0);
  box-shadow: 0 0 0 2px rgba(62, 142, 208, 0.25);
}

.city-select-arrow {
  position: absolute;
  right: 0.4rem;
  pointer-events: none;
  color: var(--bulma-info, #3e8ed0);
  display: flex;
  align-items: center;
  line-height: 1;
}
</style>
