import sqlite3
import os

# ──────────────────────────────────────────────────────────────────────
# SQL INJECTION PROTECTION
# ──────────────────────────────────────────────────────────────────────
# This application uses **parameterised queries** (also called prepared
# statements) as its primary defence against SQL injection.  Every
# user-supplied value is passed through SQLite's `?` placeholder
# mechanism — the database driver sends the SQL template and data
# separately, so user input is *never* interpolated into the SQL string.
#
# Examples throughout the codebase:
#   cursor.execute('SELECT * FROM Recipes WHERE id = ?', (recipe_id,))
#   cursor.execute('INSERT INTO Reviews ... VALUES (?, ?, ?, ?)', (...))
#
# Even the dynamic report query in routes/report.py builds its WHERE
# clause with `?` placeholders and a params list — no f-strings or
# string concatenation with user input ever touches the SQL text.
# ──────────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), 'recipes.db')


def get_db():
    """
    Return a database connection configured for manual transaction control.

    WAL (Write-Ahead Logging) mode is enabled so that readers do not
    block writers and vice-versa, which makes the different isolation
    levels meaningful in a concurrent setting.
    """
    conn = sqlite3.connect(DB_PATH, isolation_level=None)  # autocommit mode
    conn.row_factory = sqlite3.Row  # allows dict-like access to rows
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # enable WAL for concurrency
    return conn


