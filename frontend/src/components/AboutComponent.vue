<template>
  <div class="box about-component">
    <h2 class="title is-4">Bike Safety Map - Somerville, MA</h2>
    <div class="content">
      <p>
        This map shows a composite safety score for each segment of the cycling network in
        Somerville, MA. The model is targeted towards the needs of children and other vulnerable
        riders.
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

    <!-- Location Search -->
    <div class="location-search">
      <div class="field has-addons">
        <div class="control is-expanded has-icons-left" :class="{ 'is-loading': isSearching }">
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            @focus="showDropdown = true"
            @blur="onBlur"
            class="input"
            type="text"
            placeholder="Try a different place..."
          />
          <span class="icon is-small is-left">
            <i class="fas fa-search"></i>
          </span>
        </div>
        <div class="control">
          <button class="button is-info" @click="handleSubmit">Submit</button>
        </div>
      </div>

      <!-- Autocomplete Dropdown -->
      <div v-if="showDropdown && suggestions.length > 0" class="dropdown-menu" role="menu">
        <div class="dropdown-content">
          <a
            v-for="suggestion in suggestions"
            :key="suggestion.place_id"
            @mousedown="selectLocation(suggestion)"
            class="dropdown-item"
          >
            <div class="suggestion-item">
              <span class="icon has-text-info">
                <i class="fas fa-map-marker-alt"></i>
              </span>
              <span>{{ suggestion.display_name }}</span>
            </div>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue'

interface NominatimResult {
  place_id: number
  display_name: string
  lat: string
  lon: string
  type: string
  class: string
}

// Define emits
const emit = defineEmits<{
  locationSelected: [location: { lat: number; lon: number; name: string }]
}>()

const searchQuery: Ref<string> = ref('')
const suggestions: Ref<NominatimResult[]> = ref([])
const showDropdown: Ref<boolean> = ref(false)
const isSearching: Ref<boolean> = ref(false)
let searchTimeout: number | null = null

const onSearchInput = () => {
  // Clear existing timeout
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  // Don't search if query is too short
  if (searchQuery.value.trim().length < 3) {
    suggestions.value = []
    showDropdown.value = false
    return
  }

  // Debounce the search
  searchTimeout = window.setTimeout(() => {
    searchLocations()
  }, 300)
}

const searchLocations = async () => {
  const query = searchQuery.value.trim()
  if (query.length < 3) return

  isSearching.value = true

  try {
    // Using Nominatim API with focus on cities
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?` +
        new URLSearchParams({
          q: query,
          format: 'json',
          limit: '5',
          addressdetails: '1',
          featuretype: 'city',
        }),
      {
        headers: {
          'User-Agent': 'BikeSafetyMap/1.0',
        },
      },
    )

    if (response.ok) {
      const data = await response.json()
      suggestions.value = data
      showDropdown.value = data.length > 0
    }
  } catch (error) {
    console.error('Error searching locations:', error)
  } finally {
    isSearching.value = false
  }
}

const selectLocation = (location: NominatimResult) => {
  searchQuery.value = location.display_name
  showDropdown.value = false

  // Emit event to parent component
  emit('locationSelected', {
    name: location.display_name,
    lat: parseFloat(location.lat),
    lon: parseFloat(location.lon),
  })
}

const onBlur = () => {
  // Delay hiding dropdown to allow click events to fire
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

const handleSubmit = () => {
  // TODO: Implement submit functionality
  console.log('Submit clicked')
}
</script>

<style scoped>
.about-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.title {
  margin-bottom: 1rem;
}

.content {
  flex: 1;
}

.location-search {
  margin-top: 1rem;
  position: relative;
}

.dropdown-menu {
  display: block;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  margin-top: 0.25rem;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-content {
  max-height: 300px;
  overflow-y: auto;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dropdown-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: hsl(0, 0%, 96%);
}
</style>
