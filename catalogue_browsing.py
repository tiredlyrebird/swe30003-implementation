import json
import os
import getpass
import re
from datetime import datetime

CATALOGUE_FILE = "catalogue.json"
USERS_FILE = "users.json"
CART_FILE = "cart.json"
ORDERS_FILE = "orders.json"

class Product:
    def __init__(self, upc, name, description, price, category, stock):
        self.upc = upc
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.stock = stock  # integer for quantity in stock

    def display(self):
        print(f"UPC: {self.upc}")
        print(f"Name: {self.name}")
        print(f"Description: {self.description}")
        print(f"Price: ${self.price:.2f}")
        print(f"Category: {self.category}")
        print(f"Availability: {'In Stock' if self.stock > 0 else 'Out of Stock'}")

class ProductCatalogue:
    def __init__(self):
        self.products = []

    def add_product(self, product):
        self.products.append(product)

    def save(self):
        with open(CATALOGUE_FILE, "w") as f:
            json.dump([p.__dict__ for p in self.products], f)

    def load(self):
        if not os.path.exists(CATALOGUE_FILE):
            print("Catalogue file missing, loading sample data.")
            self.products = create_sample_catalogue().products
            self.save()
        else:
            try:
                with open(CATALOGUE_FILE, "r") as f:
                    product_dicts = json.load(f)
                    if not product_dicts:
                        raise ValueError("Empty catalogue file.")
                    self.products = [Product(**pd) for pd in product_dicts]
            except (json.JSONDecodeError, KeyError, ValueError):
                print("Catalogue data corrupted or empty. Loading sample data.")
                self.products = create_sample_catalogue().products
                self.save()

    def filter_by_category(self, category):
        return [p for p in self.products if p.category.lower() == category.lower()]

    def filter_by_price(self, ascending=True):
        return sorted(self.products, key=lambda x: x.price, reverse=not ascending)

    def search_by_name(self, search_name):
        return [p for p in self.products if search_name.lower() in p.name.lower()]

    def find_product_by_upc(self, upc):
        return next((p for p in self.products if p.upc == upc), None)

    def remove_product_by_upc(self, upc):
        self.products = [p for p in self.products if p.upc != upc]

class CheckoutHandler:
    @staticmethod
    def checkout(cart, catalogue):
        if not cart.items:
            print("Cart is empty.")
            return False
        # Check stock availability
        for upc, qty in cart.items.items():
            product = catalogue.find_product_by_upc(upc)
            if product:
                if product.stock < qty:
                    print(f"Not enough stock for {product.name}. Checkout aborted.")
                    return False
        # Get total cost
        total_price = cart.get_total_price(catalogue)
        print(f"Total price of items in cart: ${total_price:.2f}")

        # Payment inputs and validation
        card_number = input("Enter credit card number: ").replace("-", "").replace(" ", "")
        card_number = re.findall(r"[0-9]+", card_number)
        if not card_number or len(card_number[0]) != 16:
            print("The entered card number should be exactly 16 digits long. Checkout aborted.")
            return False

        expiry_date_month = input("Enter month of card expiry date (1-12): ").strip()
        if not expiry_date_month.isdigit() or not (1 <= int(expiry_date_month) <= 12):
            print("The entered expiry date month should be a whole number between 1 and 12. Checkout aborted.")
            return False
        expiry_date_month = int(expiry_date_month)

        expiry_date_year = input("Enter year of card expiry date (YYYY): ").strip()
        if not expiry_date_year.isdigit():
            print("The entered expiry date year should be a whole number. Checkout aborted.")
            return False
        expiry_date_year = int(expiry_date_year)

        # Check card expiration
        current_year = datetime.now().year
        current_month = datetime.now().month
        if expiry_date_year < current_year or (expiry_date_year == current_year and expiry_date_month < current_month):
            print(f"This card has already expired ({expiry_date_month}/{expiry_date_year}). Checkout aborted.")
            return False

        security_number = input("Enter security number of credit card (3 digits on back): ").strip()
        if not (security_number.isdigit() and len(security_number) == 3):
            print("The entered security number should be exactly 3 digits long. Checkout aborted.")
            return False

        # Proceed with checkout: reduce stock, clear cart
        for upc, qty in cart.items.items():
            product = catalogue.find_product_by_upc(upc)
            product.stock -= qty
        cart.items.clear()

        print("Checkout successful! Thank you for your purchase.")
        return True

