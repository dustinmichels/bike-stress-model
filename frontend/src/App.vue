<template>
  <div class="container is-fluid main-container">
    <div class="columns top-row">
      <div class="column is-two-thirds">
        <MapComponent />
      </div>
      <div class="column is-one-third">
        <AboutComponent />
      </div>
    </div>
    <div class="columns bottom-row">
      <div class="column">
        <ModelComponent />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AboutComponent from './components/AboutComponent.vue'
import MapComponent from './components/MapComponent.vue'
import ModelComponent from './components/ModelComponent.vue'
</script>

<style scoped>
.main-container {
  height: 100vh;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.top-row {
  flex: 3;
  margin: 0 !important;
}

.bottom-row {
  flex: 1;
  margin: 0 !important;
}

.column {
  padding: 0.25rem;
  display: flex;
}
</style>
