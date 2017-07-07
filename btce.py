#!/usr/bin/env python

from decimal import Decimal as d
from decimal import getcontext
from threading import Thread
from operator import itemgetter
from debug import debug
import btcelib
import myconfig
import time


# Configuration Variables Call
key = myconfig.KEY
secret = myconfig.SECRET
pair_list = myconfig.PAIRS
amount_to_trade = d(myconfig.AMOUNT / 100)
minimum_to_trade = d(myconfig.MINIMUM)
fee = d(myconfig.FEE / 100)
loop_time = myconfig.LOOP
order_timeout = myconfig.ORDER_TIMEOUT
debug_conf = myconfig.DEBUG

getcontext().prec = 8

# Debugging system initialize
if debug_conf:
    debug_status = 1


def debug(message, *date):
    if not date:
        date = time.ctime()
    msg = '[DEBUG]: %s: %s' % (date, message)
    if debug_status == 1:
        print msg
    elif debug_status == 0:
        f = open('debug.log')
        f.write(msg)
        f.close()


# Pair handler function
def pair_handler():
    if len(pair_list) > 1:
        result = '-'.join(pair_list)
        return result
    return pair_list


class Infos:

    def __init__(self, *pair):
        self.api = btcelib.PublicAPIv3(pair)
        self.tapi = btcelib.TradeAPIv1({'Key': key, 'Secret': secret})

    def ticker(self, *pair):
        result = {}
        if pair:
            self.__init__(pair)
        data = self.api.call('ticker')
        result['buy'] = data.values()[0]['buy']
        result['last'] = data.values()[0]['last']
        result['sell'] = data.values()[0]['sell']
        yield result

    def trade_hist(self, pair):
        result = {}
        data = self.tapi.call('TradeHistory', pair=pair)
        response = sorted(data.values(), key=itemgetter('timestamp'), reverse=True)
        for trades in response:
            result['timestamp'] = trades['timestamp']
            result['rate'] = trades['rate']
            result['amount'] = trades['amount']
            result['type'] = trades['type']
            result['pair'] = trades['pair']
            yield result

    def funds(self, pair):
        result = {}
        asset, cur = pair.split('_')[0], pair.split('_')[1]
        data = self.tapi.call('getInfo')
        result[asset] = data['funds'][asset]
        result[cur] = data['funds'][cur]
        debug(result)
        return result

    def active_orders(self):
            data = self.tapi.call('ActiveOrders')
            for orders in data.keys():
                try:
                    yield orders
                except btcelib.APIError:
                    pass

    # This action has been placed into Infos class to ease the management of the threads.
    def cancel_order(self, order_id):
        debug('Cancelling order: %g' % order_id)
        return self.tapi.call('CancelOrder', order_id=order_id)


class MyThread(Thread):

        def __init__(self, name):
            Thread.__init__(self)
            self.name = name

        def run(self):
            for order in Infos().active_orders():
                time.sleep(order_timeout)
                return Infos().cancel_order(order_id=order)


class Actions:

    def __init__(self):
        self.tapi = btcelib.TradeAPIv1({'Key': key, 'Secret': secret})

    def buy(self, pair):
        for rate in Infos().ticker(pair):
            rate = rate['buy']
        if 'btc' in pair.split('_'):
            amount = amount_to_trade * Infos().funds(pair)['btc']
        else:
            amount = amount_to_trade * Infos().funds(pair).values()[0] * rate
        thread = MyThread("%g:%s:%g" % (d(amount), pair, d(rate)))
        try:
            debug('Buying %g of %s @ %g...' % (d(amount), pair, rate))
            return self.tapi.call(
                'Trade',
                pair=pair,
                type='buy',
                amount=amount,
                rate=rate), thread.start()
        except:
            try:
                debug('Buying %g of %s @ %g...' % (minimum_to_trade, pair, rate))
                return self.tapi.call(
                    'Trade',
                    pair=pair,
                    type='buy',
                    amount=minimum_to_trade,
                    rate=rate), thread.start()
            except btcelib.APIError:
                debug('Not enough funds. Passing...')
                pass

    def sell(self, pair):
        for rate in Infos().ticker(pair):
            rate = rate['buy']
        if 'btc' in pair.split('_'):
            amount = amount_to_trade * Infos().funds(pair)['btc']
        else:
            amount = amount_to_trade * Infos().funds(pair).values()[0] * rate
        thread = MyThread("%g:%s:%g" % (d(amount), pair, d(rate)))
        try:
            debug('Selling %g of %s @ %g...' % (amount, pair, rate))
            return self.tapi.call(
                'Trade',
                pair=pair,
                type='sell',
                amount=amount,
                rate=rate), thread.start()
        except:
            try:
                debug('Selling %g of %s @ %g...' % (amount_to_trade, pair, rate))
                return self.tapi.call(
                    'Trade',
                    pair=pair,
                    type='sell',
                    amount=minimum_to_trade,
                    rate=rate), thread.start()
            except btcelib.APIError:
                debug('Not enough funds. Passing...')
                pass


class Rules:

    @staticmethod
    def rule_buy_1(pair):
        for rate in Infos().ticker(pair):
            rate = rate['buy']
        for price in Infos().trade_hist(pair):
            if price['type'] == 'buy':
                price = price['rate']
                debug('Testing rule_buy_1: %s > %s' % (rate, price))
                if rate > price:
                    return True
                else:
                    return False

    @staticmethod
    def rule_buy_2(pair):
        for rate in Infos().ticker(pair):
            rate = rate['buy']
        for price in Infos().trade_hist(pair):
            if price['type'] == 'buy':
                price = price['rate']
                frate = rate - rate * fee
                fprice = price + price * fee
                debug('Testing rule_buy_2: %s > %s' % (frate, fprice))
                if frate > fprice:
                    return True
                else:
                    return False

    @staticmethod
    def rule_sell_1(pair):
        for rate in Infos().ticker(pair):
            rate = rate['sell']
            for price in Infos().trade_hist(pair):
                if price['type'] == 'sell':
                    price = price['rate']
                    debug('Testing rule_sell_1: %s < %s' % (rate, price))
                    if rate < price:
                        return True
                    else:
                        return False

    @staticmethod
    def rule_sell_2(pair):
        for rate in Infos().ticker(pair):
            rate = rate['sell']
            for price in Infos().trade_hist(pair):
                if price['type'] == 'sell':
                    price = price['rate']
                    frate = rate + rate * fee
                    fprice = price - price * fee
                    debug('Testing rule_sell_2: %s < %s' % (frate, fprice))
                    if frate < fprice:
                        return True
                    else:
                        return False


def main_loop():
    for pair in pair_list:
        debug("main process: %s" % pair)
        if Rules().rule_buy_1(pair) and Rules().rule_buy_2(pair):
            return Actions().buy(pair)
        if Rules().rule_sell_1(pair) and Rules().rule_sell_2(pair):
            return Actions().sell(pair)
    time.sleep(loop_time)


if __name__ == '__main__':
    while True:
        main_loop()
