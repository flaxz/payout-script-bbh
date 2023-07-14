from beem import Hive
from beem import exceptions
from hiveengine.wallet import Wallet
from hiveengine.api import Api
import sys
import traceback
import time
import datetime
import sqlite3
import os
import csv
import getpass
import pandas as pd
import json
from datetime import datetime

testing = "NO"

hive = Hive(node="https://hived.emre.sh", nobroadcast=False, num_retries=3, expiration = 60)
he_node = "https://engine.rishipanthee.com/"
he_api = Api(url=he_node)

## Create databases if they don't exist.
# Connect to the database (create it if it doesn't exist)
conn = sqlite3.connect('processed_files.db')

# Create a table with the specified fields
conn.execute('''CREATE TABLE IF NOT EXISTS files
             (id INTEGER PRIMARY KEY,
             date_added TEXT,
             date_processed TEXT,
             file_name TEXT)''')

# Commit the changes and close the connection
conn.commit()
conn.close()


# Connect to the database (create it if it doesn't exist)
conn = sqlite3.connect('payments.db')

# Create a table with the specified fields
conn.execute('''CREATE TABLE IF NOT EXISTS transactions
             (id INTEGER PRIMARY KEY,
             account TEXT NOT NULL,
             token TEXT NOT NULL,
             amount REAL NOT NULL,
             memo TEXT,
             time_entered TEXT NOT NULL,
             time_paid TEXT,
             txid TEXT)''')

# Commit the changes and close the connection
conn.commit()
conn.close()

def post_discord_message(username, message_body, WEBHOOK_URL):
    payload = {
        "username": username,
        "content": message_body
    }

    try:
        requests.post(WEBHOOK_URL, data=payload)

    except:
        print('Error while sending discord message. Check configs.')

def get_balance(username, token_name):
    wallet = Wallet(username, api=he_api, blockchain_instance=hive)
    token_info = wallet.get_token(token_name)
    try:
        balance = token_info["balance"]
    except:
        balance = 0
    return (balance)

def write_list_to_csv(data, filename):
    header = ["id", "account", "amount", "symbol", "memo"]
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerows(data)

def add_new_files():

    # get list of csv files in current directory
    files = []
    for file in os.listdir('./pay'):
        if file.endswith('.csv') and file != "temp_payments_file.csv":
            files.append(file)

    # search database for csv and add it if not found
    conn = sqlite3.connect('processed_files.db')
    c = conn.cursor()

    found_files = []
    for file in files:
        c.execute("SELECT file_name FROM files WHERE file_name=?", (file,))
        result = c.fetchone()
        if result:
            found_files.append(result[0])
        else:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO files (date_added, file_name) VALUES (?, ?)", (date, file))
            found_files.append(file)
            conn.commit()
            print("New .csv file found:", (file))
    conn.close()

    return found_files

def add_csv_to_database(csv_file, database_file):
    print("File added: " + csv_file)
    file_to_read = "./pay/" + csv_file
    #print(file_to_read)
    # Open the CSV file and read the items
    with open(file_to_read, 'r') as file:
        reader = csv.reader(file)
        items = list(reader)[1:]  # Skip the first row

    # Open the SQLite database and insert the rows
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()

    for item in items:
        #print(item)
        if item == []:
            continue

        account = item[0]
        token = item[2]
        memo = item[3]
        amount = float(item[1].replace(',', '.'))

        # Get the current datetime
        date_entered = datetime.now()

        # Insert the row into the database
        cursor.execute(
            """
            INSERT INTO transactions (account, token, amount, memo, time_entered)
            VALUES (?, ?, ?, ?, ?)
            """,
            (account, token, amount, memo, date_entered)
        )

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

