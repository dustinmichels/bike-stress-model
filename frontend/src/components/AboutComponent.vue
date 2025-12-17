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

      <div class="level is-mobile">
        <div class="level-left">
          <div class="level-item">
            <div class="created-by">
              <span class="has-text-grey-light">Created by</span>
              <a
                href="https://dustinmichels.com/"
                target="_blank"
                rel="noopener noreferrer"
                class="has-text-link"
              >
                Dustin Michels
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
                <i class="fab fa-github"></i>
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

  .header-row .field {
    width: 100%;
  }

  .header-row .select {
    width: 100%;
  }

  .header-row .select select {
    width: 100%;
    font-size: 0.9rem;
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
</style>
