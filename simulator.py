import util
from market_engine import MarketEngine


class Simulator:
    """ Handles general information and configuration of the simulation.
        Links the bot with the market engine through callbacks.
    """
    def __init__(self, initialEquity, startDate, endDate, bot):
        self.initialEquity = initialEquity
        self.startDate = startDate
        self.endDate = endDate
        self.bot = bot
        self.mainDataFolder = self._getMainDataFolder()
        self.resultsFilePath = self.mainDataFolder + f'{self.bot}.csv'

        self.market = MarketEngine()

        # link bot and market through callbacks
        self.bot.addOrderCallback = self.market.addOrder
        self.bot.cancelOrderCallback = self.market.cancelOrder
        self.bot.getOpenOrdersCallback = self.market.getOpenOrders
        self.bot.getEquityCallback = self.market.getEquity
        self.market.orderExecutedCallback = self.bot.orderExecutedCallback

    def startSimulation(self):
        # load results if already available, perform the simulation otherwise

        if util.fileExists(self.resultsFilePath):
            util.logger.info(f"Results for this simulation are already available: {self.resultsFilePath}")
            self.results = util.loadResults(self.resultsFilePath)
        else:
            symbolDataFilePath = self.mainDataFolder + self.bot.symbol + '_candles.csv'
            symbolData = util.getSymbolData(symbolDataFilePath)

            util.logger.info("Simulation started")
            self.bot.createInitialGrid(startPrice=symbolData['Open'][0])
            self.market.startSimulation(symbolData)

            self.results = self.market.getResults()
            self.results.to_csv(self.resultsFilePath)
            util.logger.info(f"Results saved in {self.mainDataFolder}")

    def _getMainDataFolder(self):
        """ The data folder of a simulation is defined by the start and end dates.
            It has the format: datasets/yyyy-MM-dd-hhh-mmm_yyyy-MM-dd-hhh-mmm/
        """
        startDateString = f"{self.startDate.year}-{self.startDate.month:02d}-{self.startDate.day:02d}-{self.startDate.hour:02d}h-{self.startDate.minute:02d}m"
        endDateString = f"{self.endDate.year}-{self.endDate.month:02d}-{self.endDate.day:02d}-{self.endDate.hour:02d}h-{self.endDate.minute:02d}m"
        return f'datasets/{startDateString}_{endDateString}/'