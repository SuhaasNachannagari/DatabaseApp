<script setup>
import { ref, onMounted } from 'vue'

const API = 'http://127.0.0.1:5000'

const cuisineOptions = ref([])
const ingredientOptions = ref([])

const filters = ref({
  cuisine: '',
  ingredient_id: '',
  min_prep: '',
  max_prep: '',
  min_cook: '',
  max_cook: '',
  min_rating: ''
})

const stats = ref(null)
const recipes = ref([])
const loading = ref(false)
const hasSearched = ref(false)

async function fetchReport() {
  loading.value = true
  hasSearched.value = true

  const params = new URLSearchParams()
  if (filters.value.cuisine) params.set('cuisine', filters.value.cuisine)
  if (filters.value.ingredient_id) params.set('ingredient_id', filters.value.ingredient_id)
  if (filters.value.min_prep !== '' && filters.value.min_prep !== null) params.set('min_prep', filters.value.min_prep)
  if (filters.value.max_prep !== '' && filters.value.max_prep !== null) params.set('max_prep', filters.value.max_prep)
  if (filters.value.min_cook !== '' && filters.value.min_cook !== null) params.set('min_cook', filters.value.min_cook)
  if (filters.value.max_cook !== '' && filters.value.max_cook !== null) params.set('max_cook', filters.value.max_cook)
  if (filters.value.min_rating) params.set('min_rating', filters.value.min_rating)

  try {
    const res = await fetch(`${API}/report/recipes?${params.toString()}`)
    const data = await res.json()
    stats.value = data.stats
    recipes.value = data.recipes
    if (data.available_filters) {
      cuisineOptions.value = data.available_filters.cuisines || []
      ingredientOptions.value = data.available_filters.ingredients || []
    }
  } catch (e) {
    console.error('Error fetching report:', e)
  }
  loading.value = false
}

function clearFilters() {
  filters.value = {
    cuisine: '',
    ingredient_id: '',
    min_prep: '',
    max_prep: '',
    min_cook: '',
    max_cook: '',
    min_rating: ''
  }
  fetchReport()
}

