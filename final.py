import hashlib
import time
import random
import string
import hmac


class User:
    def __init__(self, name, id, password):
        self.username = name
        self.id = id
        self.password = password


class LandTransaction:
    def __init__(self, buyer, seller, landID, price, signature):
        self.buyer = buyer
        self.seller = seller
        self.landID = landID
        self.price = price
        self.signature = signature


class Block:
    def __init__(self, index, previous_hash, timestamp, validator, land_transactions):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.validator = validator
        self.land_transactions = land_transactions
        self.hash = self.generate_hash()

    def generate_hash(self):
        data = str(self.index) + self.previous_hash + \
            str(self.timestamp) + self.validator

        for transaction in self.land_transactions:
            data += transaction.buyer + transaction.seller + \
                transaction.landID + \
                str(transaction.price) + transaction.signature

        hash_value = hashlib.sha256(data.encode()).hexdigest()
        return hash_value


class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.land_ownership = {}  # To store land ownership
        self.validators = {
            "validator1": 1000,  # Initial stake for validator 1
            "validator2": 800,   # Initial stake for validator 2
            "validator3": 1200,  # Initial stake for validator 3
            "validator4": 1500   # Initial stake for validator 4
        }  # To store validators and their stakes
        self.users = {}  # To store users and passwords
        self.count = 0
    # so we will select the one who will have most stakes and then he will validate the transactions

    def create_genesis_block(self):
        genesis_block = Block(0, "0", time.time(), "genesis_validator", [])
        self.chain.append(genesis_block)

    def add_block(self, block):
        self.chain.append(block)

    def select_validator(self):
        total_stake = sum(self.validators.values())
        random_number = random.uniform(0, total_stake)
        cumulative_stake = 0

        for validator, stake in self.validators.items():
            cumulative_stake += stake
            if cumulative_stake >= random_number:
                return validator

    def create_block(self):
        validator = self.select_validator()
        new_block = Block(len(
            self.chain), self.chain[-1].hash, time.time(), validator, self.pending_transactions)
        self.add_block(new_block)
        self.pending_transactions = []

    def mine_block(self):
        print("Mining Block...")
        while True:
            new_block = Block(len(self.chain), self.chain[-1].hash, time.time(
            ), self.select_validator(), self.pending_transactions)
            if (self.count <= 1):
                print("Block Mined!")
                self.chain.append(new_block)
                self.pending_transactions = []
                break
            if self.verify_block(new_block):
                print("Block Mined!")
                self.chain.append(new_block)
                self.pending_transactions = []
                break
            else:
                print("transaction not verified")
                break

    def buy_land(self, buyer_id, seller_id, landID, price, seller_password):
        if buyer_id not in self.users:
            print("Buyer not found.")
            return -1
        if seller_id not in self.users:
            print("Seller not found.")
            return -1

        buyer = self.users[buyer_id]
        seller = self.users[seller_id]

        # either no one has bought that land till now or the seller is the owner
        print(self.land_ownership)
        if landID not in self.land_ownership or self.land_ownership[landID] == seller_id:
            # Generate HMAC challenge
            challenge = ''.join(random.choices(
                string.ascii_letters + string.digits, k=16))
            bit = random.randint(0, 1)  # Generate random bit

            hmac_challenge = hmac.new(seller_password.encode(
            ), (challenge+str(bit)).encode(), hashlib.sha256).hexdigest()

            # Buyer response
            response = hmac.new(seller.password.encode(
            ), (challenge + str(bit)).encode(), hashlib.sha256).hexdigest()
            if (hmac_challenge != response):
                print("wrong password")
                return -1

            # Signature is buyer's response
            transaction = LandTransaction(
                buyer_id, seller_id, landID, price, response)
            self.pending_transactions.append(transaction)

            self.land_ownership[landID] = buyer_id
        else:
            print(
                "Ownership violation: Land cannot be sold by someone who doesn't own it.")
            return -1

    def view_land_ownership(self, owner):
        print("Land ownership for user '{}'".format(owner))
        for block in self.chain:
            for transaction in block.land_transactions:
                if transaction.buyer == owner or transaction.seller == owner:
                    print("Land ID:", transaction.landID, ", Buyer:", transaction.buyer,
                          ", Seller:", transaction.seller, ", Price:", transaction.price)

    def get_transactions_by_land_id(self, land_id):
        matching_transactions = []
        for block in self.chain:
            for transaction in block.land_transactions:
                if transaction.landID == land_id:
                    matching_transactions.append(transaction)

        for transaction in self.pending_transactions:
            if transaction.landID == land_id:
                matching_transactions.append(transaction)
        return matching_transactions

    def verify_block(self, block):

        calculated_merkle_root = self.calculate_merkle_root(
            block.land_transactions)
        print(calculated_merkle_root)
        print("\n", block.hash)
        if calculated_merkle_root != block.hash:
            print("Block verification failed: Merkle root mismatch")
            return False
        return True

    def calculate_merkle_root(self, transactions):
        # Check if transactions list is empty
        if not transactions:
            print("Transactions list is empty. Returning hash of an empty string.")
            return hashlib.sha256(b'').hexdigest()

        # Calculate the hash of each transaction
        transaction_hashes = [hashlib.sha256((transaction.buyer + transaction.seller + transaction.landID + str(
            transaction.price) + transaction.signature).encode()).hexdigest() for transaction in transactions]

        # Debugging: Print transaction hashes
        print(f"Transaction hashes: {transaction_hashes}")

        # Compute the Merkle tree and root
        while len(transaction_hashes) > 1:
            # If the list has an odd length, duplicate the last element to make it even
            if len(transaction_hashes) % 2 != 0:
                transaction_hashes.append(transaction_hashes[-1])

            # Hash pairs of transactions
            new_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                combined_hash = hashlib.sha256(
                    (transaction_hashes[i] + transaction_hashes[i + 1]).encode()).hexdigest()
                new_hashes.append(combined_hash)

            transaction_hashes = new_hashes

        # Debugging: Print the final Merkle root
        print(f"Calculated Merkle root: {transaction_hashes[0]}")

        return transaction_hashes[0]

    def viewUser(self, user_id):
        # List all transactions against the user in mined blocks
        if not self.users:
            print("No registered users in the system")
            return

        if user_id not in self.users:
            print("User not registered")
            return
        print(f"Transactions for user ID '{user_id}':")
        found = False
        for block in self.chain:
            for transaction in block.land_transactions:
                if transaction.buyer == user_id or transaction.seller == user_id:
                    print(
                        f"Land ID: {transaction.landID}, Buyer: {transaction.buyer}, Seller: {transaction.seller}, Price: {transaction.price}")
                    found = True

        for transaction in self.pending_transactions:
            if transaction.buyer == user_id or transaction.seller == user_id:
                print(
                    f"Pending transaction - Land ID: {transaction.landID}, Buyer: {transaction.buyer}, Seller: {transaction.seller}, Price: {transaction.price}")
                found = True
            if not found:
                print(f"No transactions found for user ID '{user_id}'.")

    def add_user(self, name, id, password):
        if id not in self.users:
            self.users[id] = User(name, id, password)
            print("User added successfully.")
        else:
            print("User with ID '{}' already exists.".format(id))


