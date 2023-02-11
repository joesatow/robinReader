import glob
import pandas as pd
import csv
import datetime
from helper_funcs.downloadFunctions import get_chart

# set filename to CSV file of account activity
accountCSV = 'account_activity_8255.csv'

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
    if transactionCode != 'BTO' and transactionCode != 'STC' and transactionCode != 'OEXP':
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
    transactionCode = line['Trans Code']

    if transactionCode == 'OEXP':
        description = line['Description'].replace('call','Call').replace('put','Put').replace('Option Expiration for ', '')
        ticker = description.split(' ')[0]
        quantity = -int(line['Quantity'].replace('S',''))
        amount = 0
    else:
        description = line['Description']
        quantity = int(line['Quantity'])
        amount = fixAmount(line['Amount'])
        ticker = line['Instrument']

    if description not in contractDict:
        contractDict[description] = {
            'ticker': '',
            'quantity': 0,
            'net': 0,
            'startDate': '',
            'endDate': line['Process Date']
        }

    contractDict[description]['ticker'] = ticker
    contractDict[description]['quantity'] += quantity
    contractDict[description]['net'] += amount

    if contractDict[description]['quantity'] == 0:
        amount = round(contractDict[description]['net'],2)
        
        buyDate = line['Process Date'] # buy date must be set here since CSV file shows orders from newest to oldest, from last sell -> first buy.  first buy will be here, once quantity nets out to 0.
        buyDateSplit = buyDate.split('/')
        buyDateDay, buyDateMonth, buyDateYear = int(buyDateSplit[1]), int(buyDateSplit[0]), int(buyDateSplit[2])
        
        sellDate = contractDict[description]['endDate']
        sellDateSplit = sellDate.split('/')
        sellDateDay, sellDateMonth, sellDateYear = int(sellDateSplit[1]), int(sellDateSplit[0]), int(sellDateSplit[2])

        # if amount > 1000 or amount < -1000:
        # print("Current contract: " + description)
        # print("Current net: " + str(amount))
        # print("Buy date: " + buyDate)
        # print("Sell date: " + sellDate)

        chartStartDateDaily = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 170)).strftime("%Y-%m-%d")
        chartEndDateDaily = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 10)).strftime("%Y-%m-%d")

        chartStartDateWeekly = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 600)).strftime("%Y-%m-%d")
        chartEndDateWeekly = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 82)).strftime("%Y-%m-%d")

        obj = {
            "ticker": ticker,
            "contractDescription": description,
            "net": str(amount),
            "buyDate": buyDate,
            "sellDate": sellDate
        }
        tradeList.append(obj)
        #get_chart(ticker, '1d', chartStartDateDaily, chartEndDateDaily)
        #get_chart(ticker, '1w', chartStartDateWeekly, chartEndDateWeekly)
            
        del contractDict[description]


# field names 
fields = ['ticker', 'contractDescription', 'net', 'buyDate', 'sellDate'] 

with open('C:\\Users\\Joe Satow\\OneDrive\\Random\\Documents\\GitHub\\robinReader\\output.csv', 'w', newline='') as file: 
    writer = csv.DictWriter(file, fieldnames = fields)

    writer.writeheader()
    writer.writerows(tradeList)

pass
        

