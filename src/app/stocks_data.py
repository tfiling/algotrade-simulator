# coding=utf-8
import numpy as np
import pandas as pn
import os
from dateutil.parser import parse
import datetime
import pickle
import logging
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


# stock id and name is in the first line of cvs file
def getStockIDAndName(file_name):
    with open(os.path.join(src_path, 'IL_stocks/' + file_name)) as f:
        content = f.readline()
        stock_id = content.split('-')[2].strip()
        stock_name = content.split('-')[1].strip()
    return stock_id, stock_name


def calculateStandardDeviation():
    global chartChangesList
    filteredChartChangesList = [x for x in chartChangesList if not np.isnan(x)]
    averageProfit = np.average(filteredChartChangesList)
    averageProfit = ((1 + averageProfit)**254) - 1
    standardDeviation = np.std(filteredChartChangesList)
    standardDeviation *= 254 ** 0.5
    sharpeRatio = averageProfit / standardDeviation
    print("====calculateStandardDeviation====")
    print(filteredChartChangesList)
    print("std: ", standardDeviation)
    print("sharpe ratio: ", sharpeRatio)
    print("averageReturn: ", averageProfit)
    chartChangesList = []
    return averageProfit, standardDeviation, sharpeRatio


# load stocks from csv files
def loadStocks(includeWorld):
    stocks = []
    ILstocksMMM = pn.read_csv(os.path.join(src_path, 'ILstocksMMM.csv'), skiprows=[0, 1, 2],
                              error_bad_lines=False, encoding='Windows-1255')
    ILstocksMMM.columns = ['name', 'symbol', 'ID', 'numOfStocksInIndex', 'precentageOfPublicHoldings', 'date', 'change']
    for f in os.listdir(os.path.join(src_path, 'IL_stocks')):
        ilStock = pn.read_csv(os.path.join(src_path, 'IL_stocks/' + f), skiprows=[0, 1],
                              error_bad_lines=False, encoding='Windows-1255')
        ilStock.fillna(ilStock.mean())  # fill nan value
        ilStock.columns = renameColumns
        ilStock.IL_stocks = True
        ilStock.stockID, name = getStockIDAndName(f)
        newIdx = pn.DataFrame(ilStock['date']).iloc[::-1]
        # add a column for the stock's name(each row will contain the stock's name)
        ilStock['stockIdentifier'] = pn.Series(name, index=newIdx.index)

        # save data from general file on the stock (MMM,public precentage)
        precentage = ILstocksMMM.loc[ILstocksMMM['ID'] == int(ilStock.stockID)].precentageOfPublicHoldings.values[0]
        ilStock.precentageOfPublicHoldings = float(precentage.strip('%')) / 100.0
        ilStock.numOfStocksInIndex = \
            ILstocksMMM.loc[ILstocksMMM['ID'] == int(ilStock.stockID)].numOfStocksInIndex.values[0]
        stocks.append(ilStock)

    # add world stocks
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
            usStock['wightForFactorCheak'] = pn.Series([US_PRECENTAGE for _ in usStock['marketCapital']])
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
    # print [str(s.wightForFactorCheak.values[0])+"%"+str(s.closeValueAG.values[0])
    # +"*"+str(s.baseValue.values[0]) for s in stocks]
    sumStocks = sum([s.wightForFactorCheak.values[0] * s.closeValueAG.values[0] / s.baseValue.values[0] for s in stocks])
    chartChangesList.append(sumStocks - 1)
    # print to log info about each stock
    for s in stocks:
        name = s['stockIdentifier'].values[0]
        weight = "%d%s" % (int((s.wightForFactorCheak.values[0]) * 100), "%")
        openValue = str(s.baseValue.values[0])
        closeValue = str(s.closeValueAG.values[0])
        logging.info("stock's name: %s \n"
                     "                                        weight on chart = %s \n"
                     "                                        open value = %s \n"
                     "                                        close value = %s" % (name, weight, openValue, closeValue))
    return IYesterday * sumStocks


def computeIndexUS(iyesterday, stocks):
    sumStocks = sum([s.closeValueNormlize.values[0] / (s.baseValue.values[0]*len([a for a in stocks if not a.empty])) for s in stocks if not s.empty])
    chartChangesList.append(sumStocks - 1)
    # save the chart changes with the us
    lastChartChangesElementIndex = len(chartChangesList) - 1
    lastChartChangesElement = chartChangesList[lastChartChangesElementIndex]
    usfactor = US_PRECENTAGE * len(stocks)
    valueWithUS = sumStocks * usfactor + lastChartChangesElement * (1 - usfactor)
    chartChangesList[lastChartChangesElementIndex] = valueWithUS
    return iyesterday * sumStocks


def mixTwoindexes(idx1, idx2, precent1, precent2):
    if precent1 + precent2 != 100:
        raise ValueError('AThe sum of the precentage should be 100')
    if idx1.length != idx2.length:
        raise ValueError('the indexes should be of the same length')
    return (idx1 * precent1 / 100) + (idx2 * precent2 / 100)


