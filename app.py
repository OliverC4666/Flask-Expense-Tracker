from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

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
    return render_template('index.html', purchases=purchases, balance=balance)

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

        # Broadcast update to all users
        purchases = Purchase.query.all()
        data = {
            "balance": balance.amount,
            "purchases": [{"item": p.item, "price": p.price} for p in purchases]
        }
        socketio.emit('update', data)
    
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_balance():
    db.session.query(Purchase).delete()
    balance = Balance.query.first()
    balance.amount = 1000000  # Reset to 1,000,000 VND
    db.session.commit()
    socketio.emit('update', {"balance": balance.amount, "purchases": []})
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
