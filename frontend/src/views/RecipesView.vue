<script setup>
import { ref, onMounted } from 'vue'

const API = 'http://127.0.0.1:5000'

const recipes = ref([])
const ingredients = ref([])
const users = ref([])

const selectedRecipe = ref(null)
const reviews = ref([])
const reviewStats = ref(null)

const showForm = ref(false)
const editingRecipe = ref(null)

const form = ref(createEmptyForm())

function createEmptyForm() {
  return {
    name: '',
    cuisine: '',
    prep_time: '',
    cook_time: '',
    servings: '',
    instructions: '',
    ingredients: [{ ingredient_id: '', quantity: '' }]
  }
}

const reviewForm = ref({ user_id: '', rating: 0, comment: '' })
const editingReview = ref(null)
const deleteConfirm = ref(null)
const deleteReviewConfirm = ref(null)
const loadingRecipes = ref(true)
const recipeRatings = ref({})

async function fetchRecipes() {
  loadingRecipes.value = true
  try {
    const res = await fetch(`${API}/recipes`)
    recipes.value = await res.json()
    for (const r of recipes.value) {
      const rv = await fetch(`${API}/recipes/${r.id}/reviews`)
      const data = await rv.json()
      recipeRatings.value[r.id] = data.stats
    }
  } catch (e) {
    console.error('Failed to fetch recipes:', e)
  }
  loadingRecipes.value = false
}

async function fetchIngredients() {
  const res = await fetch(`${API}/ingredients`)
  ingredients.value = await res.json()
}

async function fetchUsers() {
  const res = await fetch(`${API}/users`)
  users.value = await res.json()
}

async function selectRecipe(recipe) {
  selectedRecipe.value = recipe
  await fetchReviews(recipe.id)
}

async function fetchReviews(recipeId) {
  const res = await fetch(`${API}/recipes/${recipeId}/reviews`)
  const data = await res.json()
  reviews.value = data.reviews
  reviewStats.value = data.stats
  recipeRatings.value[recipeId] = data.stats
}

function openNewForm() {
  editingRecipe.value = null
  form.value = createEmptyForm()
  showForm.value = true
}

function openEditForm(recipe) {
  editingRecipe.value = recipe
  form.value = {
    name: recipe.name,
    cuisine: recipe.cuisine,
    prep_time: recipe.prep_time,
    cook_time: recipe.cook_time,
    servings: recipe.servings,
    instructions: recipe.instructions,
    ingredients: recipe.ingredients.map(i => ({
      ingredient_id: i.id,
      quantity: i.quantity
    }))
  }
  if (form.value.ingredients.length === 0) {
    form.value.ingredients.push({ ingredient_id: '', quantity: '' })
  }
  showForm.value = true
}

