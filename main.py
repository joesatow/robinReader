import glob, json
import pandas as pd
for file in glob.glob("*.csv"):
    accountCSV = file

df = pd.read_csv(accountCSV)
descriptions = df['Description'] 
accountDict = df.to_dict(orient='records')
lastContract = accountDict[0]['Description']
currentNet = 0

def determine(str):
    transactionCode = str['Trans Code']
    if transactionCode != 'BTO' and transactionCode != 'STC':
        return True
    
filteredAccountDict = [x for x in accountDict if not determine(x)]

for line in filteredAccountDict:
    transactionCode = line['Trans Code']
    description = line['Description']

    amount = line['Amount'].replace('$','').replace(',','')
    if '(' in amount:
        amount = amount.replace('(','').replace(')','')
        amount = float(amount)
        amount = -amount
    amount = float(amount)

    if description == lastContract:
        currentNet += amount
    else:
        print(line['Description'])
        print(currentNet)
        currentNet = 0
        lastContract = description

