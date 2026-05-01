<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { computed, ref, onMounted } from 'vue'

const route = useRoute()
const currentRoute = computed(() => route.name)

const isReady = ref(false)
const isWakingUp = ref(false)

onMounted(async () => {
  // If the server takes more than 1 second, show the "waking up" message
  const timer = setTimeout(() => {
    if (!isReady.value) {
      isWakingUp.value = true
    }
  }, 1000)

  try {
    await fetch('https://databaseapp-68wc.onrender.com/greetings')
  } catch (e) {
    console.error('Failed to wake up backend:', e)
  } finally {
    clearTimeout(timer)
    isReady.value = true
    isWakingUp.value = false
  }
})
</script>

<template>
  <div class="app-wrapper">
    <!-- Waking up screen -->
    <div v-if="!isReady && isWakingUp" class="wake-up-screen">
      <div class="loader-content">
        <div class="spinner"></div>
        <h2>Waking up the server...</h2>
        <p>This is hosted on Render's free tier, so it might take up to 50 seconds to spin up from sleep.</p>
        <p>Hang tight! 🍳</p>
      </div>
    </div>

    <!-- Main app -->
    <div v-else-if="isReady">
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

.wake-up-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  background: var(--color-bg-white);
}

.loader-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  max-width: 400px;
  padding: 32px;
  border: 3px dashed var(--color-border);
  border-radius: var(--radius);
  background: var(--color-primary-light);
  transform: rotate(-1deg);
}

.loader-content h2 {
  font-family: var(--font-fun);
  color: var(--color-primary);
  font-size: 28px;
  margin: 0;
}

.loader-content p {
  color: var(--color-text-light);
  line-height: 1.5;
  margin: 0;
  font-size: 15px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px dashed var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
  margin-bottom: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
