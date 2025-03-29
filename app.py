from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Balance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, default=1000000)  # Default starting balance

@app.route('/')
def index():
    purchases = Purchase.query.all()
    balance = Balance.query.first().amount
    total_spent = sum(p.price for p in purchases)  # Calculate total spent
    return render_template('index.html', purchases=purchases, balance=balance, total_spent=total_spent)

@app.route('/add', methods=['POST'])
def add_purchase():
    item = request.form['item']
    price = float(request.form['price'])
    
    if item and price > 0:
        new_purchase = Purchase(item=item, price=price)
        db.session.add(new_purchase)

        # Deduct from balance
        balance = Balance.query.first()
        balance.amount -= price
        db.session.commit()

        # Calculate new total spent
        purchases = Purchase.query.all()
        total_spent = sum(p.price for p in purchases)

        # Broadcast update to all users
        data = {
            "balance": balance.amount,
            "purchases": [{"item": p.item, "price": p.price} for p in purchases],
            "total_spent": total_spent
        }
        socketio.emit('update', data)
    
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_balance():
    db.session.query(Purchase).delete()
    balance = Balance.query.first()
    balance.amount = 1000000  # Reset to 1,000,000 VND
    db.session.commit()
    socketio.emit('update', {"balance": balance.amount, "purchases": [], "total_spent": 0})
    return redirect(url_for('index'))

@app.route('/set_balance', methods=['POST'])
def set_balance():
    new_balance = request.form.get('new_balance', type=float)
    
    if new_balance is not None and new_balance >= 0:
        balance = Balance.query.first()
        if balance:
            balance.amount = new_balance
        else:
            balance = Balance(amount=new_balance)
            db.session.add(balance)

        db.session.commit()

        # Send update to all clients via WebSockets
        purchases = Purchase.query.all()
        total_spent = sum(p.price for p in purchases)
        socketio.emit('update', {"balance": balance.amount, "purchases": [], "total_spent": total_spent})

    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if not set
    socketio.run(app, host='0.0.0.0', port=port)