class Cart:
    def __init__(self):
        self.items = {}  # key: product upc, value: quantity

    def add_to_cart(self, product, quantity=1):
        if product.stock < quantity:
            print(f"Sorry, only {product.stock} units of {product.name} available. Cannot add {quantity}.")
            return
        if product.upc in self.items:
            new_quantity = self.items[product.upc] + quantity
            if new_quantity > product.stock:
                print(f"Cannot add {quantity} more units. Only {product.stock - self.items[product.upc]} units left.")
                return
            self.items[product.upc] = new_quantity
        else:
            self.items[product.upc] = quantity
        print(f"Added {quantity} x {product.name} to cart.")

    def remove_from_cart(self, product_upc):
        if product_upc in self.items:
            del self.items[product_upc]
            print("Product removed from cart.")
        else:
            print("Product not found in cart.")

    def update_quantity(self, product_upc, quantity, catalogue):
        product = catalogue.find_product_by_upc(product_upc)
        if not product:
            print("Product not found.")
            return
        if quantity <= 0:
            self.remove_from_cart(product_upc)
            return
        if quantity > product.stock:
            print(f"Only {product.stock} units available. Cannot update to {quantity}.")
            return
        self.items[product_upc] = quantity
        print(f"Updated {product.name} quantity to {quantity}.")

    def view_cart(self, catalogue):
        if not self.items:
            print("Cart is empty.")
            return
        print("\n--- Your Cart ---")
        total = 0
        for idx, (upc, qty) in enumerate(self.items.items(), start=1):
            product = catalogue.find_product_by_upc(upc)
            if product:
                subtotal = product.price * qty
                total += subtotal
                print(f"{idx}. {product.name} - ${product.price:.2f} x {qty} = ${subtotal:.2f}")
        print(f"Total: ${total:.2f}")

    def get_total_price(self, catalogue):
        total_price = 0.0
        for upc, qty in self.items.items():
            product = catalogue.find_product_by_upc(upc)
            total_price += product.price * qty
        return round(total_price, 2)

    def save(self):
        with open(CART_FILE, "w") as f:
            json.dump(self.items, f)

    def load(self):
        if os.path.exists(CART_FILE):
            try:
                with open(CART_FILE, "r") as f:
                    self.items = json.load(f)
            except json.JSONDecodeError:
                self.items = {}

def create_sample_catalogue():
    catalogue = ProductCatalogue()
    catalogue.add_product(Product("1111", "Laptop X1", "High performance laptop", 1299.99, "Computers", 5))
    catalogue.add_product(Product("2222", 'Smart TV 55"', "4K UHD Smart TV", 899.99, "TVs", 0))
    catalogue.add_product(Product("3333", "Bluetooth Speaker", "Portable speaker", 79.99, "Audio", 10))
    return catalogue

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def signup(users):
    print("\n--- Signup ---")
    while True:
        username = input("Enter a new username: ").strip()
        if username in users:
            print("Username already exists. Try another.")
        elif not username:
            print("Username cannot be empty.")
        else:
            break
    while True:
        password = getpass.getpass("Enter a password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Passwords do not match. Try again.")
        elif not password:
            print("Password cannot be empty.")
        else:
            break
    users[username] = password
    save_users(users)
    print("Signup successful! Please login now.")

def login(users):
    print("\n--- Login ---")
    for _ in range(3):
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        if users.get(username) == password:
            print(f"Welcome back, {username}!")
            return username
        else:
            print("Invalid username or password. Try again.")
    print("Too many failed attempts. Exiting.")
    return None

def display_products(products):
    if not products:
        print("No products to display.")
        return
    for idx, p in enumerate(products, start=1):
        print(f"{idx}. {p.name} - ${p.price:.2f} ({p.category}) - {'In Stock' if p.stock > 0 else 'Out of Stock'}")

