import argparse
import threading
import time
import logging

import finnhub

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *


class IBapi(EWrapper, EClient):
	def __init__(self):
		EClient.__init__(self, self)
	def nextValidId(self, orderId: int):
		super().nextValidId(orderId)
		self.nextorderId = orderId
		print('The next valid order id is: ', self.nextorderId)
	def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
		print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
	def openOrder(self, orderId, contract, order, orderState):
		print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status)
	def execDetails(self, reqId, contract, execution):
		print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)

def create_contract(symbol, sec_type, exch, curr):
    """Create a Contract object defining what will
    be purchased, at which exchange and in which currency.

    symbol - The ticker symbol for the contract
    sec_type - The security type for the contract ('STK' is 'stock')
    exch - The exchange to carry out the contract on
    prim_exch - The primary exchange to carry out the contract on
    curr - The currency in which to purchase the contract"""
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exch
    contract.currency = curr
    return contract

def amount_of_shares_to_buy(cash, price_per_share):
	if price_per_share == 0:
		return -1
	else:
		return int(cash / price_per_share)

def create_order(order_type, shares_quantity, action):
    """Create an Order object (Market/Limit) to go long/short.

    order_type - 'MKT', 'LMT' for Market or Limit orders
    quantity - Integral number of assets to order
    action - 'BUY' or 'SELL'"""
    order = Order()
    order.orderType = order_type
    order.action = action
    order.totalQuantity = shares_quantity
    return order

def run_loop():
	app.run()


if __name__ == "__main__":
	logging.basicConfig(
		format='%(asctime)s %(levelname)-8s %(message)s',
		level=logging.INFO,
		datefmt='%Y-%m-%d %H:%M:%S')
	logging.getLogger().setLevel(logging.INFO)

	parser = argparse.ArgumentParser()
	parser.add_argument('--stock', type=str, required=True, help='a stock to buy')
	parser.add_argument('--cash-quintity', type=int, required=True, help='how much USD to use in order to buy the stock')
	parser.add_argument('--api-key', type=str, required=True, help='API key')
	parser.add_argument('--order', type=str, default="MKT", help='Option of orders: MKT, LMT, etc')
	parser.add_argument('--action', type=str, default="BUY", help='Action of orders: BUY or SELL')
	args = parser.parse_args()

	# Basic auth into Interactive Brokers using TWS
	app = IBapi()
	app.connect('127.0.0.1', 7496, 1)
	app.nextorderId = 0

	# Start the socket in a thread
	api_thread = threading.Thread(target=run_loop, daemon=True)
	api_thread.start()
	# Sleep interval to allow time for connection to server
	time.sleep(1) 

	symbol = args.stock.upper()
	logging.info(f"--------------------------------------")
	logging.info(f"-- Symbol: {symbol}")
	contract = create_contract(symbol, 'STK', 'SMART', 'USD')
	finnhub_client = finnhub.Client(api_key=args.api_key)
	price_per_share  = finnhub_client.quote(symbol)['c']
	if price_per_share == 0:
		raise ValueError("Price of share is 0. That means that API KEY is not right or that there isn't such stock")
	else:
		logging.info(f"-- Price per share of {symbol} is: {price_per_share}$")
		number_of_shares = amount_of_shares_to_buy(args.cash_quintity, price_per_share)
		if number_of_shares == -1:
			logging.error("-- Not enough money to buy a share")
		else:
			order = create_order(args.order, number_of_shares, args.action) # Order in Dollars
			logging.info(f"-- Going to {args.action} {number_of_shares} stock of {symbol} at total price of {number_of_shares * price_per_share }$ using {args.order} order")
			app.placeOrder(app.nextorderId, contract, order)
			time.sleep(0.5)
	app.disconnect()
