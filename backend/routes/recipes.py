from flask import Blueprint, jsonify, request
from db import get_db, begin_transaction

recipes_bp = Blueprint('recipes', __name__)


@recipes_bp.route('/recipes', methods=['GET'])
def get_recipes():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id, r.name, r.cuisine, r.prep_time, r.cook_time, r.servings, r.instructions
        FROM Recipes r
        ORDER BY r.name
    ''')
    recipes = [dict(row) for row in cursor.fetchall()]

    # Attach ingredients to each recipe
    for recipe in recipes:
        cursor.execute('''
            SELECT i.id, i.name, i.unit, i.category, ri.quantity
            FROM RecipeIngredients ri
            JOIN Ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        ''', (recipe['id'],))
        recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(recipes), 200


@recipes_bp.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    if not recipe:
        conn.close()
        return jsonify({'error': 'Recipe not found'}), 404

    recipe = dict(recipe)

    cursor.execute('''
        SELECT i.id, i.name, i.unit, i.category, ri.quantity
        FROM RecipeIngredients ri
        JOIN Ingredients i ON ri.ingredient_id = i.id
        WHERE ri.recipe_id = ?
    ''', (recipe_id,))
    recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify(recipe), 200


@recipes_bp.route('/recipes', methods=['POST'])
def create_recipe():
    """
    Transaction Isolation: REPEATABLE READ
    Justification: This is a multi-statement write — INSERT into Recipes
    followed by N INSERTs into RecipeIngredients.  REPEATABLE READ
    prevents non-repeatable reads (another transaction modifying data
    we've already read) and acquires a write lock upfront so no other
    writer can interleave.  We don't need SERIALIZABLE here because
    we are only inserting new rows, so phantom reads are not a concern.
    Guarantees atomicity: either the recipe AND all its ingredient
    links are committed, or none are (rollback on error).
    """
    data = request.get_json()

    required = ['name', 'cuisine', 'prep_time', 'cook_time', 'servings', 'instructions']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        begin_transaction(conn, 'REPEATABLE READ')

        cursor.execute('''
            INSERT INTO Recipes (name, cuisine, prep_time, cook_time, servings, instructions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['cuisine'], data['prep_time'],
              data['cook_time'], data['servings'], data['instructions']))

        recipe_id = cursor.lastrowid

        # Insert ingredients if provided
        ingredients = data.get('ingredients', [])
        for ing in ingredients:
            cursor.execute('''
                INSERT INTO RecipeIngredients (recipe_id, ingredient_id, quantity)
                VALUES (?, ?, ?)
            ''', (recipe_id, ing['ingredient_id'], ing['quantity']))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

    conn.close()
    return jsonify({'message': 'Recipe created', 'id': recipe_id}), 201


@recipes_bp.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """
    Transaction Isolation: REPEATABLE READ
    Justification: The update touches Recipes AND replaces all
    RecipeIngredients rows (DELETE + re-INSERT).  REPEATABLE READ
    acquires a write lock at the start, preventing another writer
    from slipping in between the DELETE and the subsequent INSERTs
    (which would leave the recipe in an inconsistent state with no
    ingredients).  The snapshot is consistent from lock acquisition,
    so we won't see non-repeatable reads.  SERIALIZABLE is not
    needed because we're updating a known, existing recipe by PK.
    """
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Recipes WHERE id = ?', (recipe_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Recipe not found'}), 404

    try:
        begin_transaction(conn, 'REPEATABLE READ')

        # Update recipe fields
        cursor.execute('''
            UPDATE Recipes
            SET name = ?, cuisine = ?, prep_time = ?, cook_time = ?, servings = ?, instructions = ?
            WHERE id = ?
        ''', (data['name'], data['cuisine'], data['prep_time'],
              data['cook_time'], data['servings'], data['instructions'], recipe_id))

        # Replace ingredients: delete old, insert new
        cursor.execute('DELETE FROM RecipeIngredients WHERE recipe_id = ?', (recipe_id,))
        for ing in data.get('ingredients', []):
            cursor.execute('''
                INSERT INTO RecipeIngredients (recipe_id, ingredient_id, quantity)
                VALUES (?, ?, ?)
            ''', (recipe_id, ing['ingredient_id'], ing['quantity']))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

    conn.close()
    return jsonify({'message': 'Recipe updated'}), 200


@recipes_bp.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Recipes WHERE id = ?', (recipe_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Recipe not found'}), 404

    # RecipeIngredients deleted automatically via ON DELETE CASCADE
    cursor.execute('DELETE FROM Recipes WHERE id = ?', (recipe_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Recipe deleted'}), 200