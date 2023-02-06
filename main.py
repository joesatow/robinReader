import glob, csv
import pandas as pd
for file in glob.glob("*.csv"):
    accountCSV = file

print(accountCSV)

# with open(accountCSV, newline='') as csvfile:
#     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
#     for row in spamreader:
#         print(', '.join(row))

df = pd.read_csv(accountCSV)
descriptions = df['Description'] #you can also use df['column_name']

for line in descriptions:
    print(line)