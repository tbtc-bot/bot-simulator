import pandas as pd
from datetime import datetime
import config
import util


class Order:
    """ An order is defined by price, position size, grid number and type. All orders are considered limit orders.
    """
    staticId = 0

    def __init__(self, price, size, gridNumber, type, market):
        self.id = Order.staticId
        Order.staticId += 1
        self.price = price
        self.size = round(size,3)
        self.gridNumber = gridNumber
        self.type = type # Type: '' = normal, 'TP' = take profit, 'SL' = stop loss.
        self.market = market
        self.fee = MarketEngine.ORDER_FEE_PERCENTAGE/100 * self.price * abs(self.size) # fee associated to the order

    def __str__(self):
        return f"Price: {self.price}, size: {self.size}, gridNumber: {self.gridNumber}, type: {self.type}, market: {self.market}"


class Position:
    """ The open position is defined by an entry price and a position size.
        ROE and PNL can be computed given the mark price.
    """
    def __init__(self, entryPrice=None, size=0):
        self.entryPrice = entryPrice
        self.size = size

    def __str__(self):
        return f"Entry price: {self.entryPrice}, size: {self.size}"

    def update(self, order):
        self.entryPrice = (self.entryPrice * self.size + order.price * order.size) / (self.size + order.size)
        self.size += order.size

    def getROE(self, markPrice):
        return (markPrice - self.entryPrice) / self.entryPrice * 100 * config.LEVERAGE * self.size / abs(self.size)

    def getPNL(self, markPrice):
        return markPrice * abs(self.size) / config.LEVERAGE * self.getROE(markPrice) / 100


