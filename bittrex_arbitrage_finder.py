#!/usr/bin/env python3

from bittrex.bittrex import Bittrex, API_V2_0
from random import shuffle
import random
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
import numpy as np
import operator


def date(a_string):
    return (datetime.strptime(a_string, '%Y-%m-%dT%H:%M:%S'))


def get_markets():
    data = Bittrex(None, None).get_markets()['result']
    markets = []
    for i in data:
        markets.append(i['MarketName'])
    return (markets)


def get_interval(date, interval, add=False):
    minute = 60
    intervals = {'oneMin': minute,
                 'fiveMin': minute * 5,
                 'hour': minute * 60,
                 'thirtyMin': minute * 30,
                 'Day': (minute * 60) * 24,
                 }
    delta = timedelta(seconds=intervals[interval])
    if add:
        return (date + delta)
    else:
        return (date - delta)


def fill_missing_candles(candles, interval):
    '''
    illiquid pairs with no trades in an interval do not report back from the
    API so to normalize the data we fill in the missing price ticks here.
    '''
    filled_list = [candles[0]]
    index = 0
    for c in candles[1:]:
        timestamp = date(c['T'])
        last_timestamp = date(candles[index]['T'])
        last_tick = get_interval(timestamp, interval)
        while last_timestamp != last_tick:
            last_timestamp = get_interval(last_timestamp, interval, add=True)
            t = str(last_timestamp).split()
            n = c.copy()
            n['T'] = t[0] + 'T' + t[1]
            n['BV'] = 0.0
            n['V'] = 0.0
            filled_list.append(n)
        filled_list.append(c)
        index += 1
    return (filled_list)


def convert_prices(candles, converter):
    '''
    Converts prices to converter (USD)
    '''
    new_candles = []
    for c in candles:
        try:
            price = float(c['O'])
            timestamp = c['T']
            rate = converter[timestamp]
            new_price = price * rate
            c['USD'] = new_price
            new_candles.append(c)
        except:
            continue
    return (new_candles)


def get_anchors(interval):
    b = Bittrex(None, None, api_version='v2.0')
    btc = b.get_candles('USDT-BTC', interval)['result']
    btc = fill_missing_candles(btc, interval)
    eth = b.get_candles('USDT-ETH', interval)['result']
    eth = fill_missing_candles(eth, interval)
    anchors = {'BTC': btc, 'ETH': eth}
    new_anchors = {}
    for key in anchors:
        new = {}
        for i in anchors[key]:
            new[i['T']] = float(i['O'])
        new_anchors[key] = new
    return (new_anchors)


def get_usd(data):
    new_data = []
    for i in data:
        new_data.append(i['USD'])
    return (new_data)


def get_market_data(markets, interval='thirtyMin', convert=True):
    bittrex = Bittrex(None, None, api_version='v2.0')
    anchors = get_anchors(interval)
    data = {}
    for pair in markets:
        anchor = pair.split('-')[0]
        currency = pair.split('-')[1]
        if currency not in data.keys():
            data[currency] = []
        candles = bittrex.get_candles(pair, interval)['result']
        if candles is None:
            candles = fill_missing_candles(candles, interval)
            if 'USD' not in anchor:
                if convert:
                    converter = anchors[anchor]
                    candles = convert_prices(candles, converter)
            else:
                new_candles = []
                for c in candles:
                    c['USD'] = c['O']
                    new_candles.append(c)
                candles = new_candles
            data[currency].append(candles)
    return (data)


def get_biggest_differences(prices):
    '''
    finds biggest spread in a list of time series data
    and returns the spread between each candle.
    '''
    diffs = []
    for p in prices:
        s = sum(p)
        diffs.append(s)
    max_ = diffs.index(max(diffs))
    min_ = diffs.index(min(diffs))
    spread = []
    index = 0
    for p in prices[max_]:
        m = prices[min_]
        m = m[index]
        p = abs(p - m)
        spread.append(p)
        index += 1
    average_price = np.mean([np.mean(prices[min_]), np.mean(prices[max_])])
    average_spread = np.mean(spread)
    percent_spread = (average_spread / average_price) * 100
    return (spread, percent_spread)


def plot(data, bars, name):
    style = 'seaborn'
    plt.style.use(style)
    count = 1
    for d in data:
        plt.plot(d, label='pair ' + str(count))
        count += 1
    plt.bar(range(0, len(bars)),
            bars, color='#ff561e',
            label='price difference'
            )
    plt.xlabel(name)
    plt.ylabel('USD price')
    plt.legend()
    plt.savefig('imgs/' + name + '.png')
    plt.clf()


def fixed_lengths(prices):
    new_prices = []
    length = 10000000000
    for p in prices:
        if len(p) < length:
            length = len(p)
    for p in prices:
        new_prices.append(p[-length:])
    return (new_prices)


def main():
    pairs = get_markets()
    # shuffle(pairs) us this for testing
    data = get_market_data(pairs)
    multi_pairs = {}
    for coin in data:
        if len(data[coin]) > 1:
            multi_pairs[coin] = data[coin]
    sorted_pairs = []
    for coin in multi_pairs:
        prices = []
        multi_pairs[coin] = fixed_lengths(multi_pairs[coin])
        for p in multi_pairs[coin]:
            index = 0
            for i in p:
                index += 1
            p = get_usd(p)
            prices.append(p)
        spread = get_biggest_differences(prices)
        pair_data = {'prices': prices,
                     'spread': spread[0],
                     'avg_spread': spread[1],
                     'coin': coin
                     }
        sorted_pairs.append(pair_data)
    sorted_pairs.sort(key=operator.itemgetter('avg_spread'))
    for p in sorted_pairs:
        print (p['coin'], str(p['avg_spread'])[:5])
        name = str(p['avg_spread'])[:5] + '% ' + p['coin']
        plot(p['prices'], p['spread'], name)


if __name__ == "__main__":
    main()
