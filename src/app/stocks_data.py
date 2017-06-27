# coding=utf-8
import numpy as np
import pandas as pn
import os
from dateutil.parser import parse
import datetime
import pickle
pn.options.mode.chained_assignment = None

src_path = os.path.dirname(os.path.dirname(__file__))
data = {}
YEARS = 5
US_PRECENTAGE = 0.015
DaysInYear = 365
chartChangesList = []   # will contain all of the changes in the simulated chart value
daysCounter = 0         # counting the amount of days the chart was calculated


# תאריך,שער נעילה מתואם,שער נעילה (באגורות) ,שינוי(%),שער פתיחה,שער בסיס,שער גבוה,שער נמוך,הון רשום למסחר,
# שווי שוק (אלפי ש'ח),מחזור מסחר(ש'ח),מחזור ביחידות,מספר עסקאות,סוג האקס *,מקדם אקס,ממ'מ,אחוז החזקות הציבור למדד
renameColumns = ['date', 'closeValueNormlize', 'closeValueAG', 'changePG', 'OpenValue', 'baseValue', 'higheValue',
                 'lowValue', 'marketCapital', 'marketValueESH', 'tradeCycleSH', 'cycleUnits', 'numOfDeals', 'exType',
                 'exCofficient', 'numOfStocksInIndex', 'precentageOfPublicHoldings']


# stock id is in the first line of cvs file
def getStockID(file_name):
    with open(os.path.join(src_path, 'IL_stocks/' + file_name)) as f:
        content = f.readline()
        stock_id = content.split('-')[2].strip()
    return stock_id

def calculateStandardDeviation():
    averageProfit = np.average(chartChangesList)
    standardDeviation = np.std(chartChangesList)
    sharpeRatio = averageProfit / standardDeviation
    return(averageProfit, standardDeviation, sharpeRatio)



def calculateStandardDeviation():
    averageProfit = np.average(chartChangesList)
    standardDeviation = np.std(chartChangesList)
    sharpeRatio = averageProfit / standardDeviation
    return averageProfit, standardDeviation, sharpeRatio


# load stocks from csv files
def loadStocks(includeWorld, num=-1):
    stocks = []
    ILstocksMMM = pn.read_csv(os.path.join(src_path, 'ILstocksMMM.csv'), skiprows=[0, 1, 2],
                              error_bad_lines=False, encoding='Windows-1255')
    ILstocksMMM.columns = ['name', 'symbol', 'ID', 'numOfStocksInIndex', 'precentageOfPublicHoldings', 'date', 'change']
    for f in os.listdir(os.path.join(src_path, 'IL_stocks'))[:num]:
        ilStock = pn.read_csv(os.path.join(src_path, 'IL_stocks/' + f), skiprows=[0, 1],
                              error_bad_lines=False, encoding='Windows-1255')
        ilStock.fillna(ilStock.mean())  # fill nan value
        ilStock.columns = renameColumns
        ilStock.IL_stocks = True
        ilStock.stockID = getStockID(f)

        # save data from general file on the stock (MMM,public precentage)
        precentage = ILstocksMMM.loc[ILstocksMMM['ID'] == int(ilStock.stockID)].precentageOfPublicHoldings.values[0]
        ilStock.precentageOfPublicHoldings = float(precentage.strip('%')) / 100.0
        ilStock.numOfStocksInIndex = \
            ILstocksMMM.loc[ILstocksMMM['ID'] == int(ilStock.stockID)].numOfStocksInIndex.values[0]
        stocks.append(ilStock)

    # add world stocks TODO
    if includeWorld:
        USstocks = []
        for f in os.listdir(os.path.join(src_path, 'US_stocks')):
            usStock = pn.read_csv(os.path.join(src_path, 'US_stocks/' + f),
                                  skiprows=[0, 1], error_bad_lines=False, encoding='Windows-1255')
            usStock.fillna(usStock.mean())  # fill nan value
            usStock.columns = renameColumns
            usStock.IL_stocks = False
            usStock.precentageOfPublicHoldings = 1.0
            usStock.FFMCapi = 0.015
            usStock['closeValueNormlize'] = [x * 100 for x in usStock['closeValueNormlize']]  # ils to agorot
            usStock['marketCapital'] = [x * 1000 for x in usStock['marketCapital']]  # ils to 1000ILS
            usStock['wightForFactorCheak'] = pn.Series([US_PRECENTAGE for x in usStock['marketCapital']])
            usStock['date'] = pn.to_datetime(usStock['date'], dayfirst=True)
            usStock['date'].fillna(method='pad', inplace=True)
            usStock['date'] = [x.strftime('%d/%m/%Y') for x in usStock['date']]
            # today close is tomorrow base
            baseVal = usStock['closeValueNormlize']
            baseVal = pn.Series(baseVal[0]).append(baseVal[:-1], ignore_index=True)
            usStock['baseValue'] = baseVal
            USstocks.append(usStock)

        return stocks, USstocks
    return stocks, None


