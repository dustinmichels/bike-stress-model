<script setup lang="ts">
import {
  Bike,
  BookOpen,
  Car,
  ExternalLink,
  Gauge,
  GitBranch,
  Shield,
  SlidersHorizontal,
  X,
} from '@lucide/vue'
import { nextTick, onUnmounted, useTemplateRef, watch } from 'vue'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const dialogRef = useTemplateRef<HTMLElement>('dialog')
const closeButtonRef = useTemplateRef<HTMLButtonElement>('closeButton')
let previouslyFocused: HTMLElement | null = null
let previousBodyOverflow = ''

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

const close = () => emit('close')

const handleKeydown = (event: KeyboardEvent) => {
  if (!props.isOpen) return

  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }

  if (event.key !== 'Tab' || !dialogRef.value) return

  const focusableElements = Array.from(
    dialogRef.value.querySelectorAll<HTMLElement>(focusableSelector),
  ).filter((element) => element.offsetParent !== null)
  const firstElement = focusableElements[0]
  const lastElement = focusableElements.at(-1)

  if (!firstElement || !lastElement) {
    event.preventDefault()
    dialogRef.value.focus()
    return
  }

  if (event.shiftKey && document.activeElement === firstElement) {
    event.preventDefault()
    lastElement.focus()
  } else if (!event.shiftKey && document.activeElement === lastElement) {
    event.preventDefault()
    firstElement.focus()
  }
}