async function saveRecipe() {
  const payload = {
    name: form.value.name,
    cuisine: form.value.cuisine,
    prep_time: parseInt(form.value.prep_time),
    cook_time: parseInt(form.value.cook_time),
    servings: parseInt(form.value.servings),
    instructions: form.value.instructions,
    ingredients: form.value.ingredients
      .filter(i => i.ingredient_id && i.quantity)
      .map(i => ({
        ingredient_id: parseInt(i.ingredient_id),
        quantity: parseFloat(i.quantity)
      }))
  }

  if (editingRecipe.value) {
    await fetch(`${API}/recipes/${editingRecipe.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  } else {
    await fetch(`${API}/recipes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  }

  showForm.value = false
  await fetchRecipes()
  if (selectedRecipe.value && editingRecipe.value && editingRecipe.value.id === selectedRecipe.value.id) {
    const updated = recipes.value.find(r => r.id === selectedRecipe.value.id)
    if (updated) selectedRecipe.value = updated
  }
}

async function deleteRecipe(id) {
  await fetch(`${API}/recipes/${id}`, { method: 'DELETE' })
  deleteConfirm.value = null
  if (selectedRecipe.value && selectedRecipe.value.id === id) {
    selectedRecipe.value = null
    reviews.value = []
    reviewStats.value = null
  }
  await fetchRecipes()
}

function addIngredientRow() {
  form.value.ingredients.push({ ingredient_id: '', quantity: '' })
}
function removeIngredientRow(idx) {
  form.value.ingredients.splice(idx, 1)
}

// ── New Ingredient Creation ──
const showNewIngredient = ref(false)
const newIngredient = ref({ name: '', unit: '', category: '' })

async function createIngredient() {
  if (!newIngredient.value.name || !newIngredient.value.unit || !newIngredient.value.category) return
  try {
    const res = await fetch(`${API}/ingredients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newIngredient.value)
    })
    const data = await res.json()
    if (res.ok) {
      await fetchIngredients()
      newIngredient.value = { name: '', unit: '', category: '' }
      showNewIngredient.value = false
    } else {
      alert(data.error || 'Failed to create ingredient')
    }
  } catch (e) {
    console.error('Failed to create ingredient:', e)
  }
}

async function submitReview() {
  const payload = {
    user_id: parseInt(reviewForm.value.user_id),
    rating: reviewForm.value.rating,
    comment: reviewForm.value.comment || null
  }
  if (editingReview.value) {
    await fetch(`${API}/reviews/${editingReview.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    editingReview.value = null
  } else {
    await fetch(`${API}/recipes/${selectedRecipe.value.id}/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
  }
  reviewForm.value = { user_id: '', rating: 0, comment: '' }
  await fetchReviews(selectedRecipe.value.id)
}

function editReview(review) {
  editingReview.value = review
  reviewForm.value = {
    user_id: review.user_id,
    rating: review.rating,
    comment: review.comment || ''
  }
}

function cancelEditReview() {
  editingReview.value = null
  reviewForm.value = { user_id: '', rating: 0, comment: '' }
}

async function deleteReview(id) {
  await fetch(`${API}/reviews/${id}`, { method: 'DELETE' })
  deleteReviewConfirm.value = null
  await fetchReviews(selectedRecipe.value.id)
}

function renderStars(rating) {
  const full = Math.round(rating || 0)
  return '★'.repeat(full) + '☆'.repeat(5 - full)
}

// Fun random tilts for cards
function cardTilt(index) {
  const tilts = [-1.5, 0.8, -0.5, 1.2, -1, 0.6, -0.8, 1.5]
  return tilts[index % tilts.length]
}

onMounted(() => {
  fetchRecipes()
  fetchIngredients()
  fetchUsers()
})
</script>

<template>
  <div class="recipes-page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h2>My Recipes</h2>
        <p class="subtitle">Create, edit, and manage your recipes</p>
      </div>
      <button class="btn btn-primary btn-bouncy" @click="openNewForm" id="btn-new-recipe">+ New Recipe</button>
    </div>

    <div class="content-layout">
      <!-- Recipe List -->
      <section class="recipe-list-section">
        <p v-if="loadingRecipes" class="muted">Loading recipes...</p>
        <p v-else-if="recipes.length === 0" class="muted">No recipes yet. Create one!</p>

        <div v-else class="recipe-grid">
          <div
            v-for="(recipe, idx) in recipes"
            :key="recipe.id"
            class="recipe-card"
            :class="{ selected: selectedRecipe && selectedRecipe.id === recipe.id }"
            :style="{ transform: `rotate(${cardTilt(idx)}deg)` }"
            @click="selectRecipe(recipe)"
            :id="'recipe-card-' + recipe.id"
          >
            <div class="card-top-row">
              <span class="cuisine-tag">{{ recipe.cuisine }}</span>
              <span class="card-btns">
                <button class="btn-text" @click.stop="openEditForm(recipe)">Edit</button>
                <button class="btn-text btn-text-danger" @click.stop="deleteConfirm = recipe.id">Delete</button>
              </span>
            </div>

            <h3 class="card-name">{{ recipe.name }}</h3>

            <div v-if="recipeRatings[recipe.id]" class="card-rating">
              <span class="stars">{{ renderStars(recipeRatings[recipe.id].avg_rating) }}</span>
              <span class="rating-text">{{ recipeRatings[recipe.id].avg_rating ?? '—' }} ({{ recipeRatings[recipe.id].review_count }})</span>
            </div>

            <div class="card-meta">
              <span>Prep: {{ recipe.prep_time }}m</span>
              <span>Cook: {{ recipe.cook_time }}m</span>
              <span>{{ recipe.servings }} servings</span>
            </div>

            <!-- Delete Confirmation -->
            <div v-if="deleteConfirm === recipe.id" class="delete-overlay" @click.stop>
              <p>Delete "{{ recipe.name }}"?</p>
              <div class="delete-btns">
                <button class="btn btn-sm" @click.stop="deleteConfirm = null">Cancel</button>
                <button class="btn btn-sm btn-danger" @click.stop="deleteRecipe(recipe.id)">Delete</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Detail Panel -->
      <aside v-if="selectedRecipe" class="detail-panel">
        <div class="detail-top">
          <h3>{{ selectedRecipe.name }}</h3>
          <button class="btn-text" @click="selectedRecipe = null; reviews = []; reviewStats = null">Close</button>
        </div>
        <span class="cuisine-tag">{{ selectedRecipe.cuisine }}</span>

        <div class="detail-meta">
          <span>Prep: {{ selectedRecipe.prep_time }}m</span>
          <span>Cook: {{ selectedRecipe.cook_time }}m</span>
          <span>Total: {{ selectedRecipe.prep_time + selectedRecipe.cook_time }}m</span>
          <span>{{ selectedRecipe.servings }} servings</span>
        </div>

        <!-- Ingredients -->
        <div class="detail-section">
          <h4>Ingredients</h4>
          <ul class="ing-list">
            <li v-for="ing in selectedRecipe.ingredients" :key="ing.id">
              {{ ing.quantity }} {{ ing.unit }} — {{ ing.name }}
            </li>
          </ul>
        </div>

        <!-- Instructions -->
        <div class="detail-section">
          <h4>Instructions</h4>
          <p class="instructions-text">{{ selectedRecipe.instructions }}</p>
        </div>

        <!-- Reviews -->
        <div class="detail-section">
          <h4>
            Reviews
            <span v-if="reviewStats" class="review-summary">
              ({{ reviewStats.avg_rating ?? '—' }} avg · {{ reviewStats.review_count }} reviews)
            </span>
          </h4>

          <p v-if="reviews.length === 0" class="muted">No reviews yet.</p>

          <div v-else class="review-list">
            <div v-for="rev in reviews" :key="rev.id" class="review-item">
              <div class="review-header">
                <strong>{{ rev.user_name }}</strong>
                <span class="stars stars-sm">{{ renderStars(rev.rating) }}</span>
                <span class="review-actions">
                  <button class="btn-text btn-text-sm" @click="editReview(rev)">Edit</button>
                  <button class="btn-text btn-text-sm btn-text-danger" @click="deleteReviewConfirm = rev.id">Delete</button>
                </span>
              </div>
              <p v-if="rev.comment" class="review-comment">{{ rev.comment }}</p>
              <span class="review-date">{{ rev.created_at }}</span>

              <div v-if="deleteReviewConfirm === rev.id" class="review-delete-bar">
                <span>Delete this review?</span>
                <button class="btn btn-xs" @click="deleteReviewConfirm = null">Cancel</button>
                <button class="btn btn-xs btn-danger" @click="deleteReview(rev.id)">Delete</button>
              </div>
            </div>
          </div>

          <!-- Add/Edit Review -->
          <div class="review-form">
            <h5>{{ editingReview ? 'Edit Review' : 'Add a Review' }}</h5>

            <div class="form-row">
              <select v-model="reviewForm.user_id" class="form-input" :disabled="!!editingReview" id="review-user-select">
                <option value="" disabled>Select user</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }}</option>
              </select>
            </div>

            <div class="form-row star-picker">
              <span>Rating:</span>
              <span
                v-for="s in 5"
                :key="s"
                class="star-btn"
                :class="{ active: s <= reviewForm.rating }"
                @click="reviewForm.rating = s"
              >{{ s <= reviewForm.rating ? '★' : '☆' }}</span>
            </div>

            <div class="form-row">
              <textarea
                v-model="reviewForm.comment"
                class="form-input"
                placeholder="Optional comment..."
                rows="2"
              ></textarea>
            </div>

            <div class="form-row form-actions">
              <button v-if="editingReview" class="btn btn-sm" @click="cancelEditReview">Cancel</button>
              <button
                class="btn btn-sm btn-primary"
                @click="submitReview"
                :disabled="!reviewForm.user_id || reviewForm.rating === 0"
              >{{ editingReview ? 'Update' : 'Submit' }}</button>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Recipe Form Modal -->
    <Teleport to="body">
      <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
        <div class="modal" id="recipe-form-modal">
          <div class="modal-header">
            <h3>{{ editingRecipe ? 'Edit Recipe' : 'New Recipe' }}</h3>
            <button class="btn-text" @click="showForm = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-grid">
              <div class="form-group full-width">
                <label>Recipe Name</label>
                <input v-model="form.name" class="form-input" placeholder="e.g. Grandma's Spaghetti" id="input-recipe-name" />
              </div>
              <div class="form-group">
                <label>Cuisine</label>
                <input v-model="form.cuisine" class="form-input" placeholder="e.g. Italian" id="input-cuisine" />
              </div>
              <div class="form-group">
                <label>Servings</label>
                <input v-model="form.servings" type="number" min="1" class="form-input" id="input-servings" />
              </div>
              <div class="form-group">
                <label>Prep Time (min)</label>
                <input v-model="form.prep_time" type="number" min="0" class="form-input" id="input-prep-time" />
              </div>
              <div class="form-group">
                <label>Cook Time (min)</label>
                <input v-model="form.cook_time" type="number" min="0" class="form-input" id="input-cook-time" />
              </div>
              <div class="form-group full-width">
                <label>Instructions</label>
                <textarea v-model="form.instructions" class="form-input" rows="3" placeholder="Step-by-step instructions..." id="input-instructions"></textarea>
              </div>
            </div>

            <!-- Ingredients -->
            <div class="ing-section">
              <div class="ing-header">
                <h4>Ingredients</h4>
                <div class="ing-header-actions">
                  <button class="btn-text" @click="showNewIngredient = !showNewIngredient">{{ showNewIngredient ? 'Cancel' : '+ New Ingredient' }}</button>
                  <button class="btn-text" @click="addIngredientRow">+ Add Row</button>
                </div>
              </div>

              <!-- New Ingredient Form -->
              <div v-if="showNewIngredient" class="new-ing-form">
                <div class="new-ing-fields">
                  <input v-model="newIngredient.name" class="form-input" placeholder="Name (e.g. Basil)" />
                  <input v-model="newIngredient.unit" class="form-input" placeholder="Unit (e.g. grams)" />
                  <input v-model="newIngredient.category" class="form-input" placeholder="Category (e.g. Herb)" />
                  <button
                    class="btn btn-sm btn-primary"
                    @click="createIngredient"
                    :disabled="!newIngredient.name || !newIngredient.unit || !newIngredient.category"
                  >Create</button>
                </div>
              </div>

              <div v-for="(ing, idx) in form.ingredients" :key="idx" class="ing-row">
                <select v-model="ing.ingredient_id" class="form-input ing-select">
                  <option value="" disabled>Select ingredient</option>
                  <option v-for="opt in ingredients" :key="opt.id" :value="opt.id">
                    {{ opt.name }} ({{ opt.unit }})
                  </option>
                </select>
                <input v-model="ing.quantity" type="number" min="0" step="0.1" class="form-input qty-input" placeholder="Qty" />
                <button class="btn-text btn-text-danger" @click="removeIngredientRow(idx)" :disabled="form.ingredients.length === 1">✕</button>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn" @click="showForm = false">Cancel</button>
            <button class="btn btn-primary btn-bouncy" @click="saveRecipe" id="btn-save-recipe">
              {{ editingRecipe ? 'Save Changes' : 'Create Recipe' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.recipes-page {
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
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

/* ── Layout ── */
.content-layout {
  display: flex;
  gap: 24px;
}
.recipe-list-section {
  flex: 1;
  min-width: 0;
}
.detail-panel {
  width: 380px;
  min-width: 380px;
  background: var(--color-bg-white);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius);
  padding: 20px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  position: sticky;
  top: 80px;
}

/* ── Recipe Grid ── */
.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}

.recipe-card {
  position: relative;
  background: var(--color-bg-white);
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.recipe-card:hover {
  border-color: var(--color-primary);
  transform: rotate(0deg) scale(1.02) !important;
  box-shadow: 4px 4px 0 var(--color-primary-light);
}
.recipe-card.selected {
  border-color: var(--color-primary);
  box-shadow: 4px 4px 0 var(--color-primary-light);
  transform: rotate(0deg) !important;
}

.card-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
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

.card-btns {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.15s;
}
.recipe-card:hover .card-btns {
  opacity: 1;
}

.card-name {
  font-family: var(--font-fun);
  font-size: 20px;
  margin-bottom: 6px;
  color: var(--color-text);
}

.card-rating {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}
.stars {
  color: var(--color-star);
  letter-spacing: 2px;
  font-size: 16px;
}
.stars-sm {
  font-size: 14px;
}
.rating-text {
  font-size: 13px;
  color: var(--color-text-light);
}

.card-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: var(--color-text-light);
  font-family: var(--font-fun);
  font-size: 14px;
}

/* Delete overlay */
.delete-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 248, 240, 0.96);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-radius: var(--radius);
  z-index: 5;
}
.delete-overlay p {
  font-family: var(--font-fun);
  font-size: 16px;
}
.delete-btns {
  display: flex;
  gap: 8px;
}

/* ── Detail Panel ── */
.detail-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.detail-top h3 {
  font-family: var(--font-fun);
  font-size: 24px;
  color: var(--color-primary);
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 14px;
  font-family: var(--font-fun);
  color: var(--color-text-light);
  margin: 12px 0 16px;
  padding-bottom: 16px;
  border-bottom: 2px dashed var(--color-border);
}

.detail-section {
  margin-bottom: 20px;
}
.detail-section h4 {
  font-family: var(--font-fun);
  font-size: 18px;
  margin-bottom: 8px;
  color: var(--color-pink);
}
.review-summary {
  font-weight: 400;
  font-size: 14px;
  color: var(--color-text-light);
}

.ing-list {
  list-style: none;
  padding: 0;
}
.ing-list li {
  padding: 5px 0;
  border-bottom: 1px dashed var(--color-border);
  font-size: 14px;
}
.ing-list li:last-child {
  border-bottom: none;
}

.instructions-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-light);
}

/* ── Reviews ── */
.review-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}
.review-item {
  padding: 12px;
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--color-border);
}
.review-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.review-actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
}
.review-comment {
  font-size: 13px;
  color: var(--color-text-light);
  margin: 4px 0;
}
.review-date {
  font-size: 11px;
  color: #bbb;
}
.review-delete-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border);
  font-family: var(--font-fun);
  font-size: 14px;
  color: var(--color-danger);
}

/* Review Form */
.review-form {
  padding: 14px;
  background: var(--color-bg-white);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius);
}
.review-form h5 {
  font-family: var(--font-fun);
  font-size: 16px;
  margin-bottom: 10px;
  color: var(--color-primary);
}
.form-row {
  margin-bottom: 8px;
}
.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.star-picker {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-family: var(--font-fun);
  font-size: 16px;
}
.star-btn {
  cursor: pointer;
  font-size: 24px;
  color: var(--color-star-empty);
  transition: transform 0.15s;
}
.star-btn:hover {
  transform: scale(1.3) rotate(10deg);
}
.star-btn.active {
  color: var(--color-star);
}

/* ── Modal ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(61, 44, 94, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--color-bg-white);
  border: 3px solid var(--color-primary);
  border-radius: var(--radius);
  width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  transform: rotate(-0.5deg);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}
.modal-header h3 {
  font-family: var(--font-fun);
  font-size: 22px;
  color: var(--color-primary);
}
.modal-body {
  padding: 16px 24px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 24px 20px;
  border-top: 2px dashed var(--color-border);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.full-width {
  grid-column: span 2;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-group label {
  font-family: var(--font-fun);
  font-size: 15px;
  color: var(--color-text-light);
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

.ing-section {
  margin-top: 16px;
}
.ing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.ing-header h4 {
  font-family: var(--font-fun);
  font-size: 18px;
  color: var(--color-pink);
}
.ing-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.ing-select { flex: 2; }
.qty-input { flex: 1; max-width: 90px; }

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

.btn-danger {
  background: var(--color-danger);
  color: #fff;
  border-color: var(--color-danger);
}
.btn-danger:hover { background: var(--color-danger-hover); }

.btn-bouncy:hover {
  transform: scale(1.05) rotate(-1deg);
}

.btn-sm { padding: 5px 12px; font-size: 14px; }
.btn-xs { padding: 3px 8px; font-size: 13px; }

/* New Ingredient Form */
.ing-header-actions {
  display: flex;
  gap: 12px;
}
.new-ing-form {
  margin-bottom: 12px;
  padding: 12px;
  background: var(--color-primary-light);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
}
.new-ing-fields {
  display: flex;
  gap: 8px;
  align-items: center;
}
.new-ing-fields .form-input {
  flex: 1;
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
.btn-text-danger { color: var(--color-danger); }
.btn-text-sm { font-size: 13px; }

.muted {
  color: var(--color-text-light);
  font-family: var(--font-fun);
  font-size: 18px;
  padding: 40px 0;
  text-align: center;
}
</style>
