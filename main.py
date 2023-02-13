import pandas as pd
import csv
import datetime
from helper_funcs.downloadFunctions import get_chart

# set filename to CSV file of account activity
accountCSV = 'account_activity_8255.csv'

# create pandas dataframe
df = pd.read_csv(accountCSV)

# convert dataframe to list of objects
# this is a list made from the account activity CSV
accountActivityList = df.to_dict(orient='records')

# contract dictionary to track positions until closed
# using a dictionary is a good way to track because sometimes you open multiple options at once.
contractDict = {}

# list of trades
# once we've run through all buys and sells for an option, we append the trade data to this list
tradeList = []
chartList = []

# function for use in filtering accountActivityList below.
# get rid of anything that isnt BTO or STC or OEXP
def determine(str):
    transactionCode = str['Trans Code']
    if transactionCode != 'BTO' and transactionCode != 'STC' and transactionCode != 'OEXP':
        return True

# Filter account list
filteredAccountActivityList = [x for x in accountActivityList if not determine(x)]

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
for line in filteredAccountActivityList:
    transactionCode = line['Trans Code']

    # OEXP = option expiration
    # we'll need to get description, ticker, and quantity values differently if we're reading from a OEXP transaction code, because this is just the way Robinhood provided the data.
    # these transactions will act the same as a 'sell'.  example: 10 contracts expired acts as 10 contracts sold for 0 dollars. 
    # this is necessary for netting out quantity, since there's no STC transactions for some trades if you let them expire worthless.
    if transactionCode == 'OEXP':
        description = line['Description'].replace('call','Call').replace('put','Put').replace('Option Expiration for ', '')
        ticker = description.split(' ')[0]
        quantity = -int(line['Quantity'].replace('S','')) # quantity here is how many contracts expired.  
        amount = 0 # 0 because the option expired worthless, equivalent to selling for 0 dollars.
    else: # standard BTC or STC line
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
    contractDict[description]['quantity'] += quantity # add quantity.  since there's both positive (buys) and negative (sells) values, it'll eventually zero out (trade is done).
    contractDict[description]['net'] += amount 

    # once quantity in the contract dictionary equals 0, it means sells are equal to buys.  which means the trade is done.
    # create object with trade attributes and append it to the tradeList
    if contractDict[description]['quantity'] == 0:
        amount = round(contractDict[description]['net'],2)
        
        buyDate = line['Process Date'] # buy date must be set here since CSV file shows orders from newest to oldest, from last sell -> first buy.  first buy will be here, once quantity nets out to 0.
        sellDate = contractDict[description]['endDate']
        
        infoObj = {
            "ticker": ticker,
            "contractDescription": description,
            "net": str(amount),
            "buyDate": buyDate,
            "sellDate": sellDate
        }
        tradeList.append(infoObj)

        del contractDict[description] # delete contract from the dictionary because the trade is done.  

# # field names for CSV output file
# fields = ['ticker', 'contractDescription', 'net', 'buyDate', 'sellDate'] 

# # two paths because it changes depending on what computer im using
# path = 'C:\\Users\\Joe Satow\\OneDrive\\Random\\Documents\\GitHub\\robinReader\\output.csv'
# path = 'output.csv'
# with open(path, 'w', newline='') as file: 
#     writer = csv.DictWriter(file, fieldnames = fields)

#     writer.writeheader()
#     writer.writerows(tradeList)
        
# to open/create a new html file in the write mode
f = open('GFG.html', 'w')

# the html code which will go in the file GFG.html
html_start = """<html>
<head>
<title>RH</title>
</head>
<body>
<h2>Robinhood</h2>
"""
html_mid = ""
for line in tradeList:
    if float(line['net']) > 10000:
        ticker = line['ticker']

        buyDate = line['buyDate']
        buyDateSplit = buyDate.split('/')
        buyDateDay, buyDateMonth, buyDateYear = int(buyDateSplit[1]), int(buyDateSplit[0]), int(buyDateSplit[2])
        
        sellDate = line['sellDate']
        sellDateSplit = sellDate.split('/')
        sellDateDay, sellDateMonth, sellDateYear = int(sellDateSplit[1]), int(sellDateSplit[0]), int(sellDateSplit[2])

        chartStartDateDaily = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 170)).strftime("%Y-%m-%d")
        chartEndDateDaily = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 10)).strftime("%Y-%m-%d")

        chartStartDateWeekly = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 600)).strftime("%Y-%m-%d")
        chartEndDateWeekly = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 82)).strftime("%Y-%m-%d")

        dailyChartFilename = get_chart(ticker, '1d', chartStartDateDaily, chartEndDateDaily)
        weeklyChartFilename = get_chart(ticker, '1w', chartStartDateDaily, chartEndDateWeekly)

        html_mid += f"<h2>test ${line['ticker']}</h2><p><img src='charts\{dailyChartFilename}'><img src='charts\{weeklyChartFilename}'></p>"

html_end = """
</body>
</html>
"""

# writing the code into the file
f.write(html_start)
f.write(html_mid)
f.write(html_end)

# close the file
f.close()