watch(
  () => props.isOpen,
  async (isOpen) => {
    if (isOpen) {
      previouslyFocused =
        document.activeElement instanceof HTMLElement ? document.activeElement : null
      previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      document.addEventListener('keydown', handleKeydown)
      await nextTick()
      closeButtonRef.value?.focus()
      return
    }

    document.removeEventListener('keydown', handleKeydown)
    document.body.style.overflow = previousBodyOverflow
    previouslyFocused?.focus()
    previouslyFocused = null
  },
)

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (props.isOpen) {
    document.body.style.overflow = previousBodyOverflow
    previouslyFocused?.focus()
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="about-modal">
      <div v-if="isOpen" class="about-modal-overlay" @click.self="close">
        <div
          ref="dialog"
          class="about-modal-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="about-modal-title"
          aria-describedby="about-modal-summary"
          tabindex="-1"
        >
          <header class="about-modal-header">
            <div class="about-modal-heading">
              <Bike :size="22" aria-hidden="true" />
              <span>About this map</span>
            </div>
            <button
              ref="closeButton"
              type="button"
              class="about-modal-close"
              aria-label="Close about dialog"
              @click="close"
            >
              <X :size="22" aria-hidden="true" />
            </button>
          </header>

          <div class="about-modal-scroll" tabindex="0" aria-label="About the bike stress model">
            <section class="about-modal-intro">
              <div class="about-modal-intro-copy">
                <h2 id="about-modal-title" class="about-modal-title">
                  A street-level estimate of cycling stress
                </h2>
                <p id="about-modal-summary" class="about-modal-summary">
                  The map turns OpenStreetMap tags into a 0–4 score for each street segment. It is
                  designed around children and other riders who benefit most from low-stress
                  infrastructure—not as a guarantee that a street is safe.
                </p>
              </div>

              <div class="stress-scale" aria-label="Stress score scale from 0 low to 4 high">
                <div class="stress-scale-labels">
                  <span><strong>0</strong> lower stress</span>
                  <span><strong>4</strong> higher stress</span>
                </div>
                <div class="stress-scale-bar" aria-hidden="true"></div>
                <div class="stress-scale-ticks" aria-hidden="true">
                  <span>0</span><span>1</span><span>2</span><span>3</span><span>4</span>
                </div>
              </div>
            </section>

            <div class="about-modal-body">
              <main class="about-modal-main">
                <section class="about-section" aria-labelledby="score-heading">
                  <h3 id="score-heading" class="about-section-title">How the score is built</h3>
                  <p class="about-section-lede">
                    The default score is a weighted average. Lower numbers indicate conditions the
                    model treats as more comfortable.
                  </p>

                  <div class="factor-list">
                    <div class="factor-row">
                      <span class="factor-icon factor-icon-separation">
                        <Shield :size="19" aria-hidden="true" />
                      </span>
                      <div class="factor-copy">
                        <strong>Separation from traffic</strong>
                        <span
                          >From dedicated paths and tracks to streets with no bike facility.</span
                        >
                      </div>
                      <strong class="factor-weight">60%</strong>
                    </div>
                    <div class="factor-row">
                      <span class="factor-icon factor-icon-speed">
                        <Gauge :size="19" aria-hidden="true" />
                      </span>
                      <div class="factor-copy">
                        <strong>Posted speed</strong>
                        <span>Lower posted speeds receive lower stress scores.</span>
                      </div>
                      <strong class="factor-weight">20%</strong>
                    </div>
                    <div class="factor-row">
                      <span class="factor-icon factor-icon-street">
                        <Car :size="19" aria-hidden="true" />
                      </span>
                      <div class="factor-copy">
                        <strong>Street type</strong>
                        <span
                          >OSM road classes stand in for how busy a street is likely to be.</span
                        >
                      </div>
                      <strong class="factor-weight">20%</strong>
                    </div>
                  </div>
                </section>

                <section class="about-section use-map-section" aria-labelledby="use-heading">
                  <h3 id="use-heading" class="about-section-title">Use the map</h3>
                  <ol class="use-map-list">
                    <li>
                      <span class="step-number">1</span>
                      <span
                        >Choose a city, then select a street segment to inspect its inputs.</span
                      >
                    </li>
                    <li>
                      <span class="step-number">2</span>
                      <span>Drag the weight handles to reflect what matters most to you.</span>
                    </li>
                    <li>
                      <span class="step-number">3</span>
                      <span>
                        Use the eye to isolate one factor and the settings control to change its
                        category scores. The map recalculates immediately.
                      </span>
                    </li>
                  </ol>
                </section>
              </main>

              <aside class="about-modal-aside" aria-label="Model assumptions and limitations">
                <section class="note-block assumption-block">
                  <h3 class="note-title">
                    <SlidersHorizontal :size="18" aria-hidden="true" />
                    Assumptions
                  </h3>
                  <ul class="note-list">
                    <li>OSM tags are treated as useful proxies for conditions on the ground.</li>
                    <li>Separation matters most in the default 60 / 20 / 20 weighting.</li>
                    <li>
                      Untagged residential-class speeds use 20 mph in Cambridge and Somerville and
                      25 mph in Everett and Malden.
                    </li>
                  </ul>
                </section>

                <section class="note-block limitation-block">
                  <h3 class="note-title">Known limitations</h3>
                  <ul class="note-list">
                    <li>
                      Coverage and results inherit missing, outdated, or inconsistent OSM tags.
                    </li>
                    <li>
                      Bike facilities on opposite sides or directions are currently collapsed to the
                      best tagged facility for both directions.
                    </li>
                    <li>
                      Some boundary-crossing paths and bike-permitted footways may be absent from
                      the downloaded network.
                    </li>
                    <li>
                      Missing non-residential speeds are omitted and the remaining factor weights
                      are rebalanced.
                    </li>
                    <li>
                      The model does not measure traffic counts, intersections, lighting, crashes,
                      or real-time conditions. It is not a route planner.
                    </li>
                  </ul>
                </section>
              </aside>
            </div>
          </div>

          <footer class="about-modal-footer">
            <p class="about-modal-footer-copy">Built from a Tufts Advanced GIS project.</p>
            <div class="about-modal-links">
              <a
                href="https://arcg.is/1ziaPD1"
                target="_blank"
                rel="noopener noreferrer"
                class="resource-link resource-link-primary"
              >
                <BookOpen :size="17" aria-hidden="true" />
                <span>Read the original story map</span>
                <ExternalLink :size="14" aria-hidden="true" />
              </a>
              <a
                href="https://github.com/dustinmichels/bike-stress-model/tree/adv-gis"
                target="_blank"
                rel="noopener noreferrer"
                class="resource-link"
              >
                <GitBranch :size="17" aria-hidden="true" />
                <span>View the original code</span>
                <ExternalLink :size="14" aria-hidden="true" />
              </a>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.about-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: grid;
  place-items: center;
  padding: clamp(1rem, 3vw, 2.5rem);
  background: rgba(13, 31, 45, 0.78);
  backdrop-filter: blur(3px);
}

