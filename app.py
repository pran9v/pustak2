from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from models import db, User, Book, Interest, Exchange
from config import Config
from flask_login import logout_user
from flask import redirect, flash
from flask_login import login_required, logout_user
from flask import Flask, render_template
from flask_login import login_required, current_user
from sqlalchemy import and_, not_
from flask import Flask
import os
from werkzeug.utils import secure_filename
from datetime import datetime
# ... other imports ...

app = Flask(__name__)

# Create upload folder path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Flask app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# ... rest of your Flask configuration (SQLAlchemy, Login Manager, etc.) ...
# ... your routes and other code ...

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.password_hash = generate_password_hash(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
            
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    books = Book.query.filter_by(is_available=True).all()
    return render_template('dashboard.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        description = request.form['description']
        image = request.files['image']
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            
            book = Book(
                title=title,
                author=author,
                description=description,
                image_path=filename,
                owner=current_user
            )
            
            db.session.add(book)
            db.session.commit()
            
            flash('Book added successfully')
            return redirect(url_for('dashboard'))
            
    return render_template('add_book.html')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/show_interest/<int:book_id>')
@login_required
def show_interest(book_id):
    book = Book.query.get_or_404(book_id)
    if book.owner_id != current_user.id:
        interest = Interest(user_id=current_user.id, book_id=book_id)
        db.session.add(interest)
        db.session.commit()
        flash('Interest shown successfully')
    return redirect(url_for('dashboard'))

@app.route('/book/<int:book_id>')
@login_required
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    interests = Interest.query.filter_by(book_id=book_id).all()
    return render_template('book_details.html', book=book, interests=interests)

@app.route('/initiate_exchange/<int:book_id>/<int:interest_id>')
@login_required
def initiate_exchange(book_id, interest_id):
    book1 = Book.query.get_or_404(book_id)
    interest = Interest.query.get_or_404(interest_id)
    
    if book1.owner_id == current_user.id:
        exchange = Exchange(
            book1_id=book_id,
            book2_id=interest.book_id,
            user1_id=current_user.id,
            user2_id=interest.user_id
        )
        
        db.session.add(exchange)
        db.session.commit()
        
        flash('Exchange initiated')
    return redirect(url_for('dashboard'))

@app.route('/discover')
@login_required
def discover():
    # Get all books except those owned by the current user
    other_users_books = Book.query.filter(
        Book.owner_id != current_user.id
    ).order_by(Book.created_at.desc()).all()
    
    return render_template('discover.html', books=other_users_books)

# Optional: Add a recommendation system based on user preferences
@app.route('/recommendations')
@login_required
def recommendations():
    # Get books by other users
    other_users_books = Book.query.filter(
        and_(
            Book.owner_id != current_user.id,
            # You can add more filters here based on user preferences
            # For example, books with similar genres or authors
        )
    ).order_by(Book.created_at.desc()).limit(6).all()
    
    return render_template('discover.html', books=other_users_books)

@app.route('/process_payment/<int:exchange_id>')
@login_required
def process_payment(exchange_id):
    exchange = Exchange.query.get_or_404(exchange_id)
    
    if current_user.id == exchange.user1_id:
        exchange.user1_payment = True
    elif current_user.id == exchange.user2_id:
        exchange.user2_payment = True
        
    if exchange.user1_payment and exchange.user2_payment:
        exchange.status = 'completed'
        book1 = Book.query.get(exchange.book1_id)
        book2 = Book.query.get(exchange.book2_id)
        book1.is_available = False
        book2.is_available = False
        
    db.session.commit()
    flash('Payment processed successfully')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)