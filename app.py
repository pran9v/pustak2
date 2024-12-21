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
from models import db, User, Book, BookExchangeRequest
from sqlalchemy.orm import relationship, joinedload


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

@app.route('/show_interest/<int:book_id>', methods=['GET', 'POST'])
@login_required
def show_interest(book_id):
    book = Book.query.get_or_404(book_id)
    user_books = Book.query.filter_by(owner_id=current_user.id, is_available=True).all()
    
    if request.method == 'POST':
        exchange_book_id = request.form.get('exchange_book_id')
        exchange_message = request.form.get('exchange_message')
        
        if book.owner_id != current_user.id:
            interest = Interest(
                user_id=current_user.id,
                book_id=book_id,
                exchange_book_id=exchange_book_id,
                message=exchange_message
            )
            db.session.add(interest)
            db.session.commit()
            flash('Interest shown successfully')
            return redirect(url_for('dashboard'))
            
    return render_template('show_interest.html', book=book, user_books=user_books)



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
        price = request.form.get('price', type=float) 
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
                owner=current_user,
                price=price
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


@app.route('/book/<int:book_id>')
@login_required
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    interests = Interest.query.filter_by(book_id=book_id).options(
        joinedload(Interest.user),
        joinedload(Interest.exchange_book)
    ).all()
    return render_template('book_details.html', book=book, interests=interests)

@app.route('/view_exchange/<int:exchange_id>')
@login_required
def view_exchange(exchange_id):
    exchange = Exchange.query.get_or_404(exchange_id)
    
    # Verify user is part of the exchange
    if current_user.id not in [exchange.user1_id, exchange.user2_id]:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    return render_template('view_exchange.html', exchange=exchange)


@app.route('/initiate_exchange/<int:book_id>/<int:interest_id>')
@login_required
def initiate_exchange(book_id, interest_id):
    book1 = Book.query.get_or_404(book_id)
    interest = Interest.query.get_or_404(interest_id)
    
    if book1.owner_id == current_user.id:
        exchange = Exchange(
            book1_id=book_id,
            book2_id=interest.exchange_book_id,
            user1_id=current_user.id,
            user2_id=interest.user_id,
            payment_amount=25.0
        )
        
        db.session.add(exchange)
        db.session.commit()

        flash('Exchange initiated. Both users need to pay Rs. 25 to proceed.')
        
        # Redirect to pending payments page instead
        return redirect(url_for('pending_payments'))
    
    flash('Unauthorized action')
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

    if current_user.id not in [exchange.user1_id, exchange.user2_id]:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
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

@app.route('/request-exchange/<int:book_id>', methods=['GET', 'POST'])
@login_required
def request_exchange(book_id):
    requested_book = Book.query.get_or_404(book_id)
    
    # Don't allow requesting your own book
    if requested_book.owner_id == current_user.id:
        flash('You cannot request your own book!', 'error')
        return redirect(url_for('dashboard'))
    
    # Get user's books for exchange option
    user_books = Book.query.filter_by(owner_id=current_user.id).all()
    
    if request.method == 'POST':
        exchange_type = request.form.get('exchange_type')
        message = request.form.get('message')
        offered_book_id = request.form.get('offered_book_id') if exchange_type == 'exchange' else None
        
        # Validate offered book if it's an exchange
        if exchange_type == 'exchange' and offered_book_id:
            offered_book = Book.query.get(offered_book_id)
            if not offered_book or offered_book.owner_id != current_user.id:
                flash('Invalid book selection!', 'error')
                return redirect(url_for('request_exchange', book_id=book_id))
        
        # Create exchange request
        exchange_request = BookExchangeRequest(
            requested_book_id=book_id,
            offered_book_id=offered_book_id,
            requester_id=current_user.id,
            owner_id=requested_book.owner_id,
            message=message,
            status='pending'
        )
        
        db.session.add(exchange_request)
        db.session.commit()
        
        flash('Exchange request sent successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('exchange_request.html', 
                         requested_book=requested_book, 
                         user_books=user_books)

@app.route('/buy_book/<int:book_id>', methods=['POST'])
@login_required
def buy_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if book.owner_id == current_user.id:
        flash('You cannot buy your own book!', 'error')
        return redirect(url_for('dashboard'))
    
    shipping_address = request.form.get('shipping_address')
    payment_method = request.form.get('payment_method')
    
    # Here you would typically:
    # 1. Process the payment
    # 2. Create a purchase record
    # 3. Update book availability
    # 4. Send confirmation emails
    
    book.is_available = False
    db.session.commit()
    
    flash(f'Successfully purchased {book.title}! Shipping to provided address.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/my-requests')
@login_required
def my_requests():
    # Add explicit queries with joins to ensure all relationships are loaded
    sent_requests = BookExchangeRequest.query.filter_by(requester_id=current_user.id)\
        .options(
            db.joinedload(BookExchangeRequest.requested_book),
            db.joinedload(BookExchangeRequest.offered_book),
            db.joinedload(BookExchangeRequest.owner_user)
        ).all()
    
    received_requests = BookExchangeRequest.query.filter_by(owner_id=current_user.id)\
        .options(
            db.joinedload(BookExchangeRequest.requested_book),
            db.joinedload(BookExchangeRequest.offered_book),
            db.joinedload(BookExchangeRequest.requester_user)
        ).all()
    
    # Add debug logging
    print(f"Sent Requests: {len(sent_requests)}")
    print(f"Received Requests: {len(received_requests)}")
    
    return render_template('my_requests.html', 
                         sent_requests=sent_requests, 
                         received_requests=received_requests)

@app.route('/handle-request/<int:request_id>/<string:action>')
@login_required
def handle_request(request_id, action):
    exchange_request = BookExchangeRequest.query.get_or_404(request_id)
    
    # Verify the current user owns the requested book
    if exchange_request.owner_id != current_user.id:
        flash('Unauthorized action!', 'error')
        return redirect(url_for('my_requests'))
    
    if action == 'accept':
        exchange_request.status = 'accepted'
        flash('Exchange request accepted!', 'success')
    elif action == 'reject':
        exchange_request.status = 'rejected'
        flash('Exchange request rejected!', 'success')
    
    db.session.commit()
    return redirect(url_for('my_requests'))

@app.route('/pending_payments')
@login_required
def pending_payments():
    # Get exchanges where the current user is either user1 or user2
    # and where payment is still pending
    pending_exchanges = Exchange.query.filter(
        db.or_(
            db.and_(
                Exchange.user1_id == current_user.id,
                Exchange.user1_payment == False
            ),
            db.and_(
                Exchange.user2_id == current_user.id,
                Exchange.user2_payment == False
            )
        ),
        Exchange.status != 'completed'
    ).order_by(Exchange.created_at.desc()).all()

    return render_template('pending_payments.html', pending_exchanges=pending_exchanges)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)