def begin_transaction(conn, isolation_level='SERIALIZABLE'):
    """
    Begin a transaction at the given *standard SQL* isolation level.

    Standard SQL Isolation Levels (from weakest to strongest):
    ──────────────────────────────────────────────────────────────
    │ Level              │ Dirty │ Non-repeatable │ Phantom │
    │                    │ Reads │ Reads          │ Reads   │
    ├────────────────────┼───────┼────────────────┼─────────┤
    │ READ UNCOMMITTED   │  Yes  │  Yes           │  Yes    │
    │ READ COMMITTED     │  No   │  Yes           │  Yes    │
    │ REPEATABLE READ    │  No   │  No            │  Yes    │
    │ SERIALIZABLE       │  No   │  No            │  No     │
    ──────────────────────────────────────────────────────────────

    SQLite mapping:
      • READ UNCOMMITTED → BEGIN DEFERRED + PRAGMA read_uncommitted=ON
            Allows reading uncommitted changes from other connections
            (only observable in WAL mode with shared-cache).

      • READ COMMITTED → BEGIN DEFERRED
            SQLite natively prevents dirty reads.  Each statement
            sees only committed data, but a long-running transaction
            might see different data if another commits between
            statements.

      • REPEATABLE READ → BEGIN IMMEDIATE
            Acquires a RESERVED lock immediately, blocking other
            writers.  The transaction sees a consistent snapshot
            from the point the lock is acquired, preventing
            non-repeatable reads.

      • SERIALIZABLE → BEGIN EXCLUSIVE
            Acquires an EXCLUSIVE lock — no other connection can
            read or write.  Transactions are fully serialised,
            preventing dirty reads, non-repeatable reads, and
            phantom reads.  This is the strongest guarantee.

    Must be paired with conn.commit() or conn.rollback().
    """
    level_map = {
        'READ UNCOMMITTED': 'DEFERRED',
        'READ COMMITTED':   'DEFERRED',
        'REPEATABLE READ':  'IMMEDIATE',
        'SERIALIZABLE':     'EXCLUSIVE',
    }

    sqlite_mode = level_map.get(isolation_level, 'EXCLUSIVE')

    # For READ UNCOMMITTED, enable the SQLite pragma that allows
    # reading uncommitted data from other WAL-mode connections.
    if isolation_level == 'READ UNCOMMITTED':
        conn.execute("PRAGMA read_uncommitted = ON")
    else:
        conn.execute("PRAGMA read_uncommitted = OFF")

    conn.execute(f'BEGIN {sqlite_mode}')


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            unit TEXT NOT NULL,
            category TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            prep_time INTEGER NOT NULL,
            cook_time INTEGER NOT NULL,
            servings INTEGER NOT NULL,
            instructions TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS RecipeIngredients (
            recipe_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            PRIMARY KEY (recipe_id, ingredient_id),
            FOREIGN KEY (recipe_id) REFERENCES Recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES Ingredients(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(recipe_id, user_id),
            FOREIGN KEY (recipe_id) REFERENCES Recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
        );

        -- ───────────────────────────────────────────────────────
        -- INDEXES
        -- ───────────────────────────────────────────────────────

        -- IDX 1: idx_recipes_cuisine
        -- Used by: Report "recipe_report" (GET /report/recipes?cuisine=...)
        -- Justification: The recipe report allows filtering by cuisine.
        -- This index turns the `WHERE r.cuisine = ?` predicate from a
        -- full table scan into an index seek.
        CREATE INDEX IF NOT EXISTS idx_recipes_cuisine
            ON Recipes(cuisine);

        -- IDX 2: idx_reviews_recipe_id
        -- Used by: Report "recipe_report" (JOIN Reviews on recipe_id),
        --         Feature GET /recipes/<id>/reviews (WHERE recipe_id = ?),
        --         Feature POST /recipes/<id>/reviews (UNIQUE check)
        -- Justification: Nearly every query that touches Reviews filters
        -- by recipe_id.  The report joins Reviews to compute avg_rating
        -- and review_count per recipe.  The reviews list endpoint
        -- fetches all reviews for one recipe.  Without this index every
        -- such operation is a full scan of the Reviews table.
        CREATE INDEX IF NOT EXISTS idx_reviews_recipe_id
            ON Reviews(recipe_id);

        -- IDX 3: idx_reviews_user_id
        -- Used by: Feature POST /recipes/<id>/reviews (user existence
        --         check + UNIQUE(recipe_id, user_id) enforcement)
        -- Justification: When a new review is submitted the app checks
        -- `SELECT id FROM Users WHERE id = ?` and SQLite enforces the
        -- UNIQUE(recipe_id, user_id) constraint.  An index on user_id
        -- speeds up both the FK check and uniqueness enforcement.
        CREATE INDEX IF NOT EXISTS idx_reviews_user_id
            ON Reviews(user_id);

        -- IDX 4: idx_recipe_ingredients_ingredient_id
        -- Used by: Report "recipe_report" (filter by ingredient_id),
        --         Feature GET /recipes (ingredient list per recipe)
        -- Justification: The report filters recipes that contain a
        -- specific ingredient via `JOIN RecipeIngredients ri … WHERE
        -- ri.ingredient_id = ?`.  The primary key covers (recipe_id,
        -- ingredient_id) but lookups starting from ingredient_id need
        -- this secondary index.
        CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_ingredient_id
            ON RecipeIngredients(ingredient_id);

        -- IDX 5: idx_recipes_prep_time
        -- Used by: Report "recipe_report" (WHERE r.prep_time >= ? / <= ?)
        -- Justification: The report supports min_prep / max_prep range
        -- filters.  An index on prep_time allows SQLite to use a range
        -- scan instead of a full table scan when those filters are active.
        CREATE INDEX IF NOT EXISTS idx_recipes_prep_time
            ON Recipes(prep_time);

        -- IDX 6: idx_recipes_cook_time
        -- Used by: Report "recipe_report" (WHERE r.cook_time >= ? / <= ?)
        -- Justification: Same rationale as prep_time — supports the
        -- min_cook / max_cook range filters in the report.
        CREATE INDEX IF NOT EXISTS idx_recipes_cook_time
            ON Recipes(cook_time);
    ''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # Only seed if empty
    cursor.execute("SELECT COUNT(*) FROM Recipes")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed Users
    cursor.executemany("INSERT INTO Users (name, email) VALUES (?, ?)", [
        ("Gordon Ramsay", "gordon@example.com"),
        ("Hisham Benotman", "hisham@example.com"),
        ("Braden Smith", "braden@example.com"),
        ("Bob", "bob@example.com"),
    ])

    # Seed Ingredients
    cursor.executemany("INSERT INTO Ingredients (name, unit, category) VALUES (?, ?, ?)", [
        ("Chicken Breast", "grams", "Protein"),
        ("Olive Oil", "tbsp", "Fat"),
        ("Garlic", "cloves", "Vegetable"),
        ("Pasta", "grams", "Grain"),
        ("Tomato Sauce", "cups", "Sauce"),
        ("Parmesan Cheese", "grams", "Dairy"),
        ("Eggs", "count", "Protein"),
        ("Flour", "cups", "Grain"),
        ("Milk", "cups", "Dairy"),
        ("Butter", "tbsp", "Fat"),
        ("Onion", "count", "Vegetable"),
        ("Bell Pepper", "count", "Vegetable"),
    ])

    # Seed Recipes
    cursor.executemany("""
        INSERT INTO Recipes (name, cuisine, prep_time, cook_time, servings, instructions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ("Spaghetti Marinara", "Italian", 10, 20, 4,
         "1. Boil pasta. 2. Heat olive oil and saute garlic. 3. Add tomato sauce and simmer. 4. Toss with pasta and top with parmesan."),
        ("Garlic Chicken", "American", 15, 30, 2,
         "1. Season chicken with salt and pepper. 2. Heat olive oil in pan. 3. Cook chicken 6 min per side. 4. Add garlic and butter, baste for 2 minutes."),
        ("Veggie Omelette", "French", 5, 10, 1,
         "1. Whisk eggs with salt. 2. Heat butter in pan. 3. Pour in eggs, cook until set. 4. Add diced bell pepper and onion, fold omelette."),
        ("Chicken Pasta", "Italian", 15, 25, 3,
         "1. Cook pasta. 2. Saute garlic and onion in olive oil. 3. Add chicken and cook through. 4. Add tomato sauce, simmer. 5. Toss with pasta and parmesan."),
        ("Pancakes", "American", 10, 15, 4,
         "1. Mix flour, eggs, milk into batter. 2. Heat buttered pan. 3. Pour batter, cook until bubbles form. 4. Flip and cook 1 more minute."),
    ])

    # Seed RecipeIngredients (recipe_id, ingredient_id, quantity)
    cursor.executemany("INSERT INTO RecipeIngredients (recipe_id, ingredient_id, quantity) VALUES (?, ?, ?)", [
        # Spaghetti Marinara (id=1)
        (1, 4, 200),  # Pasta
        (1, 2, 2),    # Olive Oil
        (1, 3, 3),    # Garlic
        (1, 5, 1.5),  # Tomato Sauce
        (1, 6, 50),   # Parmesan

        # Garlic Chicken (id=2)
        (2, 1, 400),  # Chicken Breast
        (2, 2, 2),    # Olive Oil
        (2, 3, 4),    # Garlic
        (2, 10, 2),   # Butter

        # Veggie Omelette (id=3)
        (3, 7, 3),    # Eggs
        (3, 10, 1),   # Butter
        (3, 12, 1),   # Bell Pepper
        (3, 11, 0.5), # Onion

        # Chicken Pasta (id=4)
        (4, 1, 300),  # Chicken Breast
        (4, 4, 200),  # Pasta
        (4, 2, 2),    # Olive Oil
        (4, 3, 3),    # Garlic
        (4, 11, 1),   # Onion
        (4, 5, 1),    # Tomato Sauce
        (4, 6, 40),   # Parmesan

        # Pancakes (id=5)
        (5, 8, 2),    # Flour
        (5, 7, 2),    # Eggs
        (5, 9, 1),    # Milk
        (5, 10, 2),   # Butter
    ])

    # Seed Reviews (recipe_id, user_id, rating, comment)
    cursor.executemany("""
        INSERT INTO Reviews (recipe_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
    """, [
        (1, 1, 5, "Finally, a pasta that doesn't make me scream."),
        (1, 3, 4, "Pretty solid, reminds me of dining hall food but better."),
        (1, 4, 4, "Good stuff."),
        (2, 2, 5, "The garlic was perfect, very well balanced."),
        (2, 4, 3, "It was alright."),
        (3, 3, 2, "Not my favorite, a bit bland honestly."),
        (3, 1, 4, "Simple, elegant, no drama. Unlike me."),
        (4, 4, 5, "Best pasta I've ever had. And I'm Bob."),
        (4, 2, 4, "Solid recipe, the parmesan really ties it together."),
        (4, 3, 3, "Decent but I've had better chicken pasta."),
        (5, 4, 5, "Pancakes are pancakes. These are good pancakes."),
        (5, 1, 4, "Fluffy, decent. Would plate them more aggressively."),
    ])

    conn.commit()
    conn.close()
    print("Database seeded successfully.")

def seed_reviews(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Reviews")
    if cursor.fetchone()[0] > 0:
        return
    cursor.executemany("""
        INSERT INTO Reviews (recipe_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
    """, [
        (1, 1, 5, "Finally, a pasta that doesn't make me scream."),
        (1, 3, 4, "Pretty solid, reminds me of dining hall food but better."),
        (1, 4, 4, "Good stuff."),
        (2, 2, 5, "The garlic was perfect, very well balanced."),
        (2, 4, 3, "It was alright."),
        (3, 3, 2, "Not my favorite, a bit bland honestly."),
        (3, 1, 4, "Simple, elegant, no drama. Unlike me."),
        (4, 4, 5, "Best pasta I've ever had. And I'm Bob."),
        (4, 2, 4, "Solid recipe, the parmesan really ties it together."),
        (4, 3, 3, "Decent but I've had better chicken pasta."),
        (5, 4, 5, "Pancakes are pancakes. These are good pancakes."),
        (5, 1, 4, "Fluffy, decent. Would plate them more aggressively."),
    ])
    conn.commit()