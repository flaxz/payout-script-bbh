# Hive Payout Script For BBH

2 Python script files, one will create the payout data, and the other will do the payout.

*Please note that this software is in early Beta stage, and that you need to know what you are doing to use it.*

## Installation

For Ubuntu and Debian install these packages:
```
sudo apt-get install python3-pip build-essential libssl-dev python3-dev python3-setuptools python3-gmpy2
```

### Install Python Packages

Install needed packages by (you may need to replace pip3 by pip):
```
sudo pip3 install -U beem hiveengine pandas datetime
```

## Configure And Run The Script

Clone the Github repository to your home directory:
```
cd ~
git clone https://github.com/flaxz/payout-script-bbh
```

Make the bash files executable:
```
cd ~/payout-script-bbh
chmod u+x hive.sh pay.sh leo.sh
```

Edit the settings for getting the payout data, then save and close the file.

```
sudo apt install nano 
cd ~/payout-script-bbh
ls
nano gethive.py
```

token = Base token for the payout (BBH).

getHolders = Accounts to remove, separated by comma.

payToken = Token to pay out (SWAP.HIVE).

payAmount = Amount to pay out (1.0).

payMemo = Memo for the payout.

minBalance = The minimum balance of BBH needed to get a payout (10.0).

### Run the Script

Run the script to get the payout data.

```
cd ~/payout-script-bbh
./hive.sh
./leo.sh
ls
```

View the file in nano.

```
nano filename.csv
```

## Run the payout

Before the first run, set a wallet password for beempy.

```
beempy
changewalletpassphrase
```

Enter new password twice, and.

```
exit
```

After getting the payout data, then run the payout.

IMPORTANT: Make sure that the account you do the payout from has sufficient funds to cover the payout, the script does not currently have a check for this.

```
cd ~/payout-script-bbh
ls
./pay.sh
```

1. Enter account name.
2. Enter wallet password for beempy (on the first run you will be also be prompted to import the Active Key).
3. Enter the CSV file name with the data for the payout.
4. Select dot or comma for decimal point, use dot (.)

Now the payout will run to completion, if no issues arise.

If you need to edit the CSV file due to the payout stopping before it has run it's course then you need to save it with a new name for the remaining payouts, or it will load the old file from cache.

After successful run check the account to see that it has paid out correctly.

Then delete the CSV file.

```
cd ~/payout-script-bbh
ls
rm filename.csv
```

That is it, and remember that it is beta level code, plus that there is no check yet for the full payout amount, so you need to check it manually.

Coders: 
@flaxz
@bambukah
@sc-steemit
