import matplotlib.pyplot as plt
from simulator import Simulator
import util
import config
import bots
import time
import analysis


# TODO only long/short strategies
# TODO think of other relevant statistical plots
# TODO get data from futures api instead of spot
# TODO progress bar
# TODO GUI


def main():
    if util.loadConfigFile():
        info = "Loaded configuration:"
        info += f"\nSymbol: {config.SYMBOL}"
        info += f"\nInitial Equity: {config.INITIAL_EQUITY}"
        info += f"\nLeverage: {config.LEVERAGE}"
        info += f"\nStart Date: {config.START_DATE}"
        info += f"\nEnd Date: {config.END_DATE}"
        info += f"\nStrategy: GO={config.GO}, GS={config.GS}, SF={config.SF}, OS={config.OS}, OF={config.OF}, SL={config.SL}"
        util.logger.info(info)
    else:
        return

    bot = bots.Bot(config.SYMBOL, GO=config.GO, GS=config.GS, SF=config.SF, OS=config.OS, OF=config.OF, SL=config.SL)
    simulator = Simulator(config.INITIAL_EQUITY, config.START_DATE, config.END_DATE, bot)
    simulator.startSimulation()

    analysis.plotMetrics(simulator.results, str(simulator.bot), simulator.mainDataFolder + f'{simulator.bot}.png')
    # analysis.plotDistributions(simulator.results)
    plt.show()



if __name__=='__main__':
    main()
    time.sleep(0.1)
    input("\nPress Enter to exit")