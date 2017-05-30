# -*- coding: utf8 -*-
import numpy as np
import csv
import pandas as pn;
import os;
from dateutil.parser import parse
data = {}
YEARS = 5
DaysInYear = 365
#תאריך,שער נעילה מתואם,שער נעילה (באגורות)    ,שינוי(%),שער פתיחה,שער בסיס,שער גבוה,שער נמוך,הון רשום למסחר,שווי שוק (אלפי ש"ח),מחזור מסחר(ש"ח),מחזור ביחידות,מספר עסקאות,סוג האקס *,מקדם אקס,ממ"מ,אחוז החזקות הציבור למדד
renameColumns = ["date","closeValueNormlize","closeValueAG","changePG","OpenValue","baseValue","higheValue","lowValue","marketCapital","marketValueESH","tradeCycleSH","cycleUnits","numOfDeals","exType","exCofficient","numOfStocksInIndex","precentageOfPublicHoldings"]

#stock id is in the first line of cvs file
def getStockID(file):
    with open("IL_stocks/" +file) as f:
        content = f.readline()
        id = content.split('-')[2].strip()
    return id


#load stocks from csv files
def loadStocks(includeWorld):
    stocks = []
    ILstocksMMM = pn.read_csv("ILstocksMMM.csv", skiprows=[0, 1,2], error_bad_lines=False, encoding="Windows-1255")
    ILstocksMMM.columns = ['name','symbol','ID','numOfStocksInIndex','precentageOfPublicHoldings','date','change']
    for f in os.listdir("IL_stocks"):
        ilStock = pn.read_csv("IL_stocks/" +f,skiprows= [0,1], error_bad_lines=False,encoding="Windows-1255")
        ilStock.fillna(ilStock.mean()) #fill nan value
        ilStock.columns = renameColumns
        ilStock.IL_stocks = True
        ilStock.stockID = getStockID(f)

          # save data from general file on the stock (MMM,public precentage)
        precentage = ILstocksMMM.loc[ILstocksMMM['ID'] == int(ilStock.stockID)].precentageOfPublicHoldings.values[0]
        ilStock.precentageOfPublicHoldings = float(precentage.strip('%')) / 100.0
        ilStock.numOfStocksInIndex = ILstocksMMM.loc[ILstocksMMM['ID'] == int(ilStock.stockID)].numOfStocksInIndex.values[0]
        stocks.append(ilStock)

    #add world stocks TODO
    if(includeWorld):
        stocks.append(pn.read_csv(os.listdir("stocksWorld")))
    return stocks

#add index file TODO
def getIndex(idxName):
    return pn.read_csv(os.listdir("indexes/"+idxName +".csv"))

#TODO
def getStockIndex(idxName):
    f = open('stockIdx/'+idxName+'.csv', 'rt')
    try:
        reader = csv.reader(f)
        # for row in reader:
        #     print row
    finally:
        f.close()

#pick n (numOfStocks) most higher value stocks
def getIndexStocks(allStocks,numOfStocks,date):

    allStocks.sort(lambda stock1,stock2:
                            bigerThan(stock1.loc[stock1['date'] == date], stock2.loc[stock2['date']== date]))
    return allStocks[:numOfStocks]

#sorting helper function
def bigerThan(stock2,stock1):
    if stock1.empty: return -1  #ignor stocks where the data is empty or missing
    if stock2.empty: return 1
    if(stock1.baseValue.values[0]*stock1.numOfStocksInIndex.values[0] >=
                   stock2.baseValue.values[0] * stock2.numOfStocksInIndex.values[0]):
        return 1
    else: return -1

#see refrens in the pdf file from ofer
def computeFFMCap(stocks):
    return list(np.int(s.wightLimitFactor)*
                np.int(s.baseValue.values[0])*
                np.int(s.numOfStocksInIndex.values[0])*
                np.int(s.precentageOfPublicHoldings)
                for s in stocks)