def get_unprocessed_tokens(database_file):
    # Open the SQLite database and execute the query
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT token
        FROM transactions
        WHERE time_paid IS NULL
        GROUP BY token
    """)

    unprocessed_tokens = {row[0] for row in cursor.fetchall()}

    # Close the connection and return the dictionary of tokens and payments
    connection.close()
    return unprocessed_tokens

def process_files(files):
    conn = sqlite3.connect('processed_files.db')
    c = conn.cursor()
    for file in files:
        #print(file)

        add_csv_to_database(file[1], "payments.db")

        file_id = file[0]
        date_processed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if testing != "YES":
            c.execute("UPDATE files SET date_processed=? WHERE id=?", (date_processed, file_id))

    conn.commit()

    conn.close()

    return

def get_unprocessed_files():
    conn = sqlite3.connect('processed_files.db')
    c = conn.cursor()

    c.execute("SELECT id, file_name FROM files WHERE date_processed IS NULL")
    results = c.fetchall()

    conn.close()

    return results

def get_sum_for_token(db_file, token):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    c.execute("""
        SELECT SUM(amount)
        FROM transactions
        WHERE token = ? AND time_paid IS NULL
        GROUP BY token
    """, (token,))

    sum_of_payments = c.fetchone()
    #print(token + ": " + str(sum_of_payments[0]))

    # Close the connection and return the sum of payments
    conn.close()
    return sum_of_payments[0] if sum_of_payments else 0

def checkHiveWallet():
    try:
        hive.wallet.getActiveKeysForAccount(name)
    except exceptions.MissingKeyError:
        key = getpass.getpass("Please Supply the Hive Wallet Active Key: ")
        try:
            hive.wallet.addPrivateKey(key)
        except exceptions.InvalidWifError:
            print("Invalid Key! Please try again.")
            checkHiveWallet()


def unlockWallet():
    walletPassword = getpass.getpass("Wallet Password: ")
    try:
        hive.wallet.unlock(walletPassword)
    except beemstorage.exceptions.WrongMasterPasswordException:
        print("Invalid Password, please try again!")
        unlockWallet()

def get_unpaid_payments():
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()

    c.execute("SELECT id, account, amount, token, memo FROM transactions WHERE time_paid IS NULL")
    results = c.fetchall()

    conn.close()

    return results


def payout(file):
    decPoint = "."

    df = pd.read_csv(file, decimal=decPoint)
    df["account"] = df["account"].fillna("null")
    df["amount"] = df["amount"].astype(float)

    while (len(df) > 0):

        print("Payments left to process: " + str(len(df)))

        users = df[:25]
        pay = json.loads(users.to_json(orient="records"));

        payload = []

        for payUser in pay:
            amount = str(payUser["amount"])
            payload.append({
                "contractName": "tokens",
                "contractAction": "transfer",
                "contractPayload": {
                    "symbol": payUser["symbol"],
                    "to": payUser["account"],
                    "quantity": amount,
                    "memo": payUser["memo"]
                }
            })

        # Remove Backslash of payload
        jsonBuffer = json.dumps(payload)
        payload = json.loads(jsonBuffer)

        pass_test = 0
        while pass_test < 1:
            try:
                if testing == "NO":
                    result = hive.custom_json("ssc-mainnet-hive", payload, required_auths=[name])
                else:
                    result = "testing"
                    print(payload)


                pass_test = 1
                #print(json.dumps(result))


            except Exception as e:
                # Get current system exception
                ex_type, ex_value, ex_traceback = sys.exc_info()

                # Extract unformatter stack traces as tuples
                trace_back = traceback.extract_tb(ex_traceback)

                # Format stacktrace
                stack_trace = list()

                for trace in trace_back:
                    stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (
                    trace[0], trace[1], trace[2], trace[3]))

                print("Exception type : %s " % ex_type.__name__)
                #print("Exception message : %s" % ex_value)
                #print("Stack trace : %s" % stack_trace)
                print("Payment did not process.  Trying again in 5 seconds...")
                time.sleep(5)

        # update database to mark payments as paid and include tx id.

        connection = sqlite3.connect('payments.db')
        cursor = connection.cursor()
        now = datetime.now()
        transaction_number = result["trx_id"]
        #print(transaction_number)

        for payment in pay:
            id = payment["id"]

            # Update the database with the transaction number and current date for a specific payment (example: payment with ID 1)
            payment_id = 1
            cursor.execute("UPDATE transactions SET time_paid = ?, txid = ? WHERE id = ?",
                           (now, transaction_number, id))

            # Commit the changes and close the connection
            connection.commit()

        connection.close()

        df = df.iloc[25:]

        time.sleep(5)


if __name__ == "__main__":

    if testing == "YES":
        name = "bradleyarrow"
    else:
        name = input("Enter wallet name: ")
        unlockWallet()
        checkHiveWallet()

# look for new csv files in directory and add them to database
    add_new_files()

# read files database to get list of csv files that haven't been processed.
    files_to_process = get_unprocessed_files()

# process those files
    process_files(files_to_process)

# check each token to ensure enough balance to pay.

    tokens_to_payout = get_unprocessed_tokens("payments.db")
    issues = 0
    for token in tokens_to_payout:
        #print(token)
        sum_of_payments = get_sum_for_token("payments.db", token)
        balance = float(get_balance(name, token))
        if sum_of_payments > balance:
            issues = issues + 1
            print(token + ": Sum of Payments = " + str(sum_of_payments)+ ", balance = " + str(balance) + ". Add " + str(sum_of_payments - balance) + " " + token + " to continue.")
        else:
            print(token + ": Sum of Payments = " + str(sum_of_payments) + ", balance = " + str(balance) + ". Ready to payout.")

# if any balances are too low, exit script.
    if issues > 0:
        print("Payments were not processed.  Add the above tokens and rerun script.")
        if testing == "NO":
            exit()

# if all balances are ok, start paying out payments.
    unpaid_payments = get_unpaid_payments()

    if len(unpaid_payments) == 0:
        print("No unpaid payments to process.")
        exit()

    # write payments to temporary csv file

    write_list_to_csv(unpaid_payments, "temp_payments_file.csv")

    # run the temporary csv file through payout function.

    print("\nBeginning payouts.\n")
    payout("temp_payments_file.csv")

    print("All payments have been made.")
