import pandas as pd
from hiveengine.api import Api
from hiveengine.tokenobject import Token
import datetime

# Hive-engine node

api = Api(url = "https://engine.rishipanthee.com/")

# Config settings

token = str("BBH")
getHolders = str("null,bradleyarrow")
payToken = str("LEO")
payAmount = float(10.0) # LEO
payMemo = str("Weekly payout based on your BBH balance.")
minBalance = float(10000.0) # BBH
minDecimal = float(0.001) # LEO

# Script

def main():

  holders = api.find_all("tokens", "balances", query = {"symbol": token})

  df = pd.DataFrame(holders)
  df.drop(columns = ["_id", "symbol", "stake", "delegationsOut", "pendingUndelegations", "pendingUnstake", "delegationsIn"], inplace = True)

  df["balance"] = df["balance"].astype(float)

  tk = Token(token, api = api)
  tokenInfo = tk.get_info()
  decNum = tokenInfo["precision"]
  df["balance"] = df["balance"].round(decNum)
  
  indexZero = df[df["balance"] < minBalance].index
  df.drop(indexZero, inplace = True)

  df.sort_values(by=["balance"], inplace = True, ascending = False)

  dropHolders = getHolders.split(',')
  while len(dropHolders) >= 1:
    indexHolder = df[df["account"] == dropHolders[0]].index
    df.drop(indexHolder, inplace = True)
    print("Successfully removed:", dropHolders[0])
    del dropHolders[0]

  ptk = Token(payToken, api = api)
  payTokenInfo = ptk.get_info()
  payDec = payTokenInfo["precision"]

  sumBalance = float(df["balance"].sum())

  df = df.assign(amount = (payAmount * (df.sum(axis = 1, numeric_only = True) / sumBalance)))
  df["amount"] = df["amount"].astype(float)
  indexZero2 = df[df["amount"] < minDecimal].index
  df.drop(indexZero2, inplace = True)
  df["amount"] = df["amount"].round(payDec)

  sumAmount = df["amount"].sum().round(payDec)
  print("Sum payout:", sumAmount, payToken)
  df["amount"] = df["amount"].astype(str)

  df = df.assign(symbol = payToken)
  df = df.assign(memo = payMemo)

  df.drop(columns = ["balance"], inplace = True)

  now = datetime.datetime.now()
  month = now.strftime("%b")
  day = now.strftime("%d")
  year = now.strftime("%y")
  fileName = payToken + "-" + month + day + year + ".csv"
  print("File name:", fileName)
  
  path = r"./pay/"

  df.to_csv(path+fileName, index = False)

if __name__ == "__main__":
  
  main()
