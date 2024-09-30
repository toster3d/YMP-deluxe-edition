from flask import Blueprint, render_template

# Inicjalizacja blueprintu
main_bp = Blueprint('main', __name__, 
                    template_folder='../templates',
                    static_folder='../static',
                    static_url_path='/static')

@main_bp.route('/')
@main_bp.route('/index')
def index():
    return render_template('index.html')