def tryReadFromMemory(key):
    try:
        ILstocksMMM = pn.read_csv(os.path.join(src_path, 'newIndices/' + key + ".csv"))
        return ILstocksMMM
    except:
        return None


def tryReadStatisticsFromMemory(key):
    filePath = os.path.join(src_path, 'newIndices/' + key + 'Statistics')
    try:
        with open(filePath + '.pkl', 'rb') as f:
            statisticsDict = pickle.load(f)
            return statisticsDict["sharpeRatio"], statisticsDict["standardDeviation"], statisticsDict["averageProfit"]
    except Exception as e:
        print(e)
        return None, None, None


def writeNewIndexToFile(key, newIdx):
    newIdx.to_csv(os.path.join(src_path, 'newIndices/' + key + ".csv"))


def writeStatisticsToFile(key, sharpeRatio, standardDeviation, averageProfit):
    try:
        if sharpeRatio is not None and standardDeviation is not None and averageProfit is not None:
            filePath = os.path.join(src_path, 'newIndices/' + key + 'Statistics')
            statisticsDict = {
                "sharpeRatio": sharpeRatio,
                "standardDeviation": standardDeviation,
                "averageProfit": averageProfit
            }
            with open(filePath + '.pkl', 'wb') as f:
                pickle.dump(statisticsDict, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(e)


def startLogger(key=None):
    if not os.path.exists(os.path.join(src_path, 'log/')):
        os.makedirs(os.path.join(src_path, 'log/'))
    logFileName = "%s_%s.txt" % (key, datetime.datetime.now().strftime("%d-%m-%y_%H-%M"))
    logFilePath = os.path.join(src_path, 'log/' + logFileName)
    logging.basicConfig(filename=logFilePath, format='%(asctime)s - %(message)s', level=logging.DEBUG, filemode='wb')


def computeNewIndex(numOfStocks, weightLimit, withUS=False, indexName=None):
    last = None
    key = [str(numOfStocks), str(weightLimit), str(withUS), str(indexName)]
    key = '_'.join(key)
    startLogger(key)
    readFile = tryReadFromMemory(key)
    sharpeRatio, standardDeviation, averageProfit = tryReadStatisticsFromMemory(key)
    if (readFile is not None) and (sharpeRatio is not None) and (standardDeviation is not None) and (averageProfit is not None):
        logging.info("Simulator already calculated => loading saved data from file")
        return readFile, sharpeRatio, standardDeviation, averageProfit

    ILStocks, USStocks = loadStocks(withUS)
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
    lastWightLimitFactor = []

    for i in newIdx['date']:
        # update indexes in the 1 of the month (or the start)
        dayCounter += 1
        stopCounter += 1
        parsedDate = parse(i, dayfirst=True)

        if USStocks is not None:
            USStocksDay = list(s.loc[s['date'] == i] for s in USStocks)

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
                    s.wightForFactorCheak = s.publicHoldingsWorth*1.0 / wightLimitFactorSum

                # numpy.isclose(a, b, rtol=1e-05, atol=1e-08, equal_nan=False) rational round
                FFMCapOverWeight = [s for s in idxStocksDay if s.wightForFactorCheak.values[0] > weightLimit and
                                    not np.isclose(s.wightForFactorCheak.values[0], weightLimit)]
                # v1 = sum([computeFFMCap(s) for s in idxStocksDay])

                FFMCapNonCap = (sum([s.publicHoldingsWorth for s in idxStocksDay]) -
                                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]))
                FFMCapQidx = FFMCapNonCap / (1 - sum(weightLimit for _ in FFMCapOverWeight))
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
                # lastWightForFactorCheak = [s['wightForFactorCheak'] for s in idxStocksDay]
                lastWightLimitFactor = [s['wightLimitFactor'] for s in idxStocksDay]
            # print lastWightLimitFactor

        else:
            idxStocksDay = list(s.loc[s['date'] == i] for s in idxStocks)
            for index, x in enumerate(idxStocksDay):
                x.wightLimitFactor = lastWightLimitFactor[index].values[0]

        # weight for each stock
        sumWight = sum([computeFFMCap(s) for s in idxStocksDay])

        for s in idxStocksDay:
            s.wightForFactorCheak = computeStockWeight(s, sumWight)

        # compute date i value
        logging.info("===============================================================")
        logging.info("========= stocks information for date %s ==========" % i)

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

    averageProfit, standardDeviation, sharpeRatio = calculateStandardDeviation()
    newIdx['date'] = newIdx['date'].apply(lambda d: parse(d, dayfirst=True).strftime('%Y-%m-%d'))

    writeNewIndexToFile(key, newIdx)
    writeStatisticsToFile(key, sharpeRatio, standardDeviation, averageProfit)
    return newIdx, sharpeRatio, standardDeviation, averageProfit


if __name__ == '__main__':
    df = computeNewIndex(numOfStocks=34, weightLimit=0.07, withUS=False, indexName="TA-35")
    print(df)