function renderStars(rating) {
  const full = Math.round(rating || 0)
  return '★'.repeat(full) + '☆'.repeat(5 - full)
}

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="report-page">
    <div class="page-header">
      <div>
        <h2>Recipe Report</h2>
        <p class="subtitle">Filter and view recipe statistics</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-card" id="report-filters">
      <div class="filters-top">
        <h4>Filters</h4>
        <button class="btn-text" @click="clearFilters">Reset</button>
      </div>

      <div class="filters-grid">
        <div class="filter-group">
          <label>Cuisine</label>
          <select v-model="filters.cuisine" class="form-input" id="filter-cuisine">
            <option value="">All</option>
            <option v-for="c in cuisineOptions" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Ingredient</label>
          <select v-model="filters.ingredient_id" class="form-input" id="filter-ingredient">
            <option value="">Any</option>
            <option v-for="i in ingredientOptions" :key="i.id" :value="i.id">{{ i.name }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Min Prep</label>
          <input v-model.number="filters.min_prep" type="number" min="0" class="form-input" placeholder="—" id="filter-min-prep" />
        </div>
        <div class="filter-group">
          <label>Max Prep</label>
          <input v-model.number="filters.max_prep" type="number" min="0" class="form-input" placeholder="—" id="filter-max-prep" />
        </div>
        <div class="filter-group">
          <label>Min Cook</label>
          <input v-model.number="filters.min_cook" type="number" min="0" class="form-input" placeholder="—" id="filter-min-cook" />
        </div>
        <div class="filter-group">
          <label>Max Cook</label>
          <input v-model.number="filters.max_cook" type="number" min="0" class="form-input" placeholder="—" id="filter-max-cook" />
        </div>
        <div class="filter-group">
          <label>Min Rating</label>
          <select v-model="filters.min_rating" class="form-input" id="filter-min-rating">
            <option value="">Any</option>
            <option value="1">≥ 1</option>
            <option value="2">≥ 2</option>
            <option value="3">≥ 3</option>
            <option value="4">≥ 4</option>
            <option value="5">5</option>
          </select>
        </div>
        <div class="filter-group filter-action">
          <button class="btn btn-primary btn-bouncy" @click="fetchReport" id="btn-apply-filters">Apply Filters</button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div v-if="stats && hasSearched" class="stats-bar" id="report-stats">
      <div class="stat-item stat-highlight">
        <span class="stat-val">{{ stats.total_recipes }}</span>
        <span class="stat-label">Total</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{{ stats.avg_prep_time ?? '—' }}m</span>
        <span class="stat-label">Avg Prep</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{{ stats.avg_cook_time ?? '—' }}m</span>
        <span class="stat-label">Avg Cook</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{{ stats.avg_total_time ?? '—' }}m</span>
        <span class="stat-label">Avg Total</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{{ stats.avg_servings ?? '—' }}</span>
        <span class="stat-label">Avg Servings</span>
      </div>
      <div class="stat-item">
        <span class="stat-val">{{ stats.avg_rating ?? '—' }}</span>
        <span class="stat-label">Avg Rating</span>
      </div>
    </div>

    <!-- Loading -->
    <p v-if="loading" class="muted">Loading report...</p>

    <!-- Results Table -->
    <div v-else-if="hasSearched && recipes.length > 0" class="results-section">
      <h4 class="results-heading">{{ recipes.length }} match{{ recipes.length !== 1 ? 'es' : '' }} found</h4>

      <div class="table-wrapper">
        <table class="results-table" id="report-results-table">
          <thead>
            <tr>
              <th>Recipe</th>
              <th>Cuisine</th>
              <th>Prep</th>
              <th>Cook</th>
              <th>Total</th>
              <th>Servings</th>
              <th>Rating</th>
              <th>Reviews</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in recipes" :key="r.id">
              <td>
                <strong>{{ r.name }}</strong>
                <br><span class="ingredients-preview">{{ r.ingredients.map(i => i.name).join(', ') }}</span>
              </td>
              <td><span class="cuisine-tag">{{ r.cuisine }}</span></td>
              <td>{{ r.prep_time }}m</td>
              <td>{{ r.cook_time }}m</td>
              <td><strong>{{ r.prep_time + r.cook_time }}m</strong></td>
              <td>{{ r.servings }}</td>
              <td>
                <span class="stars stars-sm">{{ renderStars(r.avg_rating) }}</span>
                {{ r.avg_rating ?? '—' }}
              </td>
              <td>{{ r.review_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty -->
    <p v-else-if="hasSearched && recipes.length === 0 && !loading" class="muted">
      No recipes match your filters. Try adjusting or resetting.
    </p>
  </div>
</template>

<style scoped>
.report-page {
  min-height: 100%;
}

.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-family: var(--font-fun);
  font-size: 30px;
  color: var(--color-primary);
}
.subtitle {
  font-family: var(--font-fun);
  font-size: 16px;
  color: var(--color-text-light);
  margin-top: 2px;
}

/* ── Filters ── */
.filters-card {
  background: var(--color-bg-white);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 20px;
}
.filters-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.filters-top h4 {
  font-family: var(--font-fun);
  font-size: 20px;
  color: var(--color-pink);
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  align-items: end;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.filter-group label {
  font-family: var(--font-fun);
  font-size: 15px;
  color: var(--color-text-light);
}
.filter-action {
  display: flex;
  align-items: flex-end;
}
.filter-action .btn {
  width: 100%;
  justify-content: center;
}

.form-input {
  padding: 8px 10px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-family: inherit;
  color: var(--color-text);
  background: #fff;
  outline: none;
  width: 100%;
  transition: border-color 0.15s;
}
.form-input:focus {
  border-color: var(--color-primary);
}

/* ── Stats ── */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  margin-bottom: 24px;
}
.stat-item {
  text-align: center;
  padding: 14px 8px;
  background: var(--color-bg-white);
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  transition: transform 0.15s;
}
.stat-item:hover {
  transform: rotate(-2deg) scale(1.03);
}
.stat-highlight {
  background: var(--color-primary);
  border-color: var(--color-primary);
}
.stat-highlight .stat-val { color: #fff; }
.stat-highlight .stat-label { color: rgba(255,255,255,0.85); }

.stat-val {
  display: block;
  font-family: var(--font-fun);
  font-size: 28px;
  color: var(--color-text);
  margin-bottom: 2px;
}
.stat-label {
  font-family: var(--font-fun);
  font-size: 14px;
  color: var(--color-text-light);
}

/* ── Results ── */
.results-section {
  margin-bottom: 32px;
}
.results-heading {
  font-family: var(--font-fun);
  font-size: 20px;
  margin-bottom: 12px;
  color: var(--color-green);
}

.table-wrapper {
  background: var(--color-bg-white);
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
}
.results-table th {
  padding: 10px 14px;
  font-family: var(--font-fun);
  font-size: 15px;
  color: var(--color-text-light);
  text-align: left;
  background: var(--color-primary-light);
  border-bottom: 2px dashed var(--color-border);
}
.results-table td {
  padding: 12px 14px;
  font-size: 14px;
  border-bottom: 1px dashed var(--color-border);
}
.results-table tbody tr:last-child td {
  border-bottom: none;
}
.results-table tbody tr:hover {
  background: #fef9f0;
}

.ingredients-preview {
  font-size: 12px;
  color: var(--color-text-light);
}

.cuisine-tag {
  display: inline-block;
  padding: 3px 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-family: var(--font-fun);
  font-size: 13px;
  border-radius: 20px;
  border: 1px dashed var(--color-border);
}

.stars {
  color: var(--color-star);
  letter-spacing: 2px;
}
.stars-sm {
  font-size: 14px;
}

/* ── Buttons ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--color-text);
  font-family: var(--font-fun);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn:hover { background: var(--color-primary-light); }
.btn-primary {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.btn-primary:hover { background: var(--color-primary-hover); border-color: var(--color-primary-hover); }
.btn-bouncy:hover {
  transform: scale(1.05) rotate(-1deg);
}

.btn-text {
  background: none;
  border: none;
  color: var(--color-primary);
  font-family: var(--font-fun);
  font-size: 15px;
  cursor: pointer;
  padding: 0;
}
.btn-text:hover { text-decoration: underline; }

.muted {
  color: var(--color-text-light);
  font-family: var(--font-fun);
  font-size: 18px;
  text-align: center;
  padding: 40px 0;
}
</style>
