import glob
import pandas as pd
import datetime
from helper_funcs.downloadFunctions import get_chart

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

# list of trades
tradeList = []

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
        
        buyDate = line['Process Date']
        buyDateSplit = buyDate.split('/')
        buyDateDay, buyDateMonth, buyDateYear = int(buyDateSplit[1]), int(buyDateSplit[0]), int(buyDateSplit[2])
        
        sellDate = contractDict[description]['endDate']
        sellDateSplit = sellDate.split('/')
        sellDateDay, sellDateMonth, sellDateYear = int(sellDateSplit[1]), int(sellDateSplit[0]), int(sellDateSplit[2])

        if amount > 10000:
            print("Current contract: " + description)
            print("Current net: " + str(amount))
            print("Buy date: " + buyDate)
            print("Sell date: " + sellDate)

            chartStartDateDaily = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 200)).strftime("%Y-%m-%d")
            chartEndDateDaily = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 10)).strftime("%Y-%m-%d")

            chartStartDateWeekly = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 730)).strftime("%Y-%m-%d")
            chartEndDateWeekly = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 182)).strftime("%Y-%m-%d")

            obj = {
                "contractDescription": description,
                "net": str(amount),
                "buyDate": buyDate,
                "sellDate": sellDate,
                "chartStart": chartStartDateDaily,
                "chartEnd": chartEndDateDaily,
            }
            get_chart('AAPL', '1d', chartStartDateDaily, chartEndDateDaily)
            get_chart('AAPL', '1w', chartStartDateWeekly, chartEndDateWeekly)
            break
        del contractDict[description]
        

