from beem import Hive
from beem import exceptions
from time import sleep

import getpass
import pandas as pd
import json

hive = Hive(node = "https://api.deathwing.me", nobroadcast=False, num_retries = 3)

name = input("Enter wallet name: ")

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

def payout():
	file = input("Enter CSV file name: ")
	decPoint = input("Enter decimal point(.or,): ")

	df = pd.read_csv(file, decimal = decPoint)
	df["amount"] = df["amount"].astype(float)
	
	while(len(df) > 0) : 
		
		print(len(df))

		users = df[:25]
		pay = json.loads(users.to_json(orient="records"));

		payload =[]

		for payUser in pay :
			amount = str(payUser["amount"])
			payload.append({
				"contractName": "tokens",
				"contractAction":"transfer",  
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
		
		result = hive.custom_json("ssc-mainnet-hive", payload, required_auths=[name])
		print(json.dumps(result))
		
		df = df.iloc[25:]
		
		sleep(5)


if __name__ == "__main__":
    
    unlockWallet()
    checkHiveWallet()
    payout()
