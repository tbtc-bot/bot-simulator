import logging
from datetime import datetime
from pathlib import Path
import config
import xml.etree.ElementTree as ET
import pandas as pd
from binance.client import Client


##### LOGGER
logger = logging.getLogger("Log")
logger.setLevel(logging.DEBUG)

# console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# file
fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(filename)s at line %(lineno)s:  %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


##### UTILITIES FUNCTIONS
def loadConfigFile(filePath=None) -> bool:
    if filePath is None:
        filePath = config.CONFIGURATION_FILE
    if fileExists(filePath):
        return parseConfigFile(filePath)
    else:
        logger.error(f"Configuration file not found: {filePath}")
        return False


def parseConfigFile(filePath) -> bool:
    """ Parse the configuration file and set the config.py global variables.
    """
    try:
        root = ET.parse(filePath).getroot()

        config.SYMBOL = root.find('Symbol').text.strip().upper()
        config.INITIAL_EQUITY = float(root.find('InitialEquity').text.strip())
        config.LEVERAGE = int(root.find('Leverage').text.strip())
        config.BUY_SELL = root.find('BuySell').text.strip().upper()

        startDateNode = root.find('StartDate')
        startYear = int(startDateNode.find('StartYear').text.strip())
        startMonth = int(startDateNode.find('StartMonth').text.strip())
        startDay = int(startDateNode.find('StartDay').text.strip())
        startHour = int(startDateNode.find('StartHour').text.strip())
        startMinute = int(startDateNode.find('StartMinute').text.strip())
        config.START_DATE = datetime(startYear, startMonth, startDay, startHour, startMinute, 0)

        endDateNode = root.find('EndDate')
        endYear = int(endDateNode.find('EndYear').text.strip())
        endMonth = int(endDateNode.find('EndMonth').text.strip())
        endDay = int(endDateNode.find('EndDay').text.strip())
        endHour = int(endDateNode.find('EndHour').text.strip())
        endMinute = int(endDateNode.find('EndMinute').text.strip())
        config.END_DATE = datetime(endYear, endMonth, endDay, endHour, endMinute, 0)

        strategyNode = root.find('Strategy')
        config.GO = int(strategyNode.find('GO').text.strip())
        config.GS = float(strategyNode.find('GS').text.strip())
        config.SF = float(strategyNode.find('SF').text.strip())
        config.OS = float(strategyNode.find('OS').text.strip())
        config.OF = float(strategyNode.find('OF').text.strip())
        config.TS = float(strategyNode.find('TS').text.strip())
        config.SL = strategyNode.find('SL').text
        if config.SL is not None:
            config.SL = float(config.SL.strip())

        return True

    except Exception as e:
        logger.error(f"Error parsing configuration file: {e}")
        return False


def fileExists(filePath) -> bool:
    return Path(filePath).is_file()


def loadDataset(filePath) -> pd.DataFrame:
    return pd.read_csv(filePath, parse_dates=['Date'], index_col='Date')


def getSymbolData(filePath) -> pd.DataFrame:
    if not fileExists(filePath):
        logger.info(f"Downloading dataset to: {filePath} ...")
        downloadSymbolData(filePath)

    logger.info(f"Loading dataset ...")
    return loadDataset(filePath)


def downloadSymbolData(filePath) -> None:
        client = Client('', '')
        startTsMs = int(datetime.timestamp(config.START_DATE) * 1000)
        endTsMs = int(datetime.timestamp(config.END_DATE) * 1000)
        klines = client.get_historical_klines(config.SYMBOL, Client.KLINE_INTERVAL_1MINUTE, startTsMs, endTsMs)

        dataDictList = []
        for i in range(len(klines)):
            dataDict = {}
            timestamp = int(klines[i][0] / 1000)
            dataDict['Date'] = datetime.fromtimestamp(timestamp)
            dataDict['Timestamp'] = timestamp
            dataDict['Price'] = float(klines[i][1])
            dataDictList.append(dataDict)

        df = pd.DataFrame(dataDictList)
        df.set_index('Date', inplace=True)

        # create main data folder
        Path(str(Path(filePath).parent)).mkdir(parents=True, exist_ok=True)
        df.to_csv(filePath)