def getStockIndex(idxName):
    idxValue = pn.read_csv(os.path.join(src_path, 'stockIdx/' + idxName + '.csv'), skiprows=[0, 1, 2],
                           error_bad_lines=False, encoding='Windows-1255')
    idxValue.columns = ['date', 'indexBasePrice', 'indexOpeningPrice', 'closingIndexValue', 'high', 'low',
                        'OverallMarketCap']
    idxValue['date'] = idxValue['date'].apply(lambda d: parse(d, dayfirst=True).strftime('%Y-%m-%d'))
    idxValue.rename(columns={'closingIndexValue': 'value'}, inplace=True)
    idxValue.fillna(idxValue.mean())  # fill nan value
    return idxValue


# pick n (numOfStocks) most higher value stocks
def getIndexStocks(allStocks, numOfStocks, date):
    allStocks.sort(lambda stock1, stock2: biggerThan(stock1.loc[stock1['date'] == date],
                                                     stock2.loc[stock2['date'] == date]))
    return allStocks[:int(numOfStocks)]


# sorting helper function
def biggerThan(stock2, stock1):
    if stock1.empty:
        return -1  # ignore stocks where the data is empty or missing
    if stock2.empty:
        return 1
    if (stock1.baseValue.values[0] * stock1.numOfStocksInIndex.values[0] >=
            stock2.baseValue.values[0] * stock2.numOfStocksInIndex.values[0]):
        return 1
    return -1


# see reference in the pdf file from ofer
def computeFFMCap(s):  # f*Q*P*F
    return (s.wightLimitFactor.values[0] * s.baseValue.values[0] *
            s.numOfStocksInIndex.values[0] * computeBigF(s.precentageOfPublicHoldings.values[0]))


# public holdings precentage - see refrens in the pdf file from ofer
def computeBigF(pVal):
    idx = [20, 25, 30, 35, 45, 60, 80, 100]
    val = [10, 20, 25, 35, 45, 60, 80, 100]
    for i in range(0, 7):
        if pVal < idx[i]:
            return val[i]
    return 100


# see referents in the pdf file from ofer
def computeStockWeight(stock, sum_i):  # Q*F*f*P/sum(i)(#Q*F*f*P)
    FFMCap = computeFFMCap(stock)
    return FFMCap / sum_i


# compute Index value by using yesterday's index value - see referents in the pdf file from ofer
def computeIndex(IYesterday, stocks):
    # print [str(s.wightForFactorCheak.values[0])+"%"+str(s.closeValueAG.values[0])+"*"+str(s.baseValue.values[0]) for s in stocks]
    sumStocks = sum([s.wightForFactorCheak.values[0] * s.closeValueAG.values[0] / s.baseValue.values[0] for s in stocks])
    print(sumStocks)
    chartChangesList.append(sumStocks)
    return IYesterday * sumStocks


def computeIndexUS(iyesterday, stocks):
    return iyesterday * sum([s.closeValueNormlize.values[0] / (s.baseValue.values[0]*len([a for a in stocks if not a.empty])) for s in stocks if not s.empty])


def mixTwoindexes(idx1, idx2, precent1, precent2):
    if precent1 + precent2 != 100:
        raise ValueError('AThe sum of the precentage should be 100')
    if idx1.length != idx2.length:
        raise ValueError('the indexes should be of the same length')
    return (idx1 * precent1 / 100) + (idx2 * precent2 / 100)


def tryReadFromMemory(key):
    try:
        ILstocksMMM = pn.read_csv(os.path.join(src_path, 'newIndexes/' + key + ".csv"))
        return ILstocksMMM
    except:
        return None

def tryReadStatisticsFromMemory(key):
    filePath = os.path.join(src_path, 'newIndexes/' + key + "Statistics")
    try:
        with open( filePath + '.pkl', 'rb') as file:
            statisticsDict = pickle.load(file)
            return (statisticsDict["sharpeRatio"], statisticsDict["standardDeviation"], statisticsDict["averageProfit"])
    except Exception as e:
        print(e)
        return (None, None, None)