blockchain = Blockchain()
blockchain.create_genesis_block()
flag = True
while flag:
    print("Enter 1 for new transaction\nEnter 2 for viewing transaction details by land id \nEnter 3 for veiwing transaction details by user\nEnter 4 for add user\nEnter 5 for exit")
    a = int(input())
    if a == 1:
        buyerid = input("Enter buyer's id: ")
        sellerid = input("Enter seller's id: ")
        landid = input("Enter land id: ")
        amount = float(input("Enter price of land: "))
        password = input("Enter seller's password: ")
        status = blockchain.buy_land(
            buyerid, sellerid, landid, amount, password)
        if status != -1:
            print("Transaction added.")
            if len(blockchain.pending_transactions) == 4:
                blockchain.count += 1
                print("4 transactions reached. Creating and mining a block")
                blockchain.create_block()
                blockchain.mine_block()
    elif a == 2:
        landid = input("Enter land Id: ")
        transactions = blockchain.get_transactions_by_land_id(landid)
        for i in transactions:
            print(f"Buyer: {i.buyer}, Seller: {i.seller}, Price: {i.price}")
    elif a == 3:

        x = input("Enter your id")
        blockchain.viewUser(x)
    elif a == 4:
        name = input("Enter name: ")
        id = input("Enter ID: ")
        password = input("Enter password: ")
        blockchain.add_user(name, id, password)
    elif a == 5:
        flag = False
        print("Exit")
    else:
        print("Invalid option.")
