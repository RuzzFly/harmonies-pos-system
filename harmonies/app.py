import json
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

MENU_FILE = 'menu.json'
ORDERS_FILE = 'orders.json'

ORDER_TYPES = ['dine-in', 'take-out', 'delivery']
PAYMENT_METHODS = ['cash', 'gcash']
STATUSES = ['pending', 'paid']

def read_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as file:
        return json.load(file)

def write_json(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

def generate_id(data_dict):
    if not data_dict:
        return "1"
    return str(max([int(k) for k in data_dict.keys()]) + 1)

def is_whole_number(value):
    return isinstance(value, int) and not isinstance(value, bool)

def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)

def get_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data

@app.route('/orders', methods=['POST'])
def add_order():
    data = get_body()
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    menu = read_json(MENU_FILE)
    orders = read_json(ORDERS_FILE)

    order_type = data.get('order_type')
    payment_method = str(data.get('payment_method', '')).lower()
    items = data.get('items')

    if order_type not in ORDER_TYPES:
        return jsonify({"error": "order_type must be dine-in, take-out, or delivery"}), 400
    if payment_method not in PAYMENT_METHODS:
        return jsonify({"error": "payment_method must be cash or gcash"}), 400
    if not isinstance(items, list) or not items:
        return jsonify({"error": "items must be a non-empty list"}), 400

    requested = {}
    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Each item must be an object"}), 400
        item_id = str(item.get('item_id'))
        qty = item.get('quantity')

        if item_id not in menu:
            return jsonify({"error": f"Item ID {item_id} not found in menu"}), 400
        if not is_whole_number(qty) or qty <= 0:
            return jsonify({"error": "quantity must be a whole number greater than 0"}), 400
        requested[item_id] = requested.get(item_id, 0) + qty

    total_cost = 0
    for item_id, qty in requested.items():
        if menu[item_id]['stock'] < qty:
            return jsonify({"error": f"Not enough stock for {menu[item_id]['name']}"}), 400
        total_cost += menu[item_id]['price'] * qty

    for item_id, qty in requested.items():
        menu[item_id]['stock'] -= qty

    write_json(MENU_FILE, menu)

    order_id = generate_id(orders)
    new_order = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "order_type": order_type,
        "payment_method": payment_method,
        "items": [
            {
                "item_id": i,
                "name": menu[i]['name'],
                "price": menu[i]['price'],
                "quantity": q
            }
            for i, q in requested.items()
        ],
        "total": total_cost,
        "status": "pending"
    }

    orders[order_id] = new_order
    write_json(ORDERS_FILE, orders)

    return jsonify({"message": "Order created", "order_id": order_id, "total": total_cost}), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = read_json(ORDERS_FILE)

    status = request.args.get('status')
    if status:
        if status not in STATUSES:
            return jsonify({"error": "Invalid status"}), 400
        orders = {o_id: o for o_id, o in orders.items() if o['status'] == status}

    return jsonify(orders), 200

@app.route('/orders/<order_id>', methods=['GET'])
def get_order_by_id(order_id):
    orders = read_json(ORDERS_FILE)
    if order_id in orders:
        return jsonify(orders[order_id]), 200
    return jsonify({"error": "Order not found"}), 404

@app.route('/reports/daily', methods=['GET'])
def daily_sales_report():
    orders = read_json(ORDERS_FILE)
    day = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))

    total_sales = 0
    daily_orders = 0

    for o_id, details in orders.items():
        if details['date'] == day and details['status'] == 'paid':
            total_sales += details['total']
            daily_orders += 1

    report = {
        "date": day,
        "total_paid_orders": daily_orders,
        "total_revenue": total_sales
    }
    return jsonify(report), 200

@app.route('/orders/<order_id>', methods=['PUT'])
def update_order_status(order_id):
    data = get_body()
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    orders = read_json(ORDERS_FILE)
    if order_id not in orders:
        return jsonify({"error": "Order not found"}), 404

    new_status = data.get('status')
    if new_status in STATUSES:
        orders[order_id]['status'] = new_status
        write_json(ORDERS_FILE, orders)
        return jsonify({"message": "Order status updated", "order": orders[order_id]}), 200
    return jsonify({"error": "Invalid status"}), 400

@app.route('/menu/<item_id>', methods=['PUT'])
def update_menu_item(item_id):
    data = get_body()
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    menu = read_json(MENU_FILE)
    if item_id not in menu:
        return jsonify({"error": "Menu item not found"}), 404

    if 'price' in data:
        if not is_number(data['price']) or data['price'] <= 0:
            return jsonify({"error": "price must be a number greater than 0"}), 400
    if 'stock' in data:
        if not is_whole_number(data['stock']) or data['stock'] < 0:
            return jsonify({"error": "stock must be a whole number, 0 or higher"}), 400

    if 'price' in data:
        menu[item_id]['price'] = float(data['price'])
    if 'stock' in data:
        menu[item_id]['stock'] = data['stock']

    write_json(MENU_FILE, menu)
    return jsonify({"message": "Menu updated", "item": menu[item_id]}), 200

@app.route('/orders/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    orders = read_json(ORDERS_FILE)

    if order_id not in orders:
        return jsonify({"error": "Order not found"}), 404

    if orders[order_id]['status'] != 'paid':
        menu = read_json(MENU_FILE)
        for item in orders[order_id]['items']:
            item_id = str(item['item_id'])
            if item_id in menu:
                menu[item_id]['stock'] += item['quantity']
        write_json(MENU_FILE, menu)

    del orders[order_id]
    write_json(ORDERS_FILE, orders)
    return '', 204

@app.route('/menu/<item_id>', methods=['DELETE'])
def remove_menu_item(item_id):
    menu = read_json(MENU_FILE)

    if item_id not in menu:
        return jsonify({"error": "Menu item not found"}), 404

    del menu[item_id]
    write_json(MENU_FILE, menu)
    return '', 204

@app.route('/menu', methods=['GET'])
def get_menu():
    menu = read_json(MENU_FILE)
    return jsonify(menu), 200

@app.route('/menu', methods=['POST'])
def add_menu_item():
    data = get_body()
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    menu = read_json(MENU_FILE)

    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name is required"}), 400
    if not is_number(price) or price <= 0:
        return jsonify({"error": "price must be a number greater than 0"}), 400
    if not is_whole_number(stock) or stock < 0:
        return jsonify({"error": "stock must be a whole number, 0 or higher"}), 400

    item_id = generate_id(menu)
    menu[item_id] = {
        "name": name.strip(),
        "price": float(price),
        "stock": stock
    }

    write_json(MENU_FILE, menu)
    return jsonify({"message": "Menu item created", "item_id": item_id, "item": menu[item_id]}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)