.about-modal-panel {
  width: min(1080px, 100%);
  max-height: calc(100dvh - clamp(2rem, 6vw, 5rem));
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  background: #f7f9fa;
  color: #253746;
  box-shadow: 0 24px 70px rgba(4, 17, 27, 0.38);
}

.about-modal-header {
  flex: 0 0 auto;
  min-height: 58px;
  padding: 0.75rem 1rem 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-bottom: 1px solid #d8e0e6;
  background: #fff;
}

.about-modal-heading {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  color: #173a56;
  font-size: 1.05rem;
  font-weight: 700;
}

.about-modal-close {
  width: 2.5rem;
  height: 2.5rem;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #3f5667;
  cursor: pointer;
}

.about-modal-close:hover {
  background: #edf2f5;
  color: #173a56;
}

.about-modal-close:focus-visible,
.resource-link:focus-visible {
  outline: 3px solid #f4b942;
  outline-offset: 2px;
}

.about-modal-scroll {
  min-height: 0;
  overflow-y: auto;
}

.about-modal-scroll:focus-visible {
  outline: 3px solid #f4b942;
  outline-offset: -3px;
}

.about-modal-intro {
  padding: clamp(1.5rem, 3vw, 2.35rem);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 0.42fr);
  align-items: center;
  gap: clamp(1.5rem, 4vw, 3.5rem);
  background: #173a56;
  color: #fff;
}

.about-modal-title {
  max-width: 18ch;
  margin: 0 0 0.8rem;
  color: #fff;
  font-size: clamp(1.8rem, 4vw, 3rem);
  font-weight: 750;
  line-height: 1.04;
  letter-spacing: -0.035em;
}

.about-modal-summary {
  max-width: 68ch;
  margin: 0;
  color: #d8e7f0;
  font-size: 1rem;
  line-height: 1.6;
}

.stress-scale {
  padding: 1rem 1.1rem 0.9rem;
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: rgba(255, 255, 255, 0.08);
}

.stress-scale-labels,
.stress-scale-ticks {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stress-scale-labels {
  margin-bottom: 0.7rem;
  color: #fff;
  font-size: 0.76rem;
}

.stress-scale-labels span {
  display: inline-flex;
  align-items: baseline;
  gap: 0.3rem;
}

.stress-scale-labels strong {
  font-size: 1.1rem;
}

.stress-scale-bar {
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.7);
  background: linear-gradient(
    90deg,
    #2ca25f 0%,
    #88b14b 25%,
    #d97706 50%,
    #e34a33 75%,
    #b30000 100%
  );
}

.stress-scale-ticks {
  padding-top: 0.35rem;
  color: #c7dbe7;
  font-size: 0.7rem;
}

.about-modal-body {
  padding: clamp(1.35rem, 3vw, 2.25rem);
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(260px, 0.85fr);
  gap: clamp(1.5rem, 3vw, 2.5rem);
}

.about-modal-main,
.about-modal-aside {
  min-width: 0;
}

.about-section + .about-section {
  margin-top: 2rem;
  padding-top: 1.75rem;
  border-top: 1px solid #d8e0e6;
}

.about-section-title,
.note-title {
  margin: 0;
  color: #173a56;
  font-weight: 750;
}

.about-section-title {
  font-size: 1.25rem;
}

.about-section-lede {
  max-width: 65ch;
  margin: 0.45rem 0 1rem;
  color: #5a6b78;
  line-height: 1.55;
}

.factor-list {
  border-top: 1px solid #d8e0e6;
}

.factor-row {
  padding: 0.9rem 0;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.85rem;
  border-bottom: 1px solid #d8e0e6;
}

.factor-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 50%;
}

.factor-icon-separation {
  background: #e2f0fa;
  color: #2373a7;
}

.factor-icon-speed {
  background: #e4f3e8;
  color: #287f4b;
}

