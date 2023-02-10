import glob
import pandas as pd

# find CSV file.  make sure there's only one in directory.
# will set to latest one.
for file in glob.glob("*.csv"):
    accountCSV = file

# create pandas dataframe
df = pd.read_csv(accountCSV)

# convert dataframe to dictionary
accountDict = df.to_dict(orient='records')

# contract dictionary to track positions until closed
contractDict = {}

# function for use in filtering accountDict below.
# get rid of anything that isnt BTO or STC
def determine(str):
    transactionCode = str['Trans Code']
    if transactionCode != 'BTO' and transactionCode != 'STC':
        return True

# Filter account dictionary
filteredAccountDict = [x for x in accountDict if not determine(x)]

# function to fix amounts
def fixAmount(str):
    amount = str.replace('$','').replace(',','')
    if '(' in amount:
        amount = amount.replace('(','').replace(')','')
        amount = float(amount)
        amount = -amount
    amount = float(amount)
    return amount

# Iterate through account activity
for line in filteredAccountDict:
    description = line['Description']
    quantity = int(line['Quantity'])
    amount = fixAmount(line['Amount'])

    if description not in contractDict:
        contractDict[description] = {
            'quantity': 0,
            'net': 0,
            'startDate': '',
            'endDate': line['Process Date']
        }

    contractDict[description]['quantity'] += quantity
    contractDict[description]['net'] += amount

    if contractDict[description]['quantity'] == 0:
        amount = round(contractDict[description]['net'],2)
        if amount > 1000:
            print("Current contract: " + description)
            print("Current net: " + str(amount))
            print("Buy date: " + line['Process Date'])
            print("Sell date: " + contractDict[description]['endDate'])
        del contractDict[description]
        

