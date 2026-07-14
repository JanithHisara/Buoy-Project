"""
Live Map page route.
"""
from flask import Blueprint, render_template, session, redirect, url_for

live_map_bp = Blueprint('live_map', __name__)


@live_map_bp.route('/map')
def map_page():
    if 'user' not in session:
        return redirect(url_for('auth.index'))
    return render_template('live_map.html', user=session['user'])
