import tkinter as tk
from tkinter import simpledialog, messagebox
from pymongo import MongoClient
from datetime import datetime
import random
import hashlib

class BankingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Banking App")

        # MongoDB connection
        try:
            self.client = MongoClient("mongodb+srv://galiyawalagaurav:X3InvPJUPBGqcPR2@bank0.qgowop5.mongodb.net/?retryWrites=true&w=majority")
            self.db = self.client["bank0"]
            self.users_collection = self.db["users"]
            self.accounts_collection = self.db["accounts"]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to MongoDB: {e}")
            self.root.destroy()
            return

        # Current user details
        self.current_user = None
        self.current_account_number = None


        # GUI elements
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)

        self.account_label = tk.Label(self.main_frame, text="")
        self.account_label.grid(row=0, column=0, padx=(5, 5), sticky="w")

        self.menu_label = tk.Label(self.main_frame, text="Menu:")
        self.menu_label.grid(row=1, column=0, pady=(0, 10), sticky="w")

        self.register_button = tk.Button(self.main_frame, text="Register", command=self.register)
        self.register_button.grid(row=2, column=0, pady=(0, 5), sticky="w")

        self.login_button = tk.Button(self.main_frame, text="Login", command=self.login)
        self.login_button.grid(row=3, column=0, pady=(0, 5), sticky="w")

        self.logout_button = tk.Button(self.main_frame, text="Logout", command=self.logout,state=tk.DISABLED)
        self.logout_button.grid(row=4, column=0, pady=(0, 5), sticky="w")

        self.operations_button = tk.Button(self.main_frame, text="Perform Operations", command=self.perform_operations, state=tk.DISABLED)
        self.operations_button.grid(row=5, column=0, pady=(0, 5), sticky="w")

        self.transactions_button = tk.Button(self.main_frame, text="Show Transactions", command=self.show_transactions, state=tk.DISABLED)
        self.transactions_button.grid(row=6, column=0, pady=(0, 10), sticky="w")

        self.exit_button = tk.Button(self.main_frame, text="Exit", command=self.root.destroy)
        self.exit_button.grid(row=7, column=0, pady=(0, 10), sticky="w")

        self.operations_window=None

    def hash_password(self, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password

    def generate_account_number(self):
        return str(random.randint(10000000, 99999999))

    def register(self):
        try:
            username = simpledialog.askstring("Input", "Enter username:")

            if self.users_collection.find_one({"username": username}):
                messagebox.showinfo("Error", "Username already exists. Please choose a different username.")
                return
            
            password = simpledialog.askstring("Input", "Enter password:", show='*')
            confirm_password = simpledialog.askstring("Input", "Confirm password:", show='*')

            if password != confirm_password:
                messagebox.showinfo("Error", "Passwords do not match.")
                return

            account_number = self.generate_account_number()

            hashed_password = self.hash_password(password)
            
            while self.accounts_collection.find_one({"account_no": account_number}):
                account_number = self.generate_account_number()
                
            initial_balance = simpledialog.askfloat("Input", "Enter initial balance:")

            transactions = []

            if initial_balance > 0:
                transactions.append({
                "transaction_id": str(datetime.now()),
                "type": "Deposit",
                "amount": initial_balance,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                

            # Insert account document
            account = {
                "account_no": account_number,
                "balance": initial_balance,
                "transactions": transactions
            }
            account_id = self.accounts_collection.insert_one(account).inserted_id

            # Insert user document with reference to account ID
            self.users_collection.insert_one({"username": username, "password": hashed_password, "account_id": account_id})
            
            self.current_user = username
            self.current_account_number = account_number
            
            messagebox.showinfo("Success", "Registration successful and logged in.")
            self.login_button["state"]=tk.DISABLED
            self.register_button["state"]=tk.DISABLED
            self.logout_button["state"]=tk.NORMAL
            self.operations_button["state"] = tk.NORMAL
            self.transactions_button["state"] = tk.NORMAL

            self.account_label["text"]=f"Logged in as {self.current_user} - Account Number {self.current_account_number}"
            
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")

    def login(self):
        try:
            username = simpledialog.askstring("Input", "Enter username:")
            password = simpledialog.askstring("Input", "Enter password:", show='*')

            hashed_password = self.hash_password(password)

            user = self.users_collection.find_one({"username": username, "password": hashed_password})
            
            if user:
                account = self.accounts_collection.find_one({"_id":user["account_id"]})
                
                self.current_user = username
                self.current_account_number = account["account_no"]
                
                messagebox.showinfo("Success", "Login successful.")
                self.login_button["state"]=tk.DISABLED
                self.register_button["state"]=tk.DISABLED
                self.logout_button["state"]=tk.NORMAL
                self.operations_button["state"] = tk.NORMAL
                self.transactions_button["state"] = tk.NORMAL

                self.account_label["text"]=f"Logged in as {self.current_user} - Account Number {self.current_account_number}"
            else:
                messagebox.showinfo("Error", "Invalid username or password.")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {e}")

    def logout(self):
        self.current_user=None
        self.current_account_number = None
        if self.operations_window:
            self.operations_window.destroy()
            
        self.login_button["state"]=tk.NORMAL
        self.register_button["state"]=tk.NORMAL    
        self.operations_button["state"]=tk.DISABLED
        self.logout_button["state"]=tk.DISABLED
        self.transactions_button["state"]=tk.DISABLED

        self.account_label["text"]=""

        messagebox.showinfo("Info","Logged out seccessfully!")


    def perform_operations(self):
        try:
            user = self.users_collection.find_one({"username": self.current_user})

            if not user:
                messagebox.showinfo("Error", "Please register or log in first.")
                return

            account_id = user["account_id"]
            account = self.accounts_collection.find_one({"_id": account_id})

            operations_window = tk.Toplevel(self.root)
            operations_window.title("Operations")

            # GUI elements for operations window
            operations_frame = tk.Frame(operations_window)
            operations_frame.pack(padx=10, pady=10)

            deposit_button = tk.Button(operations_frame, text="Deposit", command=lambda: self.deposit(account))
            deposit_button.grid(row=0, column=0, pady=(0, 5), sticky="w")

            withdraw_button = tk.Button(operations_frame, text="Withdraw", command=lambda: self.withdraw(account))
            withdraw_button.grid(row=1, column=0, pady=(0, 5), sticky="w")

            check_balance_button = tk.Button(operations_frame, text="Check Balance", command=lambda: self.check_balance(account))
            check_balance_button.grid(row=2, column=0, pady=(0, 5), sticky="w")

            transfer_button = tk.Button(operations_frame, text="Transfer", command=lambda: self.transfer_amount())
            transfer_button.grid(row=3, column=0, pady=(0, 10), sticky="w")

            exit_operations_button = tk.Button(operations_frame, text="Exit", command=operations_window.destroy)
            exit_operations_button.grid(row=4, column=0, pady=(0, 10), sticky="w")
            
            
            self.operations_window=operations_window
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to perform operations: {e}")

    def deposit(self, account):
        try:
            amount = simpledialog.askfloat("Input", "Enter deposit amount:")
            account["balance"] += amount
            transaction = {
                "transaction_id": str(datetime.now()),
                "type": "Deposit",
                "amount": amount,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            account["transactions"].append(transaction)
            self.accounts_collection.update_one({"_id": account["_id"]}, {"$set": account})
            messagebox.showinfo("Success", "Deposit successful.")
        except Exception as e:
            messagebox.showerror("Error", f"Deposit failed: {e}")

    def withdraw(self, account):
        try:
            amount = simpledialog.askfloat("Input", "Enter withdrawal amount:")
            if amount <= account["balance"]:
                account["balance"] -= amount
                transaction = {
                    "transaction_id": str(datetime.now()),
                    "type": "Withdrawal",
                    "amount": amount,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                account["transactions"].append(transaction)
                self.accounts_collection.update_one({"_id": account["_id"]}, {"$set": account})
                messagebox.showinfo("Success", "Withdrawal successful.")
            else:
                messagebox.showinfo("Error", "Insufficient funds.")
        except Exception as e:
            messagebox.showerror("Error", f"Withdrawal failed: {e}")

    def check_balance(self, account):
        try:
            balance = account["balance"]
            messagebox.showinfo("Balance", f"Current Balance: ${balance}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check balance: {e}")

    def transfer_amount(self):
        try:
            if not self.current_user:
                messagebox.showinfo("Error","Please Login First!")
                return
            
            user = self.users_collection.find_one({"username": self.current_user})

            if not user:
                messagebox.showinfo("Error", "Please register or log in first.")
                return

            source_account_id = user["account_id"]
            source_account = self.accounts_collection.find_one({"_id":source_account_id})

            target_account_number = simpledialog.askstring("Input","Enter target account number:")
            
            if target_account_number == source_account["account_no"]:
                messagebox.showinfo("Error", "Cannot transfer to self account!")
                return
            
            target_account = self.accounts_collection.find_one({"account_no":target_account_number})

            if not target_account:
                messagebox.showinfo("Error", "Target account not found!")
                return

            amount = simpledialog.askfloat("Input","Enter Amount:")

            if amount <= source_account["balance"]:
                source_account["balance"]-=amount
                target_account["balance"]+=amount

                source_transaction={
                    "transaction_id":str(datetime.now()),
                    "type": "Transfer(Debit)",
                    "amount":amount,
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "target_account":target_account_number
                }

                target_transaction={
                    "transaction_id":str(datetime.now()),
                    "type": "Transfer(Credit)",
                    "amount":amount,
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_account":source_account["account_no"]
                }

                source_account["transactions"].append(source_transaction)
                target_account["transactions"].append(target_transaction)

                self.accounts_collection.update_one({"_id":source_account["_id"]},{"$set":source_account})
                self.accounts_collection.update_one({"_id":target_account["_id"]},{"$set":target_account})

                messagebox.showinfo("Success","Amount Transferred Successfully !")
            else:
                messagebox.showinfo("Error","Insufficient Balance!")
        except Exception as e:
            messagebox.showerror("Error",f"Transaction failed:{e}")
                
            

    def show_transactions(self):
        try:

            if not self.current_user:
                messagebox.showinfo("Error","Please Login First!")
                return
                
            user = self.users_collection.find_one({"username": self.current_user})

            if not user:
                messagebox.showinfo("Error", "Please register or log in first.")
                return

            account_id = user["account_id"]
            account = self.accounts_collection.find_one({"_id": account_id})
            transactions = account["transactions"]

            if transactions:
                transactions_window = tk.Toplevel(self.root)
                transactions_window.title("Transactions")

                # GUI elements for transactions window
                transactions_frame = tk.Frame(transactions_window)
                transactions_frame.pack(padx=10, pady=10)

                # Display transactions
                for i, transaction in enumerate(transactions):
                    transaction_label = tk.Label(transactions_frame, text=f"{i + 1}. {transaction['type']} - Amount: ${transaction['amount']}, Timestamp: {transaction['timestamp']}")
                    if 'target_account' in transaction:
                        transaction_label["text"]+=f"  Account: {transaction['target_account']}"
                    if 'source_account' in transaction:
                        transaction_label["text"]+=f"  Account: {transaction['source_account']}"
                        
                    transaction_label.grid(row=i, column=0, pady=(0, 5), sticky="w")
                    
            else:
                messagebox.showinfo("Info", "No transactions to display.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show transactions: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BankingApp(root)
    root.mainloop()

