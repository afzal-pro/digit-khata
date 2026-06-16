from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'easy_khata_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///easy_khata.db'
db = SQLAlchemy(app)

# --- Database Models ---
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    transactions = db.relationship('Transaction', backref='customer', lazy=True, cascade="all, delete-orphan")

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'Diya' ya 'Liya'
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

# --- Routes / Pages ---

# 1. Main Dashboard (Naam aur Phone Dono Se Search)
@app.route('/', methods=['GET', 'POST'])
def index():
    search_query = request.form.get('search', '')
    
    if search_query:
        customers = Customer.query.filter(
            or_(
                Customer.name.like(f"%{search_query}%"),
                Customer.phone.like(f"%{search_query}%")
            )
        ).all()
    else:
        customers = Customer.query.all()
        
    return render_template('index.html', customers=customers, search_query=search_query)

# 2. Add New Customer
@app.route('/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        
        new_customer = Customer(name=name, phone=phone)
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_customer.html')

# 3. Delete Customer
@app.route('/delete/<int:id>')
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('index'))

# 4. Customer Ledger (Udhaar & Payment Management)
@app.route('/ledger/<int:customer_id>', methods=['GET', 'POST'])
def ledger(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        amount = int(request.form['amount'])
        tx_type = request.form['type']
        description = request.form['description']
        
        new_tx = Transaction(amount=amount, type=tx_type, description=description, customer_id=customer_id)
        db.session.add(new_tx)
        db.session.commit()
        return redirect(url_for('ledger', customer_id=customer_id))
    
    total_udhaar = sum(t.amount for t in customer.transactions if t.type == 'Diya')
    total_received = sum(t.amount for t in customer.transactions if t.type == 'Liya')
    net_balance = total_udhaar - total_received
    
    return render_template('ledger.html', customer=customer, net_balance=net_balance)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 
