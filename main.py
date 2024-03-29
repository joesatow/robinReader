import pandas as pd
import csv
import datetime
from helper_funcs.downloadFunctions import get_chart
from operator import itemgetter
import time

# set filename to CSV file of account activity
accountCSV = '/Users/joe/Documents/tests/robinReader/activity.csv'

def remove_last_rows(csv_file):
    # Step 1: Open the CSV file in read mode
    with open(csv_file, 'r') as file:
        # Step 2: Read all the rows from the CSV file
        rows = list(csv.reader(file))
    
    # Step 3: Close the file
    file.close()

    # check if last row needs to be removed
    # needs to be removed if more than 10 columns - this 10th column is robinhood's message they put at the end.
    # row before this is also blank. thats why we can remove two lines.
    if len(rows[-1]) == 10:
        # Step 4: Open the CSV file in write mode
        with open(csv_file, 'w') as file:
            # Step 5: Write all the rows except the last one back into the file
            writer = csv.writer(file)
            writer.writerows(rows[:-2])
        
        # Step 6: Close the file
        file.close()

# Usage
remove_last_rows(accountCSV)

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

# create datetime object based on account_activity date format
def getDateObject(dateStr: str):
    dateSplit = dateStr.split('/')
    dateDay, dateMonth, dateYear = int(dateSplit[1]), int(dateSplit[0]), int(dateSplit[2])
    dateObj = datetime.datetime(dateYear, dateMonth, dateDay)
    return dateObj

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
        letExpire = True
    else: # standard BTO or STC line
        description = line['Description']
        quantity = int(line['Quantity'])
        amount = fixAmount(line['Amount'])
        ticker = line['Instrument']
        letExpire = False

    if description not in contractDict:
        contractDict[description] = {
            'ticker': '',
            'currentQuantity': 0,
            'cons': 0,
            'buySum': 0,
            'buyCons': 0,
            'sellSum': 0,
            'sellCons': 0,
            'net': 0,
            'startDate': '',
            'endDate': line['Process Date'],
            'letExpire': ''
        }

    contractDict[description]['ticker'] = ticker
    contractDict[description]['currentQuantity'] += quantity # add quantity.  since there's both positive (buys) and negative (sells) values, it'll eventually zero out (trade is done).
    contractDict[description]['cons'] = max(contractDict[description]['cons'], abs(contractDict[description]['currentQuantity']))
    contractDict[description]['net'] += amount
    if letExpire: 
        contractDict[description]['letExpire'] = 'Yes'
    if transactionCode == 'BTO':
        contractDict[description]['buySum'] += amount
        contractDict[description]['buyCons'] += quantity
    else: # STC or OEXP
        contractDict[description]['sellSum'] += amount
        contractDict[description]['sellCons'] += quantity

    # once quantity in the contract dictionary equals 0, it means sells are equal to buys.  which means the trade is done.
    # create object with trade attributes and append it to the tradeList
    if contractDict[description]['currentQuantity'] == 0:
        buySum = contractDict[description]['buySum']
        buyCons = contractDict[description]['buyCons']
        sellSum = contractDict[description]['sellSum'] 
        sellCons = contractDict[description]['sellCons']
        averageBuy = abs(round((buySum / buyCons)/100, 2))
        averageSell = abs(round((sellSum / sellCons)/100, 2))
        if averageSell == 0:
            pctChange = -1
        else:
            pctChange = -round(((averageBuy - averageSell) / averageBuy), 4)

        cons = contractDict[description]['cons']
        net = round(contractDict[description]['net'],2)
        
        buyDate = line['Process Date'] # buy date must be set here since CSV file shows orders from newest to oldest, from last sell -> first buy.  first buy will be here, once quantity nets out to 0.
        sellDate = contractDict[description]['endDate']
        
        buyDateObject = getDateObject(buyDate)
        sellDateObject = getDateObject(sellDate)

        buyDateDayOfWeek = buyDateObject.strftime('%A')
        sellDateDayOfWeek = sellDateObject.strftime('%A')

        daysHeld = (sellDateObject - buyDateObject).days

        infoObj = {
            "ticker": ticker,
            "contractDescription": description,
            "averageBuy": averageBuy,
            "totalBuy": averageBuy * cons * 100,
            "averageSell": averageSell,
            "totalSell": averageSell * cons * 100,
            "pctChange": pctChange,
            "net": net,
            "contracts": cons,
            "buyDate": buyDate,
            "buyDateDayOfWeek": buyDateDayOfWeek,
            "sellDate": sellDate,
            "sellDateDayOfWeek": sellDateDayOfWeek,
            "daysHeld": daysHeld,
            "letExpire": contractDict[description]['letExpire'] or "No"
        }
        tradeList.append(infoObj)

        del contractDict[description] # delete contract from the dictionary because the trade is done.  