def product_details_and_add_to_cart(product, cart):
    product.display()
    while True:
        choice = input("Add this product to cart? (y/n): ").strip().lower()
        if choice == "y":
            while True:
                qty_str = input(f"Enter quantity to add (available: {product.stock}): ").strip()
                if not qty_str.isdigit() or int(qty_str) < 1:
                    print("Enter a valid positive integer.")
                    continue
                qty = int(qty_str)
                cart.add_to_cart(product, qty)
                break
            break
        elif choice == "n":
            break
        else:
            print("Invalid input. Enter y or n.")

def add_new_product(catalogue):
    print("\n--- Add New Product ---")
    upc = input("Enter UPC code: ").strip()
    # Check if UPC already exists
    if catalogue.find_product_by_upc(upc):
        print("Product with this UPC already exists.")
        return
    name = input("Enter product name: ").strip()
    description = input("Enter product description: ").strip()
    while True:
        try:
            price = float(input("Enter product price: ").strip())
            if price < 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid price. Enter a positive number.")
    category = input("Enter product category (Computers, TVs, Audio): ").strip()
    while True:
        try:
            stock = int(input("Enter stock quantity: ").strip())
            if stock < 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid stock. Enter a non-negative integer.")
    new_product = Product(upc, name, description, price, category, stock)
    catalogue.add_product(new_product)
    catalogue.save()
    print(f"Product '{name}' added successfully!")

def manage_catalogue_menu(catalogue):
    while True:
        print("\n--- Manage Catalogue ---")
        print("1. Edit product stock")
        print("2. Delete product from catalogue")
        print("3. Return to main menu")
        choice = input("Enter your choice (1-3): ").strip()
        if choice == "1":
            edit_product_stock(catalogue)
        elif choice == "2":
            delete_product_from_catalogue(catalogue)
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")

def edit_product_stock(catalogue):
    if not catalogue.products:
        print("Catalogue is empty.")
        return
    display_products(catalogue.products)
    upc = input("Enter the UPC of the product to edit stock: ").strip()
    product = catalogue.find_product_by_upc(upc)
    if not product:
        print("Product not found.")
        return
    print(f"Current stock for {product.name}: {product.stock}")
    while True:
        try:
            new_stock = int(input("Enter new stock quantity: ").strip())
            if new_stock < 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid stock quantity. Enter a non-negative integer.")
    product.stock = new_stock
    catalogue.save()
    print(f"Stock updated for {product.name} to {new_stock}.")

def delete_product_from_catalogue(catalogue):
    if not catalogue.products:
        print("Catalogue is empty.")
        return
    display_products(catalogue.products)
    upc = input("Enter the UPC of the product to delete: ").strip()
    product = catalogue.find_product_by_upc(upc)
    if not product:
        print("Product not found.")
        return
    confirm = input(f"Are you sure you want to delete '{product.name}'? (y/n): ").strip().lower()
    if confirm == "y":
        catalogue.remove_product_by_upc(upc)
        catalogue.save()
        print(f"Product '{product.name}' deleted from catalogue.")
    else:
        print("Deletion cancelled.")

