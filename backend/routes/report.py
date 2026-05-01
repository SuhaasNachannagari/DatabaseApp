from flask import Blueprint, jsonify, request
from db import get_db

report_bp = Blueprint('report', __name__)


@report_bp.route('/report/recipes', methods=['GET'])
def recipe_report():
    """
    Filterable report for Requirement 2.
    Query params:
      - cuisine       (optional) e.g. "Italian"
      - ingredient_id (optional) filter recipes containing this ingredient
      - min_prep      (optional) minimum prep time in minutes
      - max_prep      (optional) maximum prep time in minutes
      - min_cook      (optional) minimum cook time in minutes
      - max_cook      (optional) maximum cook time in minutes
      - min_rating    (optional) only include recipes with avg rating >= this value
    """
    cuisine = request.args.get('cuisine')
    ingredient_id = request.args.get('ingredient_id', type=int)
    min_prep = request.args.get('min_prep', type=int)
    max_prep = request.args.get('max_prep', type=int)
    min_cook = request.args.get('min_cook', type=int)
    max_cook = request.args.get('max_cook', type=int)
    min_rating = request.args.get('min_rating', type=float)

    conn = get_db()
    cursor = conn.cursor()

    # Build dynamic query — join Reviews to get avg_rating per recipe
    query = '''
        SELECT DISTINCT r.id, r.name, r.cuisine, r.prep_time, r.cook_time, r.servings,
               r.instructions,
               ROUND(AVG(rv.rating), 2) AS avg_rating,
               COUNT(rv.id) AS review_count
        FROM Recipes r
        LEFT JOIN Reviews rv ON r.id = rv.recipe_id
    '''
    params = []

    if ingredient_id:
        query += ' JOIN RecipeIngredients ri ON r.id = ri.recipe_id'

    query += ' WHERE 1=1'

    if cuisine:
        query += ' AND r.cuisine = ?'
        params.append(cuisine)
    if ingredient_id:
        query += ' AND ri.ingredient_id = ?'
        params.append(ingredient_id)
    if min_prep is not None:
        query += ' AND r.prep_time >= ?'
        params.append(min_prep)
    if max_prep is not None:
        query += ' AND r.prep_time <= ?'
        params.append(max_prep)
    if min_cook is not None:
        query += ' AND r.cook_time >= ?'
        params.append(min_cook)
    if max_cook is not None:
        query += ' AND r.cook_time <= ?'
        params.append(max_cook)

    query += ' GROUP BY r.id'

    if min_rating is not None:
        query += ' HAVING avg_rating >= ?'
        params.append(min_rating)

    query += ' ORDER BY avg_rating DESC, r.name'

    cursor.execute(query, params)
    recipes = [dict(row) for row in cursor.fetchall()]

    # Attach ingredients to each recipe
    for recipe in recipes:
        cursor.execute('''
            SELECT i.id, i.name, i.unit, ri.quantity
            FROM RecipeIngredients ri
            JOIN Ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        ''', (recipe['id'],))
        recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]

    # Compute aggregate stats over filtered result set
    if recipes:
        prep_times = [r['prep_time'] for r in recipes]
        cook_times = [r['cook_time'] for r in recipes]
        servings = [r['servings'] for r in recipes]
        ratings = [r['avg_rating'] for r in recipes if r['avg_rating'] is not None]
        stats = {
            'total_recipes': len(recipes),
            'avg_prep_time': round(sum(prep_times) / len(prep_times), 1),
            'avg_cook_time': round(sum(cook_times) / len(cook_times), 1),
            'avg_total_time': round(sum(p + c for p, c in zip(prep_times, cook_times)) / len(recipes), 1),
            'avg_servings': round(sum(servings) / len(servings), 1),
            'avg_rating': round(sum(ratings) / len(ratings), 2) if ratings else None,
        }
    else:
        stats = {
            'total_recipes': 0,
            'avg_prep_time': None,
            'avg_cook_time': None,
            'avg_total_time': None,
            'avg_servings': None,
            'avg_rating': None,
        }

    # Retrieve filter options for building UI dropdowns dynamically
    cursor.execute('SELECT DISTINCT cuisine FROM Recipes ORDER BY cuisine')
    cuisines = [row['cuisine'] for row in cursor.fetchall()]

    cursor.execute('SELECT id, name, category FROM Ingredients ORDER BY category, name')
    all_ingredients = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'filters_applied': {
            'cuisine': cuisine,
            'ingredient_id': ingredient_id,
            'min_prep': min_prep,
            'max_prep': max_prep,
            'min_cook': min_cook,
            'max_cook': max_cook,
            'min_rating': min_rating,
        },
        'stats': stats,
        'recipes': recipes,
        'available_filters': {
            'cuisines': cuisines,
            'ingredients': all_ingredients,
        }
    }), 200