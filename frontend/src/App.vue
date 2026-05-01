<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const currentRoute = computed(() => route.name)
</script>

<template>
  <div class="app-wrapper">
    <nav class="top-nav">
      <span class="nav-brand">Recipe Manager</span>
      <div class="nav-links">
        <RouterLink to="/" class="nav-link" :class="{ active: currentRoute === 'recipes' }">Recipes</RouterLink>
        <RouterLink to="/report" class="nav-link" :class="{ active: currentRoute === 'report' }">Report</RouterLink>
      </div>
    </nav>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-wrapper {
  min-height: 100vh;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 60px;
  background: var(--color-bg-white);
  border-bottom: 3px dashed var(--color-border);
}

.nav-brand {
  font-family: var(--font-fun);
  font-size: 22px;
  color: var(--color-primary);
}

.nav-links {
  display: flex;
  gap: 6px;
}

.nav-link {
  padding: 8px 16px;
  border-radius: var(--radius);
  font-family: var(--font-fun);
  font-size: 17px;
  color: var(--color-text-light);
  text-decoration: none;
  transition: all 0.2s;
  border: 2px solid transparent;
}
.nav-link:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
  text-decoration: none;
  transform: translateY(-1px);
}
.nav-link.active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border-color: var(--color-primary);
  transform: rotate(-1deg);
}

.main-content {
  padding: 28px 32px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