class MarketEngine:
    """ Simulates the behaviour of an exchange.
        Handles the order executions based on the mark price and updates the open positions each time an order is executed.
    """
    ORDER_FEE_PERCENTAGE = 0.02

    def __init__(self):
        self.equity = config.INITIAL_EQUITY
        self.openOrders = {}
        self.position = Position()
        self.lastGridReached = None
        self.grossProfit = None
        self.netProfit = None
        self.cumulativeFee = 0
        self.dictList = []
        self.orderExecutedCallback = None


    ##### PUBLIC METHODS
    def startSimulation(self, df):
        nPoints = len(df['Timestamp'])
        for i in range(1, nPoints):
            if i % 10000 == 0:
                util.logger.info(f"{round(i/nPoints*100, 2)} %")
            self.timestamp = df['Timestamp'][i]
            self.markPrice = df['Price'][i]
            ordersToExecute = self._getOrdersToExecute(self.markPrice)
            if len(ordersToExecute) > 0:
                # print(datetime.fromtimestamp(self.timestamp))
                # self.printGrid()
                for order in ordersToExecute:
                    util.logger.debug(f"Position before order: {self.position}")
                    self._executeOrder(order)
                    util.logger.debug(f"Position after order: {self.position}")
                    self._addDataframeRow(order)
            else:
                self.grossProfit = None
                self._addDataframeRow()

        util.logger.info("Simulation done")

    def addOrder(self, price, size, gridNumber, type='', market=False):
        order = Order(price, size, gridNumber, type, market)
        self.openOrders[order.id] = order

    def cancelOrder(self, order):
        if order.id in self.openOrders:
            del self.openOrders[order.id]

    def getOpenOrders(self):
        return self.openOrders.values()

    def cancelAllOrders(self):
        self.openOrders = {}

    def getEquity(self):
        return self.equity

    def getResults(self):
        df = pd.DataFrame(self.dictList) # convert the list of dictionaries in a pandas dataframe
        df['Date'] = [datetime.fromtimestamp(ts) for ts in df['Timestamp']] # add a column with a date format
        df.set_index('Date', inplace=True) # set the date column as index of the dataframe
        return df


    ##### PRIVATE METHODS
    def _executeOrder(self, order):
        util.logger.debug(f"[{datetime.fromtimestamp(self.timestamp)}] Mark price: {self.markPrice}. Execute order: {order}")
        if self.position.entryPrice is None:
            self.position = Position(order.price, order.size)
            self.grossProfit = None
            self.netProfit = None
            self.lastGridReached = order.gridNumber
            self.cumulativeFee += order.fee
        else:
            if order.type=='TP':
                self._takeProfit(order)
            elif order.type=='SL':
                self._stopLoss(order)
                self.lastGridReached = order.gridNumber
            else:
                # increase position
                if self.position.size * order.size <= 0:
                    util.logger.error(f"[{datetime.fromtimestamp(self.timestamp)}] Position should be increasing")
                self.position.update(order)
                self.grossProfit = None
                self.netProfit = None
                self.lastGridReached = order.gridNumber
                self.cumulativeFee += order.fee

        self.equity -= order.fee
        self.cancelOrder(order)
        self.orderExecutedCallback(order, self.position)

    def _takeProfit(self, order):
        if (self.position.size + order.size) > 0.0001:
            util.logger.error("Take profit did not reduce position to zero")
        self.grossProfit = self.position.getPNL(order.price)
        self.equity += self.grossProfit
        self.cumulativeFee += order.fee
        self.netProfit = self.grossProfit - self.cumulativeFee
        self.cumulativeFee = 0
        self.position = Position()

    def _stopLoss(self, order):
        self.grossProfit = self.position.getPNL(order.price)
        self.equity += self.grossProfit
        self.cumulativeFee += order.fee
        self.netProfit = self.grossProfit - self.cumulativeFee
        self.cumulativeFee = 0
        self.position = Position()
        self.cancelAllOrders()

    def _getOrdersToExecute(self, markPrice):
        """ Returns a list of order to be executed. """
        ordersToExecute = []
        takeProfitOrder = None
        stopLossOrder = None
        for order in self.openOrders.values():
            # if market order, execute at mark price
            if order.market:
                order.price = markPrice
                ordersToExecute.append(order)
                continue

            # if limit order, define buy and sell conditions
            if order.type=='SL':
                if (order.size < 0 and markPrice <= order.price) or (order.size > 0 and markPrice >= order.price):
                    stopLossOrder = order
            else:
                triggerBuy = order.size > 0 and markPrice <= order.price
                triggerSell = order.size < 0 and markPrice >= order.price
                if triggerBuy or triggerSell:
                    if order.type=='TP':
                        takeProfitOrder = order
                    else:
                        ordersToExecute.append(order)

        # make sure that the take profit is executed first to simplify the simulation
        if takeProfitOrder is not None:
            return [takeProfitOrder] + ordersToExecute

        # make sure that the stop loss is executed last to simplify the simulation
        elif stopLossOrder is not None:
            return ordersToExecute + [stopLossOrder]

        else:
            return ordersToExecute

    def _addDataframeRow(self, order=None):
        """ Builds a list of dictionaries with all the relevant data about the simulation. """
        lastGridReached = self.lastGridReached
        orderSize = None
        orderPrice = None
        orderFee = None
        grossProfit = None
        netProfit = None
        if order is not None:
            lastGridReached = abs(self.lastGridReached)
            orderSize = order.size
            orderPrice = order.price
            orderFee = order.fee
            grossProfit = self.grossProfit
            netProfit = self.netProfit

        tmp = dict()
        tmp['Timestamp'] = self.timestamp
        tmp['MarkPrice'] = self.markPrice
        tmp['PositionSize'] = self.position.size
        tmp['EntryPrice'] = self.position.entryPrice
        tmp['GridReached'] = lastGridReached
        tmp['Equity'] = self.equity
        tmp['OrderSize'] = orderSize
        tmp['OrderPrice'] = orderPrice
        tmp['Fee'] = orderFee
        tmp['GrossProfit'] = grossProfit
        tmp['NetProfit'] = netProfit
        if self.position.entryPrice is not None:
            tmp['ROE %'] = self.position.getROE(self.markPrice)
            tmp['PNL'] = self.position.getPNL(self.markPrice)
            tmp['Drawdown %'] = tmp['PNL'] / self.equity * 100
        else:
            tmp['ROE %'] = None
            tmp['PNL'] = None
            tmp['Drawdown %'] = None

        self.dictList.append(tmp)


    # for debug purposes
    def printGrid(self):
        priceToOrderDict = {}
        for order in self.openOrders.values():
            priceToOrderDict[order.price] = order

        orderPrices = list(priceToOrderDict.keys())
        orderPrices.sort(reverse=True)
        for p in orderPrices:
            print(f"----- {priceToOrderDict[p].gridNumber} -> price: {p:.2f}, size: {priceToOrderDict[p].size:.3f}")