# field names for CSV output file
fields = ['ticker', 'contractDescription', 'contracts', 'averageBuy', 'totalBuy', 'averageSell', 'totalSell', 'pctChange', 'net', 'buyDate', 'buyDateDayOfWeek', 'sellDate', 'sellDateDayOfWeek', 'daysHeld', 'letExpire'] 

# two paths because it changes depending on what computer im using
path = 'C:\\Users\\Joe Satow\\OneDrive\\Random\\Documents\\GitHub\\robinReader\\output.csv'
path = 'output.csv'
with open(path, 'w', newline='') as file: 
    writer = csv.writer(file)
    writer.writerow(['Ticker', 'Description', 'Contracts', 'Average Buy', 'Total Buy', 'Average Sell', 'Total Sell', 'Percent Change', 'Net', 'Buy Date', 'Day', 'Sell Date', 'Day', 'Days Held', 'Let Expire?'])

    writer = csv.DictWriter(file, fieldnames = fields)
    writer.writerows(tradeList)
        


# # to open/create a new html file in the write mode
# f = open('GFG.html', 'w')

# # the html code which will go in the file GFG.html
# html_start = """<html>
# <head>
# <title>RH</title>
# <link rel="stylesheet" href="styles.css">
# </head>
# <body>
# <h1>Robinhood</h1>
# """
# html_mid = ""
# sortedTradeList = sorted(tradeList, key=itemgetter('net'), reverse=False)
# for line in sortedTradeList:
#     net = float(line['net'])
#     if net > 20000:
#         ticker = line['ticker']

#         buyDate = getDateObject(line['buyDate']).strftime("%B %d, %Y")
#         sellDate = getDateObject(line['sellDate']).strftime("%B %d, %Y")

#         chartStartDateDaily = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 170)).strftime("%Y-%m-%d")
#         chartEndDateDaily = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 10)).strftime("%Y-%m-%d")

#         chartStartDateWeekly = (datetime.date(buyDateYear, buyDateMonth, buyDateDay) - datetime.timedelta(days = 600)).strftime("%Y-%m-%d")
#         chartEndDateWeekly = (datetime.date(sellDateYear, sellDateMonth, sellDateDay) + datetime.timedelta(days = 82)).strftime("%Y-%m-%d")

#         time.sleep(0.5)
#         dailyChartFilename = get_chart(ticker, '1d', chartStartDateDaily, chartEndDateDaily)
#         weeklyChartFilename = get_chart(ticker, '1w', chartStartDateWeekly, chartEndDateWeekly)

#         html_mid += f"""
#         <h2>{line['contractDescription']}</h2>
#         <h3>Buy Date: {buyDate}</h3>
#         <h3>Sell Date: {sellDate}</h3>
#         <h3>Net: {'${:,.2f}'.format(float(line['net']))}</h3>
#         <p>
#             <img src='charts\{weeklyChartFilename}'>
#             <img src='charts\{dailyChartFilename}'>
#         </p>"""

# html_end = """
# </body>
# </html>
# """

# # writing the code into the file
# f.write(html_start)
# f.write(html_mid)
# f.write(html_end)

# # close the file
# f.close()
