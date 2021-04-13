import util


class Bot:
    """ Defines the strategy and its parameters.
            Receives information from the market engine whenever an order is executed and responds accordingly.
        """
    def __init__(self, symbol, GO, GS, SF, OS, OF, TS, SL):
        self.symbol = symbol
        self.GO = GO
        self.GS = GS
        self.SF = SF
        self.OS = OS
        self.OF = OF
        self.TS = TS
        self.SL = SL

        self.position = None
        self.addOrderCallback = None
        self.cancelOrderCallback = None
        self.getOpenOrdersCallback = None
        self.getEquityCallback = None

    def createInitialGrid(self, startPrice):
        util.logger.debug(f"Create initial grid at price {startPrice}")

    def _setTakeProfit(self, position):
        util.logger.debug(f"Set take profit. Position: {position}")

    def _createSellGrid(self, entryPrice):
        util.logger.debug(f"Create sell grid at entry price: {entryPrice}")

    def _createBuyGrid(self, entryPrice):
        util.logger.debug(f"Create buy grid at entry price: {entryPrice}")

    def _cancelSellGrid(self):
        pass

    def _cancelBuyGrid(self):
        pass


class BotBoth(Bot):
    """ Strategy both.
    """
    def __init__(self, symbol, GO, GS, SF, OS, OF, TS, SL):
        super().__init__(symbol, GO, GS, SF, OS, OF, TS, SL)

    def __str__(self):
        return f"{self.symbol}_BOTH_GO{self.GO}_GS{self.GS}_SF{self.SF}_OS{self.OS}_OF{self.OF}_TS{self.TS}_SL{self.SL}"


    ##### PULBLIC METHODS
    def createInitialGrid(self, startPrice):
        super().createInitialGrid(startPrice)
        self._createSellGrid(startPrice)
        self._createBuyGrid(startPrice)

    def orderExecutedCallback(self, order, position):
        if position.entryPrice is None and order.type != 'TP':
            self.createInitialGrid(order.price)
        elif order.type == 'TP':
            if order.size < 0:
                self._createBuyGrid(order.price)
            else:
                self._createSellGrid(order.price)
        else:
            self._setTakeProfit(position)


    ##### PRIVATE METHODS
    def _setTakeProfit(self, position):
        super()._setTakeProfit(position)
        if position.size < 0:
            self._createBuyGrid(position.entryPrice)
            takeProfitPrice = position.entryPrice * (1 - self.TS / 100)
        else:
            self._createSellGrid(position.entryPrice)
            takeProfitPrice = position.entryPrice * (1 + self.TS / 100)
        self.addOrderCallback(takeProfitPrice, -position.size, gridNumber=-1, type='TP')

    def _createSellGrid(self, entryPrice):
        super()._createSellGrid(entryPrice)
        self._cancelSellGrid()

        p0 = entryPrice
        s0 = (self.getEquityCallback() / p0) * (self.OS / 100)

        ### upper grid
        p_1 = p0 * (1 + self.GS / 100)
        s_1 = -s0
        p_2 = p0
        self.addOrderCallback(p_1, s_1, 1)
        upperGridSize = s_1

        for i in range(2, self.GO + 1):
            p = p_1 + (p_1 - p_2) * self.SF
            s = s_1 * self.OF
            upperGridSize += s
            self.addOrderCallback(p, s, i)
            p_2 = p_1
            p_1 = p
            s_1 = s

        # set upper stop loss
        if self.SL is not None:
            p_SL = p_1 * (1 + self.SL/100)
            self.addOrderCallback(p_SL, -upperGridSize, self.GO+1, 'SL')

    def _createBuyGrid(self, entryPrice):
        super()._createBuyGrid(entryPrice)
        self._cancelBuyGrid()

        p0 = entryPrice
        s0 = (self.getEquityCallback() / p0) * (self.OS / 100)

        ### lower grid
        p_1 = p0 * (1 - self.GS / 100)
        s_1 = s0
        p_2 = p0
        self.addOrderCallback(p_1, s_1, 1)
        lowerGridSize = s_1

        for i in range(-2, -self.GO - 1, -1):
            p = p_1 - (p_2 - p_1) * self.SF
            s = s_1 * self.OF
            lowerGridSize += s
            self.addOrderCallback(p, s, abs(i))
            p_2 = p_1
            p_1 = p
            s_1 = s

        # set lower stop loss
        if self.SL is not None:
            p_SL = p_1 * (1 - self.SL / 100)
            self.addOrderCallback(p_SL, -lowerGridSize, self.GO+1, 'SL')

    def _cancelSellGrid(self):
        ordersToDelete = []
        for order in self.getOpenOrdersCallback():
            if order.size < 0 and order.type != 'SL':
                ordersToDelete.append(order)
            if order.size > 0 and order.type == 'SL':
                ordersToDelete.append(order)
        for order in ordersToDelete:
            self.cancelOrderCallback(order)

    def _cancelBuyGrid(self):
        ordersToDelete = []
        for order in self.getOpenOrdersCallback():
            if order.size > 0 and order.type != 'SL':
                ordersToDelete.append(order)
            if order.size < 0 and order.type == 'SL':
                ordersToDelete.append(order)
        for order in ordersToDelete:
            self.cancelOrderCallback(order)


