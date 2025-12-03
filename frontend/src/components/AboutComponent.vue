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
  </div>
</template>

<script setup lang="ts">
// About component logic
</script>

<style scoped>
.about-component {
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
}
</style>
