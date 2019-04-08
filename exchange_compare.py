#!/usr/bin/env python3

import requests
from pycoingecko import CoinGeckoAPI
import operator
import random


def get_coin_pair_data(exclude=[], include=[]):
    cg = CoinGeckoAPI()
    coins = cg.get_coins_list()
    random.shuffle(coins)
    coin_data = []
    for coin in coins:
        try:
            market_data = cg.get_coin_by_id(coin['id'])['tickers']
            pairs_data = []
            for i in market_data:
                market = i['market']['name']
                price = float(i['converted_last']['usd'])
                volume = float(i['converted_volume']['usd'])
                info = {'market': market,
                        'price': price,
                        'target': i['target'],
                        'volume': volume
                        }
                if len(include) == 0:
                    if market not in exclude:
                        pairs_data.append(info)
                else:
                    if market in include:
                        pairs_data.append(info)
            coin_data.append({'name': i['base'], 'market data': pairs_data})
        except:
            continue
    return (coin_data)


def coins_by_spread(coins, min_volume=5000):
    coins_spread = []
    for coin in coins:
        prices = []
        for m in coin['market data']:
            vol = m['volume']
            if vol >= min_volume:
                prices.append(m['price'])
        if len(prices) > 1:
            spread = ((max(prices) - min(prices)) / min(prices)) * 100
            coins_spread.append({'name': coin['name'], 'spread': spread})
    coins_spread.sort(key=operator.itemgetter('spread'))
    return (coins_spread)


def get_coins_with_spread(min_spread=0.01):
    exchanges = ['Bibox',
                 'Huobi Global',
                 'Poloniex',
                 'Kraken',
                 'Kucoin',
                 'Bittrex',
                 'Binance',
                 'HitBTC',
                 'Upbit',
                 'Coineal'
                 ]
    coins = get_coin_pair_data(include=exhanges)
    coins = coins_by_spread(coins)
    return (coins)


def main():
    coins_spread = get_coins_with_spread()
    for coin in coins_spread:
        spread = 'spread: ' + str(coin['spread'])[:4] + '%'
        print (coin['name'], spread)


if __name__ == "__main__":
    main()