def cart_menu(cart, catalogue):
    while True:
        cart.view_cart(catalogue)
        if not cart.items:
            break
        print("\n1. Remove item")
        print("2. Update item quantity")
        print("3. Checkout")
        print("0. Back to main menu")
        choice = input("Select an option: ").strip()
        if choice == "1":
            remove_idx = input("Enter item number to remove: ").strip()
            try:
                idx = int(remove_idx) - 1
                if idx < 0 or idx >= len(cart.items):
                    raise IndexError
                upc_to_remove = list(cart.items.keys())[idx]
                cart.remove_from_cart(upc_to_remove)
            except (ValueError, IndexError):
                print("Invalid item number.")
        elif choice == "2":
            update_idx = input("Enter item number to update quantity: ").strip()
            try:
                idx = int(update_idx) - 1
                if idx < 0 or idx >= len(cart.items):
                    raise IndexError
                upc_to_update = list(cart.items.keys())[idx]
                product = catalogue.find_product_by_upc(upc_to_update)
                if not product:
                    print("Product not found.")
                    continue
                qty_str = input(f"Enter new quantity for {product.name} (0 to remove): ").strip()
                if not qty_str.isdigit():
                    print("Enter a valid integer quantity.")
                    continue
                qty = int(qty_str)
                cart.update_quantity(upc_to_update, qty, catalogue)
            except (ValueError, IndexError):
                print("Invalid item number.")
        elif choice == "3":
            if CheckoutHandler.checkout(cart, catalogue):
                catalogue.save()
                cart.save()
                break
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def main():
    users = load_users()
    catalogue = ProductCatalogue()
    catalogue.load()
    cart = Cart()
    cart.load()

    while True:
        print("\nWelcome to AWE Electronics!")
        print("1. Login")
        print("2. Signup")
        print("3. Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            user = login(users)
            if user:
                while True:
                    print("\n--- Welcome to AWE Electronics Catalogue ---")
                    print("1. View All Products")
                    print("2. View Cart")
                    print("3. Add New Product")
                    print("4. Manage Catalogue")
                    print("5. Save & Exit")
                    main_choice = input("Enter your choice (1-5): ").strip()

                    if main_choice == "1":
                        while True:
                            print("\n1. Filter by Category")
                            print("2. Filter by Price Range")
                            print("3. Search by Product Name")
                            print("0. Back to Main Menu")
                            filter_choice = input("Choose option (0-3): ").strip()

                            if filter_choice == "1":
                                print("\n1. Computers")
                                print("2. TVs")
                                print("3. Audio")
                                category_choice = input("Select category (1-3): ").strip()
                                categories = {"1": "Computers", "2": "TVs", "3": "Audio"}
                                category = categories.get(category_choice)
                                if not category:
                                    print("Invalid category choice.")
                                    continue
                                products = catalogue.filter_by_category(category)
                                if not products:
                                    print(f"No products found in category: '{category}'.")
                                    continue
                                display_products(products)
                                while True:
                                    select = input("Enter product number to view details or 0 to go back: ").strip()
                                    if select == "0":
                                        break
                                    try:
                                        idx = int(select) - 1
                                        if idx < 0 or idx >= len(products):
                                            raise IndexError
                                        product_details_and_add_to_cart(products[idx], cart)
                                    except (ValueError, IndexError):
                                        print("Invalid selection.")

                            elif filter_choice == "2":
                                while True:
                                    print("\n1. Low to high")
                                    print("2. High to low")
                                    print("0. Back to Previous Menu")
                                    price_choice = input("Select price sort option (0-2): ").strip()
                                    if price_choice == "0":
                                        break
                                    elif price_choice in ("1", "2"):
                                        ascending = price_choice == "1"
                                        products = catalogue.filter_by_price(ascending)
                                        if not products:
                                            print("No products available.")
                                            continue
                                        display_products(products)
                                        while True:
                                            select = input("Enter product number to view details or 0 to go back: ").strip()
                                            if select == "0":
                                                break
                                            try:
                                                idx = int(select) - 1
                                                if idx < 0 or idx >= len(products):
                                                    raise IndexError
                                                product_details_and_add_to_cart(products[idx], cart)
                                            except (ValueError, IndexError):
                                                print("Invalid selection.")
                                    else:
                                        print("Invalid choice.")

                            elif filter_choice == "3":
                                search_name = input("Enter product name to search: ").strip()
                                products = catalogue.search_by_name(search_name)
                                if not products:
                                    print(f"No products found with name containing '{search_name}'.")
                                    continue
                                display_products(products)
                                while True:
                                    select = input("Enter product number to view details or 0 to go back: ").strip()
                                    if select == "0":
                                        break
                                    try:
                                        idx = int(select) - 1
                                        if idx < 0 or idx >= len(products):
                                            raise IndexError
                                        product_details_and_add_to_cart(products[idx], cart)
                                    except (ValueError, IndexError):
                                        print("Invalid selection.")
                            elif filter_choice == "0":
                                break
                            else:
                                print("Invalid choice.")

                    elif main_choice == "2":
                        cart_menu(cart, catalogue)

                    elif main_choice == "3":
                        add_new_product(catalogue)

                    elif main_choice == "4":
                        manage_catalogue_menu(catalogue)

                    elif main_choice == "5":
                        print("Saving data and exiting...")
                        catalogue.save()
                        cart.save()
                        return

                    else:
                        print("Invalid choice. Try again.")
            else:
                continue
        elif choice == "2":
            signup(users)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