.factor-icon-street {
  background: #fff0d2;
  color: #9b6400;
}

.factor-copy {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.factor-copy strong {
  color: #263d4d;
  font-size: 0.96rem;
}

.factor-copy span {
  color: #5f707c;
  font-size: 0.86rem;
  line-height: 1.4;
}

.factor-weight {
  color: #173a56;
  font-size: 1.1rem;
  font-variant-numeric: tabular-nums;
}

.use-map-list {
  margin: 1rem 0 0;
  padding: 0;
  display: grid;
  gap: 0.7rem;
  list-style: none;
}

.use-map-list li {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  align-items: start;
  gap: 0.7rem;
  color: #4b5e6c;
  line-height: 1.5;
}

.step-number {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #173a56;
  color: #fff;
  font-size: 0.78rem;
  font-weight: 700;
}

.about-modal-aside {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.note-block {
  padding: 1.15rem 1.2rem;
  border-left: 4px solid;
  background: #fff;
  box-shadow: 0 1px 0 rgba(29, 56, 75, 0.08);
}

.assumption-block {
  border-color: #3e8ed0;
}

.limitation-block {
  border-color: #d97706;
}

.note-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
}

.note-list {
  margin: 0.8rem 0 0 1rem;
  color: #526573;
  font-size: 0.84rem;
  line-height: 1.48;
}

.note-list li + li {
  margin-top: 0.55rem;
}

.about-modal-footer {
  flex: 0 0 auto;
  padding: 0.9rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-top: 1px solid #d8e0e6;
  background: #fff;
}

.about-modal-footer-copy {
  margin: 0;
  color: #687985;
  font-size: 0.82rem;
}

.about-modal-links {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.resource-link {
  min-height: 38px;
  padding: 0.55rem 0.8rem;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: 1px solid #b9c7d1;
  border-radius: 5px;
  background: #fff;
  color: #245b82;
  font-size: 0.84rem;
  font-weight: 650;
  text-decoration: none;
}

.resource-link:hover {
  border-color: #3e8ed0;
  background: #f0f7fc;
  color: #173a56;
}

.resource-link-primary {
  border-color: #3273dc;
  background: #3273dc;
  color: #fff;
}

.resource-link-primary:hover {
  border-color: #2366d1;
  background: #2366d1;
  color: #fff;
}

.about-modal-enter-active,
.about-modal-leave-active {
  transition: opacity 160ms ease;
}

.about-modal-enter-active .about-modal-panel,
.about-modal-leave-active .about-modal-panel {
  transition: transform 160ms ease;
}

.about-modal-enter-from,
.about-modal-leave-to {
  opacity: 0;
}

.about-modal-enter-from .about-modal-panel,
.about-modal-leave-to .about-modal-panel {
  transform: translateY(8px) scale(0.99);
}

@media screen and (max-width: 820px) {
  .about-modal-body,
  .about-modal-intro {
    grid-template-columns: 1fr;
  }

  .stress-scale {
    max-width: 420px;
  }

  .about-modal-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .about-modal-links {
    width: 100%;
  }

  .resource-link {
    flex: 1;
    justify-content: center;
  }
}

@media screen and (max-width: 560px) {
  .about-modal-overlay {
    padding: 0;
  }

  .about-modal-panel {
    width: 100%;
    height: 100dvh;
    max-height: none;
    border: 0;
    border-radius: 0;
  }

  .about-modal-header {
    padding-left: 1rem;
  }

  .about-modal-intro,
  .about-modal-body {
    padding: 1.25rem 1rem;
  }

  .about-modal-title {
    font-size: 2rem;
  }

  .factor-row {
    grid-template-columns: 36px minmax(0, 1fr);
  }

  .factor-weight {
    grid-column: 2;
    font-size: 0.9rem;
  }

  .about-modal-links {
    align-items: stretch;
    flex-direction: column;
  }

  .resource-link {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .about-modal-enter-active,
  .about-modal-leave-active,
  .about-modal-enter-active .about-modal-panel,
  .about-modal-leave-active .about-modal-panel {
    transition: none;
  }
}
</style>