class BotLong(Bot):
    """ Strategy both.
    """
    def __init__(self, symbol, GO, GS, SF, OS, OF, TS, SL):
        super().__init__(symbol, GO, GS, SF, OS, OF, TS, SL)

    def __str__(self):
        return f"{self.symbol}_LONG_GO{self.GO}_GS{self.GS}_SF{self.SF}_OS{self.OS}_OF{self.OF}_TS{self.TS}_SL{self.SL}"


    ##### PULBLIC METHODS
    def createInitialGrid(self, startPrice):
        super().createInitialGrid(startPrice)
        self._createBuyGrid(startPrice)
        s0 = (self.getEquityCallback() / startPrice) * (self.OS / 100)
        self.addOrderCallback(startPrice, s0, 1, market=True)

    def orderExecutedCallback(self, order, position):
        if position.entryPrice is None:
            self.createInitialGrid(order.price)
        else:
            self._setTakeProfit(position)


    ##### PRIVATE METHODS
    def _setTakeProfit(self, position):
        super()._setTakeProfit(position)
        # TODO cancel previous TP
        takeProfitPrice = position.entryPrice * (1 + self.TS / 100)
        self.addOrderCallback(takeProfitPrice, -position.size, gridNumber=-1, type='TP')

    def _createBuyGrid(self, entryPrice):
        super()._createBuyGrid(entryPrice)
        self._cancelBuyGrid()

        p0 = entryPrice * (1 - self.GS / 100)
        s0 = (self.getEquityCallback() / p0) * (self.OS / 100)

        ### lower grid
        p_1 = p0 * (1 - self.GS / 100)
        s_1 = s0
        p_2 = p0
        self.addOrderCallback(p_1, s_1, 1)
        lowerGridSize = s_1

        for i in range(-2, -self.GO - 1, -1):
            p = p_1 - (p_2 - p_1) * self.SF
            s = s_1 * self.OF
            lowerGridSize += s
            self.addOrderCallback(p, s, abs(i))
            p_2 = p_1
            p_1 = p
            s_1 = s

        # set lower stop loss
        if self.SL is not None:
            p_SL = p_1 * (1 - self.SL / 100)
            self.addOrderCallback(p_SL, -lowerGridSize, self.GO+1, 'SL')

    def _cancelBuyGrid(self):
        ordersToDelete = []
        for openOrder in self.getOpenOrdersCallback():
            ordersToDelete.append(openOrder)
        for order in ordersToDelete:
            self.cancelOrderCallback(order)