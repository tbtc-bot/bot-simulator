import matplotlib.pyplot as plt
from simulator import Simulator
import util
import config
import bots
import time
import analysis


# v1.0.0
# TODO fix profit distribution with stop loss
# TODO think of other relevant statistical plots
# TODO get data from futures api instead of spot


def main():
    if util.loadConfigFile():
        info = "\nLoaded configuration:"
        info += f"\nSymbol: {config.SYMBOL}"
        info += f"\nInitial Equity: {config.INITIAL_EQUITY}"
        info += f"\nLeverage: {config.LEVERAGE}"
        info += f"\nStart Date: {config.START_DATE}"
        info += f"\nEnd Date: {config.END_DATE}"
        info += f"\nStrategy: GO={config.GO}, GS={config.GS}, SF={config.SF}, OS={config.OS}, OF={config.OF}, SL={config.SL}"
        util.logger.info(info)
    else:
        return

    if config.BUY_SELL == 'BOTH':
        bot = bots.BotBoth(config.SYMBOL, GO=config.GO, GS=config.GS, SF=config.SF, OS=config.OS, OF=config.OF, TS = config.TS, SL=config.SL)
    elif config.BUY_SELL == 'LONG':
        bot = bots.BotLong(config.SYMBOL, GO=config.GO, GS=config.GS, SF=config.SF, OS=config.OS, OF=config.OF, TS = config.TS, SL=config.SL)
    else:
        util.logger.error(f"{config.BUY_SELL} is not a valid strategy")
        return

    simulator = Simulator(config.INITIAL_EQUITY, config.START_DATE, config.END_DATE, bot)
    simulator.startSimulation()

    analysis.plotMetrics(simulator.results, str(simulator.bot), simulator.mainDataFolder + f'{simulator.bot}.png')
    analysis.plotDistributions(simulator.results, simulator.mainDataFolder + f'{simulator.bot}_distr.png')
    plt.show()



if __name__=='__main__':
    main()
    time.sleep(0.1)
    input("\nPress Enter to exit")