def tryReadStatisticsFromMemory(key):
    filePath = os.path.join(src_path, 'newIndexes/' + key + 'Statistics')
    try:
        with open(filePath + '.pkl', 'rb') as f:
            statisticsDict = pickle.load(f)
            return statisticsDict["sharpeRatio"], statisticsDict["standardDeviation"], statisticsDict["averageProfit"]
    except Exception as e:
        print(e)
        return None, None, None


def writeNewIndexToFile(key, newIdx):
    newIdx.to_csv(os.path.join(src_path, 'newIndexes/' + key + ".csv"))

def writeStatisticsToFile(key, sharpeRatio, standardDeviation, averageProfit):
    try:
        if (sharpeRatio is not None and standardDeviation is not None and averageProfit is not None):
            filePath = os.path.join(src_path, 'newIndexes/' + key + "Statistics")
            statisticsDict = {"sharpeRatio" : sharpeRatio, "standardDeviation" : standardDeviation , "averageProfit" : averageProfit}
            with open(filePath + '.pkl', 'wb') as file:
                pickle.dump(statisticsDict, file, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(e)


def writeStatisticsToFile(key, sharpeRatio, standardDeviation, averageProfit):
    try:
        if sharpeRatio is not None and standardDeviation is not None and averageProfit is not None:
            filePath = os.path.join(src_path, 'newIndexes/' + key + 'Statistics')
            statisticsDict = {
                "sharpeRatio": sharpeRatio,
                "standardDeviation": standardDeviation,
                "averageProfit": averageProfit
            }
            with open(filePath + '.pkl', 'wb') as f:
                pickle.dump(statisticsDict, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(e)


def computeNewIndex(numOfStocks, weightLimit, withUS=False, numOfStocksToLoad=-1, indexName=None):
    last = None
    key = [str(numOfStocks), str(weightLimit), str(withUS), str(numOfStocksToLoad), str(indexName)]
    key = '_'.join(key)
    readFile = tryReadFromMemory(key)
    sharpeRatio, standardDeviation, averageProfit = tryReadStatisticsFromMemory(key)
    if (readFile is not None) and (sharpeRatio is not None) and (standardDeviation is not None) and (averageProfit is not None):
        return readFile, sharpeRatio, standardDeviation, averageProfit

    ILStocks, USStocks = loadStocks(withUS, numOfStocksToLoad)

    # filter empty data
    ILStocks = [x for x in ILStocks if not x.empty]

    # create empty object for the new index, and revers its order
    newIdx = pn.DataFrame(ILStocks[0]['date']).iloc[::-1]
    UsIdx = pn.DataFrame(ILStocks[0]['date']).iloc[::-1]
    newIdx['value'] = pn.Series(-1, index=newIdx.index)
    UsIdx['value'] = pn.Series(-1, index=newIdx.index)
    for s in ILStocks:
        s['wightLimitFactor'] = pn.Series(1, index=newIdx.index)  # initalize limit factor
    for s in ILStocks:
        s['publicHoldingsWorth'] = pn.Series(1, index=newIdx.index)  # initalize limit factor
    for s in ILStocks:
        s['wightForFactorCheak'] = pn.Series(0, index=newIdx.index)  # initalize limit factor
    if indexName is not None:
        real_index = getStockIndex(indexName)
        startValue = real_index.loc[real_index.shape[0]-1]['indexBasePrice']
    else:
        startValue = 1000
    idxStocks = []
    lastValueIL = startValue
    lastValueUS = startValue
    dayCounter = 0
    stopCounter = 0

    for i in newIdx['date']:
        # update indexes in the 1 of the month (or the start)
        dayCounter += 1
        stopCounter += 1
        # stop calc for testing TODO remove
        # if (stopCounter > 20) :
        #     break
        #########
        parsedDate = parse(i, dayfirst=True)

        if USStocks is not None:
            USStocksDay = list(s.loc[s['date'] == i] for s in USStocks)
            j = parsedDate - datetime.timedelta(days=2)

            if USStocksDay[0].empty:  # skip weekends
                USStocksDay = last
            else:
                last = USStocksDay

        if idxStocks == [] or (1 <= parsedDate.day <= 10 and dayCounter > 25):
            dayCounter = 0
            idxStocks = getIndexStocks(ILStocks, numOfStocks, i)
            # for t in idxStocks: print t.stockID
            # pick the first n high value stocks
            # Take the current day from each stock in the new index
            idxStocksDay = list(s.loc[s['date'] == i] for s in idxStocks)

            # limit the run to 50 times
            for r in range(0, 50):
                # sum of weights
                # see referents in the pdf file from ofer, sec 3.b.2
                for s in idxStocksDay:
                    s.publicHoldingsWorth = computeFFMCap(s)
                wightLimitFactorSum = sum(s.publicHoldingsWorth for s in idxStocksDay)
                for s in idxStocksDay:
                    s.wightForFactorCheak = s.publicHoldingsWorth / wightLimitFactorSum

                # numpy.isclose(a, b, rtol=1e-05, atol=1e-08, equal_nan=False) rational round
                FFMCapOverWeight = [s for s in idxStocksDay if s.wightForFactorCheak.values[0] > weightLimit and
                                    not np.isclose(s.wightForFactorCheak.values[0], weightLimit)]
                # v1 = sum([computeFFMCap(s) for s in idxStocksDay])

                FFMCapNonCap = (sum([s.publicHoldingsWorth for s in idxStocksDay]) -
                                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]))
                FFMCapQidx = FFMCapNonCap / (1 - sum(weightLimit for _ in FFMCapOverWeight))  # TODO weightLimit?
                # print(sum(s.wightForFactorCheak for s in idxStocksDay))
                for s in idxStocksDay:
                    # print(s.wightForFactorCheak.values[0])
                    if (s.wightForFactorCheak.values[0] > np.float(weightLimit) and
                            not np.isclose(s.wightForFactorCheak.values[0], weightLimit)):
                        s.publicHoldingsWorth = weightLimit * FFMCapQidx
                        # print(s.publicHoldingsWorth / wightLimitFactorSum)

                    s.wightLimitFactor = s.publicHoldingsWorth / (computeBigF(s.precentageOfPublicHoldings.values[0]) *
                                                                  s.baseValue.values[0] *
                                                                  s.numOfStocksInIndex.values[0])

                # loop until no function value is over the limit
                if not [s for s in idxStocksDay if s.wightForFactorCheak.values[0] > weightLimit and
                        not np.isclose(s.wightForFactorCheak.values[0], weightLimit)]:
                    break  # loop until this happend
                lastWightForFactorCheak = [s['wightForFactorCheak'] for s in idxStocksDay]
        else:
            idxStocksDay = list(s.loc[s['date'] == i] for s in idxStocks)
            for index, x in enumerate(idxStocksDay):
                idxStocksDay[index]['wightForFactorCheak'] = lastWightForFactorCheak[index]

        if str(i) == "29/04/2013":
            a = 6
        # weight for each stock
        sumWight = sum([computeFFMCap(s) for s in idxStocksDay])
        for s in idxStocksDay:
            s.wightForFactorCheak = computeStockWeight(s, sumWight)
        # compute date i value

        lastValueIL = computeIndex(lastValueIL, idxStocksDay)

        if USStocks is not None:
            lastValueUS = computeIndexUS(lastValueUS, USStocksDay)
            print "US:" + str(i) + '#' + str(lastValueUS)
            # mix both indexes
            usfactor = US_PRECENTAGE * len(USStocksDay)
            value = lastValueUS*usfactor + lastValueIL * (1 - usfactor)
            newIdx.loc[newIdx['date'] == i, 'value'] = value
        else:
            newIdx.loc[newIdx['date'] == i, 'value'] = lastValueIL
            print str(i) + '#' + str(lastValueIL)

