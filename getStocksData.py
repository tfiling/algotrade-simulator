# -*- coding: utf8 -*-
import datetime
import numpy as np
import csv
import pandas as pn;
import os;
from dateutil.parser import parse
from pandas._libs.tslib import NaTType

data = {}
YEARS = 5
US_PRECENTAGE = 0.015
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
def loadStocks(includeWorld,num = -1):
    stocks = []
    ILstocksMMM = pn.read_csv("ILstocksMMM.csv", skiprows=[0, 1,2], error_bad_lines=False, encoding="Windows-1255")
    ILstocksMMM.columns = ['name','symbol','ID','numOfStocksInIndex','precentageOfPublicHoldings','date','change']
    for f in os.listdir("IL_stocks")[:num]:
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
        USstocks = []
        for f in os.listdir("US_stocks"):
            usStock = pn.read_csv("US_stocks/" + f, skiprows=[0, 1], error_bad_lines=False, encoding="Windows-1255")
            usStock.fillna(usStock.mean())  # fill nan value
            usStock.columns = renameColumns
            usStock.IL_stocks = False
            usStock.precentageOfPublicHoldings = 1.0
            usStock.FFMCapi = 0.015
            usStock['closeValueNormlize'] = [x*100 for x in usStock['closeValueNormlize']] #ils to agorot
            usStock['marketCapital'] = [x * 1000 for x in usStock['marketCapital']]  # ils to 1000ILS
            usStock['wightForFactorCheak'] = US_PRECENTAGE
            usStock['date'] = pn.to_datetime(usStock['date'],dayfirst=True)
            usStock['date'].fillna(method='pad',inplace=True)
            usStock['date'] = [x.strftime('%d/%m/%Y') for x in usStock['date']]
            # today close is tomorrow base
            baseVal = usStock['closeValueNormlize']
            baseVal = pn.Series(baseVal[0]).append(baseVal[:-1],ignore_index=True)
            usStock['baseValue'] = baseVal
            USstocks.append(usStock)

        return stocks,USstocks
    return stocks,None
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
def computeFFMCap(s):  #f*Q*P*F
    return s.wightLimitFactor.values[0]*s.baseValue.values[0]*s.numOfStocksInIndex.values[0]*computeBigF(s.precentageOfPublicHoldings.values[0])

#public holdings precentage - see refrens in the pdf file from ofer
def computeBigF(pVal):
    idx = [20,25,30,35,45,60,80,100]
    val = [10, 20, 25, 35, 45, 60, 80, 100]
    for i in range(0,7):
        if(pVal<idx[i]):
            return val[i]
    return 100

# see referents in the pdf file from ofer
def computeStockWeight(stock,sum): #Q*F*f*P/sum(i)(#Q*F*f*P)
    FFMCap = computeFFMCap(stock)
    return FFMCap/sum


# compute Index value by using yesterday 's index value - see referents in the pdf file from ofer
def computeIndex(IYesterday,stocks):
    return IYesterday*sum([s.wightForFactorCheak.values[0]*s.closeValueAG.values[0]/s.baseValue.values[0] for s in stocks])

def computeIndexUS(iyesterday,stocks):
    return iyesterday*sum([s.wightForFactorCheak.values[0]*s.closeValueNormlize.values[0]/s.baseValue.values[0] for s in stocks])


#TODO?
def mixTwoindexes(idx1,idx2,precent1,precent2):
    if(precent1+precent2 != 100):
        raise ValueError('AThe sum of the precentage should be 100')
    if (idx1.length  != idx2.length):
        raise ValueError('the indexes should be of the same length')
    return (idx1*precent1/100) + (idx2*precent2/100)

#main function, returns new index (pandas DataFrame)
def computeUsIndex(lastValueUS, i, USStocks):

    pass


