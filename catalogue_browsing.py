import json
import os
import getpass

CATALOGUE_FILE = "catalogue.json"
USERS_FILE = "users.json"
CART_FILE = "cart.json"

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

class Cart:
    def __init__(self):
        self.items = {}  # key: product upc, value: quantity

    def add_to_cart(self, product):
        if product.stock <= 0:
            print("Sorry, this product is out of stock and cannot be added.")
            return
        if product.upc in self.items:
            self.items[product.upc] += 1
        else:
            self.items[product.upc] = 1
        print(f"Added {product.name} to cart.")

    def remove_from_cart(self, product_upc):
        if product_upc in self.items:
            del self.items[product_upc]
            print("Product removed from cart.")
        else:
            print("Product not found in cart.")

    def view_cart(self, catalogue):
        if not self.items:
            print("Cart is empty.")
            return
        print("\n--- Your Cart ---")
        total = 0
        for idx, (upc, qty) in enumerate(self.items.items(), start=1):
            product = next((p for p in catalogue.products if p.upc == upc), None)
            if product:
                subtotal = product.price * qty
                total += subtotal
                print(f"{idx}. {product.name} - ${product.price:.2f} x {qty} = ${subtotal:.2f}")
        print(f"Total: ${total:.2f}")

    def checkout(self, catalogue):
        if not self.items:
            print("Cart is empty.")
            return False
        # Decrement stock in catalogue
        for upc, qty in self.items.items():
            product = next((p for p in catalogue.products if p.upc == upc), None)
            if product:
                if product.stock < qty:
                    print(f"Not enough stock for {product.name}. Checkout aborted.")
                    return False
        # Proceed with checkout
        for upc, qty in self.items.items():
            product = next(p for p in catalogue.products if p.upc == upc)
            product.stock -= qty
        self.items.clear()
        print("Checkout successful! Thank you for your purchase.")
        return True

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
            cart.add_to_cart(product)
            break
        elif choice == "n":
            break
        else:
            print("Invalid input. Enter y or n.")

def add_new_product(catalogue):
    print("\n--- Add New Product ---")
    upc = input("Enter UPC code: ").strip()
    # Check if UPC already exists
    if any(p.upc == upc for p in catalogue.products):
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
                    print("4. Save & Exit")
                    main_choice = input("Enter your choice (1-4): ").strip()

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
                                        print("Invalid option.")

                            elif filter_choice == "3":
                                search_name = input("Enter product name to search: ").strip()
                                products = catalogue.search_by_name(search_name)
                                if not products:
                                    print(f"No products found matching name: '{search_name}'.")
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
                                print("Invalid option.")

                    elif main_choice == "2":
                        cart.view_cart(catalogue)
                        while True:
                            print("\n1. Remove item")
                            print("2. Checkout")
                            print("0. Back")
                            cart_choice = input("Select an option: ").strip()
                            if cart_choice == "1":
                                remove_idx = input("Enter item number to remove: ").strip()
                                try:
                                    idx = int(remove_idx) - 1
                                    if idx < 0 or idx >= len(cart.items):
                                        raise IndexError
                                    upc_to_remove = list(cart.items.keys())[idx]
                                    cart.remove_from_cart(upc_to_remove)
                                except (ValueError, IndexError):
                                    print("Invalid item number.")
                            elif cart_choice == "2":
                                if cart.checkout(catalogue):
                                    catalogue.save()
                                    cart.save()
                                break
                            elif cart_choice == "0":
                                break
                            else:
                                print("Invalid choice.")

                    elif main_choice == "3":
                        add_new_product(catalogue)

                    elif main_choice == "4":
                        catalogue.save()
                        cart.save()
                        print("Data saved. Exiting...")
                        break

                    else:
                        print("Invalid choice.")

        elif choice == "2":
            signup(users)

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