# <<<<<<< HEAD
#     (averageProfit, standardDeviation, sharpeRatio) = calculateStandardDeviation()
#     newIdx['date'] = newIdx['date'].apply(lambda d: parse(d, dayfirst=True).strftime('%Y-%m-%d'))
#
#     writeNewIndexToFile(key,newIdx)
#     writeStatisticsToFile(key, sharpeRatio, standardDeviation, averageProfit)
#     return (newIdx, sharpeRatio, standardDeviation, averageProfit)
# =======
    averageProfit, standardDeviation, sharpeRatio = calculateStandardDeviation()
    newIdx['date'] = newIdx['date'].apply(lambda d: parse(d, dayfirst=True).strftime('%Y-%m-%d'))

    writeNewIndexToFile(key, newIdx)
    writeStatisticsToFile(key, sharpeRatio, standardDeviation, averageProfit)
    return newIdx, sharpeRatio, standardDeviation, averageProfit
# >>>>>>> e6c0fc8476e75a567965971293f1ae91cd424be3


if __name__ == '__main__':
    df = computeNewIndex(numOfStocks=35, weightLimit=0.07, withUS=False, indexName="TA-35")
    # df = computeNewIndex(numOfStocks=5, weightLimit=0.3, numOfStocksToLoad=10)
    # df.to_csv(os.path.join(src_path, 'newindex_15_1.csv'))
    print(df)

