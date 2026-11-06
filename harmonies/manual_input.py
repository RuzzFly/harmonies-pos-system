import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def show(response):
    print("\n-> Server Response:", response.status_code)
    if response.text:
        print(json.dumps(response.json(), indent=2))

while True:
    print("\n" + "="*45)
    print("    HARMONIES FOOD CORNER - POS SYSTEM")
    print("="*45)
    print("1.  [CREATE] Add a New Order")
    print("2.  [CREATE] Add a New Menu Item")
    print("3.  [READ]   View Menu & Stock")
    print("4.  [READ]   View Orders (All / Pending / Paid)")
    print("5.  [READ]   View Daily Sales Report")
    print("6.  [UPDATE] Change Order Status")
    print("7.  [UPDATE] Update Menu Item (Stock/Price)")
    print("8.  [DELETE] Cancel an Order")
    print("9.  [DELETE] Remove a Menu Item")
    print("10. Exit")
    print("="*45)

    choice = input("Enter your choice (1-10): ").strip()

    try:
        if choice == '1':
            print("\n--- NEW ORDER ---")
            o_type = input("Order Type (dine-in, take-out, delivery): ").strip().lower()
            payment = input("Payment Method (cash, GCash): ").strip().lower()
            
            items = []
            while True:
                item_id = input("Menu Item ID (e.g., 1) [or press Enter to finish order]: ").strip()
                if not item_id:
                    if not items:
                        print("An order must contain at least one item. Please add an item.")
                        continue
                    break
                qty = int(input(f"Quantity for Item ID {item_id}: "))
                items.append({"item_id": item_id, "quantity": qty})
                
                add_more = input("Add another item to this order? (y/n): ").strip().lower()
                if add_more != 'y':
                    break

            order_data = {
                "order_type": o_type,
                "payment_method": payment,
                "items": items
            }
            show(requests.post(f"{BASE_URL}/orders", json=order_data))

        elif choice == '2':
            print("\n--- NEW MENU ITEM ---")
            name = input("Enter Item Name: ")
            price = float(input("Enter Price: "))
            stock = int(input("Enter Initial Stock: "))

            item_data = {"name": name, "price": price, "stock": stock}
            show(requests.post(f"{BASE_URL}/menu", json=item_data))

        elif choice == '3':
            print("\n--- MENU & INVENTORY STOCK ---")
            show(requests.get(f"{BASE_URL}/menu"))

        elif choice == '4':
            print("\n--- SAVED ORDERS ---")
            status = input("Filter by status (pending, paid, or press Enter for all): ").strip().lower()
            params = {"status": status} if status else {}
            show(requests.get(f"{BASE_URL}/orders", params=params))

        elif choice == '5':
            print("\n--- DAILY SALES REPORT ---")
            day = input("Date (YYYY-MM-DD, or press Enter for today): ").strip()
            params = {"date": day} if day else {}
            show(requests.get(f"{BASE_URL}/reports/daily", params=params))

        elif choice == '6':
            print("\n--- UPDATE ORDER STATUS ---")
            order_id = input("Enter the Order ID you want to update: ").strip()
            new_status = input("Enter new status (pending, paid): ").strip().lower()
            show(requests.put(f"{BASE_URL}/orders/{order_id}", json={"status": new_status}))

        elif choice == '7':
            print("\n--- UPDATE MENU ITEM ---")
            item_id = input("Enter the Menu Item ID you want to update: ").strip()
            new_stock = input("Enter new stock quantity (or press Enter to skip): ")
            new_price = input("Enter new price (or press Enter to skip): ")

            update_data = {}
            if new_stock.strip():
                update_data["stock"] = int(new_stock)
            if new_price.strip():
                update_data["price"] = float(new_price)

            if update_data:
                show(requests.put(f"{BASE_URL}/menu/{item_id}", json=update_data))
            else:
                print("No updates provided.")

        elif choice == '8':
            print("\n--- CANCEL ORDER ---")
            order_id = input("Enter the Order ID you want to cancel: ").strip()
            response = requests.delete(f"{BASE_URL}/orders/{order_id}")
            print("\n-> Server Response:", response.status_code)
            if response.status_code == 204:
                print(f"Order {order_id} was successfully deleted.")
            else:
                print("Error: Could not delete order. Status:", response.status_code)

        elif choice == '9':
            print("\n--- REMOVE MENU ITEM ---")
            item_id = input("Enter the Menu Item ID you want to remove: ").strip()
            response = requests.delete(f"{BASE_URL}/menu/{item_id}")
            print("\n-> Server Response:", response.status_code)
            if response.status_code == 204:
                print(f"Menu item {item_id} was successfully deleted.")
            else:
                print("Error: Could not delete menu item. Status:", response.status_code)

        elif choice == '10':
            print("Exiting POS System...")
            break
        else:
            print("Invalid choice, please try again.")

    except ValueError:
        print("\nInvalid input. Please type a number where a number is required.")
    except requests.exceptions.ConnectionError:
        print("\nCannot reach the server. Start app.py first.")