#public holdings precentage - see refrens in the pdf file from ofer
def computeBigF(pVal):
    idx = [20,25,30,35,45,60,80,100]
    val = [10, 20, 25, 35, 45, 60, 80, 100]
    for i in range(0,7):
        if(pVal<idx[i]):
            return val[i]
    return 100

# see referents in the pdf file from ofer
def wighetFotStock(stock): #Q*F*f*P
    return stock.numOfStocksInIndex.values[0] * computeBigF(stock.precentageOfPublicHoldings.values[0]) * stock.marketCapital.values[0] * stock.baseValue.values[0]

# see referents in the pdf file from ofer
def computeStockWeight(stock,sum): #Q*F*f*P/sum(i)(#Q*F*f*P)
    return wighetFotStock(stock)/sum


# compute Index value by using yesterday 's index value - see referents in the pdf file from ofer
def computeIndex(IYesterday,stocks):
    return IYesterday*sum([s.FFMCapi*s.closeValueNormlize.values[0]/s.baseValue.values[0] for s in stocks])


#TODO?
def mixTwoindexes(idx1,idx2,precent1,precent2):
    if(precent1+precent2 != 100):
        raise ValueError('AThe sum of the precentage should be 100')
    if (idx1.length  != idx2.length):
        raise ValueError('the indexes should be of the same length')
    return (idx1*precent1/100) + (idx2*precent2/100)

#main function, returns new index (pandas DataFrame)
def computeNewIndex(allStocks,numOfStocks,weightLimit):
    #filter empty data
    allStocks = [x for x in allStocks if not x.empty]
    #create empty object for the new index, and revers its order
    newIdx = pn.DataFrame(allStocks[0]["date"]).iloc[::-1]
    newIdx ['value'] = -1.0
    idxStocks = []
    lastValue = 1
    for i in newIdx["date"]:
        #update indexes in the 1 of the month (or the start)
        if idxStocks == [] or parse(i).day == 1:
            #pick the first n high value stocks
            idxStocks = getIndexStocks(allStocks,numOfStocks,i)
        #Take the current day from each stock in the new index

        #choose the relevant data for date i
        idxStocksDay = list(s.loc[s['date'] == i] for s in idxStocks)
        for s in idxStocksDay:s.wightLimitFactor = 1 #initalize limit factor

        while True:
            #sum of weights
            sumWight = sum(wighetFotStock(x) for x in idxStocksDay)
            # weight factor for each stock
            for s in idxStocksDay: s.wightForFactorCheak = computeStockWeight(s,sumWight)

            # see referents in the pdf file from ofer
            FFMCapOverWeight = [s for s in idxStocksDay if s.wightForFactorCheak >= weightLimit]
            FFMCapNonCap = sum(computeFFMCap(idxStocksDay)) - sum(computeFFMCap(FFMCapOverWeight))
            FFMCapQidx = FFMCapNonCap/(1-sum(weightLimit for s in idxStocksDay)) #TODO weightLimit?

            for s in idxStocksDay:
                if (s.wightForFactorCheak < s.wightLimitFactor):
                    s.FFMCapi  = computeStockWeight(s,sumWight)
                else:
                    s.FFMCapi = s.wightLimitFactor*FFMCapQidx

                s.wightLimitFactor = s.FFMCapi/(computeBigF(s.precentageOfPublicHoldings.values[0]) * s.baseValue.values[0] * s.numOfStocksInIndex.values[0])

            #loop until no function value is over the limit
            if([s for s in idxStocksDay if s.wightForFactorCheak >= weightLimit] == []):
                break #loop until this happend

        #compute date i value
        lastValue = computeIndex(lastValue,idxStocksDay)
        newIdx.loc[newIdx['date'] == i,["value"]] = lastValue
    return newIdx


stocks = loadStocks(False)
print(computeNewIndex(stocks,5,7))