def computeNewIndex(ILStocks, numOfStocks, weightLimit, USStocks=None):
    #filter empty data
    ILStocks = [x for x in ILStocks if not x.empty]

    #create empty object for the new index, and revers its order
    newIdx = pn.DataFrame(ILStocks[0]["date"]).iloc[::-1]
    UsIdx = pn.DataFrame(ILStocks[0]["date"]).iloc[::-1]
    newIdx ['value'] = pn.Series(-1, index=newIdx.index)
    UsIdx['value'] = pn.Series(-1, index=newIdx.index)
    for s in  ILStocks: s['wightLimitFactor'] = pn.Series(1, index=newIdx.index)  # initalize limit factor
    for s in ILStocks: s['publicHoldingsWorth'] = pn.Series(1, index=newIdx.index)  # initalize limit factor
    for s in ILStocks: s['wightForFactorCheak'] = pn.Series(0, index=newIdx.index)  # initalize limit factor
    if (USStocks != None):
        for s in USStocks: s['wightForFactorCheak'] = pn.Series(0, index=newIdx.index)  # initalize limit factor
    idxStocks = []
    lastValueIL = 1
    lastValueUS = 1
    dayCounter = 0
    for i in newIdx["date"]:
        #update indexes in the 1 of the month (or the start)
        dayCounter+=1
        if idxStocks == [] or (parse(i).day >= 1 and parse(i).day <= 10 and dayCounter>25):
            dayCounter = 0
            idxStocks = getIndexStocks(ILStocks, numOfStocks, i)
            #pick the first n high value stocks
            #Take the current day from each stock in the new index
            idxStocksDay = list(s.loc[s['date'] == i] for s in idxStocks)
            if(USStocks != None):
                USStocksDay = list(s.loc[s['date'] == i] for s in USStocks)
                j = parse(i) - datetime.timedelta(days=2)

                while(USStocksDay[0].empty): #skipp weekends
                    #print(i)
                    #print(USStocks)
                    j = j - datetime.timedelta(days=1)
                    USStocksDay = list(s.loc[s['date'] == j] for s in USStocks)
            #limit the run to 50 times
            for r in range(0,50) :
                #sum of weights
                # see referents in the pdf file from ofer, sec 3.b.2
                for s in idxStocksDay:s.publicHoldingsWorth = computeFFMCap(s)
                wightLimitFactorSum = sum(s.publicHoldingsWorth for s in idxStocksDay)
                for s in idxStocksDay: s.wightForFactorCheak = s.publicHoldingsWorth/wightLimitFactorSum

                #numpy.isclose(a, b, rtol=1e-05, atol=1e-08, equal_nan=False) rational round
                FFMCapOverWeight = [s for s in idxStocksDay if s.wightForFactorCheak.values[0] > weightLimit  and not np.isclose(s.wightForFactorCheak.values[0],weightLimit)]
                #v1 = sum([computeFFMCap(s) for s in idxStocksDay])

                FFMCapNonCap = sum([s.publicHoldingsWorth for s in idxStocksDay])- sum([s.publicHoldingsWorth for s in FFMCapOverWeight])
                FFMCapQidx = FFMCapNonCap/(1-sum(weightLimit for s in FFMCapOverWeight)) #TODO weightLimit?
                #print(sum(s.wightForFactorCheak for s in idxStocksDay))
                for s in idxStocksDay:
                    #print(s.wightForFactorCheak.values[0])
                    if (s.wightForFactorCheak.values[0] > np.float(weightLimit) and not np.isclose(s.wightForFactorCheak.values[0],weightLimit)):
                        s.publicHoldingsWorth = weightLimit*FFMCapQidx
                        # print(s.publicHoldingsWorth / wightLimitFactorSum)

                    s.wightLimitFactor = s.publicHoldingsWorth/(computeBigF(s.precentageOfPublicHoldings.values[0]) * s.baseValue.values[0] * s.numOfStocksInIndex.values[0])

                #loop until no function value is over the limit
                if([s for s in idxStocksDay if s.wightForFactorCheak.values[0] > weightLimit  and not np.isclose(s.wightForFactorCheak.values[0],weightLimit)] == []):
                    break #loop until this happend

        # weight for each stock
        sumWight = sum([computeFFMCap(s) for s in idxStocksDay])
        for s in idxStocksDay:
            s.wightForFactorCheak = computeStockWeight(s, sumWight)
        #compute date i value

        lastValueIL = computeIndex(lastValueIL,idxStocksDay)
        print (str(i) + "#" +str(lastValueIL))
        if(USStocks!=None):
            lastValueUS = computeIndexUS(lastValueUS,USStocksDay)
            #mix both indexes
            usfactor = US_PRECENTAGE*len(USStocksDay)
            newIdx.loc[newIdx['date'] == i, ["value"]] = lastValueUS*usfactor + lastValueIL*(1-usfactor)
        else:
            newIdx.loc[newIdx['date'] == i,["value"]] = lastValueIL
    return newIdx


stocks,usStocks = loadStocks(False,50)
print(computeNewIndex(stocks,40,0.07,usStocks))
