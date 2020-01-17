import datetime
import threading
import json
import websocket # pip install websocket-client==0.47.0
import time
import pandas as pd

import threading # マルチスレッド
from queue import Queue # マルチスレッド

# websocketを使ってtickerをリアルタイム取得
class BfRealtimeTicker(object):
    def __init__(self, symbol):
        self.symbol = symbol
        self.ticker = None
        self.connect()

    def connect(self):
        self.ws = websocket.WebSocketApp(
            'wss://ws.lightstream.bitflyer.com/json-rpc', header=None,
            on_open = self.on_open, on_message = self.on_message,
            on_error = self.on_error, on_close = self.on_close)
        self.ws.keep_running = True 
        self.thread = threading.Thread(target=lambda: self.ws.run_forever())
        self.thread.daemon = True
        self.thread.start()

    def is_connected(self):
        return self.ws.sock and self.ws.sock.connected

    def disconnect(self):
        self.ws.keep_running = False
        self.ws.close()

    def get(self):
        return self.ticker

    def on_message(self, ws, message):
        message = json.loads(message)['params']
        self.ticker = message['message']

    def on_error(self, ws, error):
        self.disconnect()
        time.sleep(0.5)
        self.connect()

    def on_close(self, ws):
        print('Websocket disconnected')

    def on_open(self, ws):
        ws.send(json.dumps( {'method':'subscribe',
            'params':{'channel':'lightning_board_snapshot_' + self.symbol}} )) #板をとる　https://bf-lightning-api.readme.io/docs/realtime-ticker
        print('Websocket connected')


def sim_price(bfrt, position_side = "bids", invest_money = [10**4, 10**5, 10**6, 10**7]):
    try:
        df = pd.DataFrame(bfrt.get()[position_side])
        if position_side == "bids":
            df = df.sort_values('price').reset_index(drop=True)
        else:
            df = df.sort_values('price', ascending=False).reset_index(drop=True)
        df["amount"] = df["price"]*df["size"]
        df["amount_cumsume"] = df["amount"].cumsum()
        return_price = []
        for money in invest_money:
            if money <= df.head(1)["amount"].values[0]:
                return_price.append(df.head(1)["price"].values[0])
            else:
                df_ = df.query("amount_cumsume < @money")
                simprice = df_.amount.sum()/df_["size"].sum() 
                return_price.append(simprice)
        return return_price
    except:
        print("もう一度ロードすべし")

def funcbtc(q, bfrt, position_side, invest_money):
    while True:
        list_ = sim_price(bfrt, position_side, invest_money)
        print("現物のシミュレーション価格１〜1000万円：")
        print(list_ )
        q.put(list_)
        time.sleep(0.2)


def funcfx(q, bfrt, position_side, invest_money):
    while True:
        list_ = sim_price(bfrt, position_side, invest_money)
        print("FXのシミュレーション価格１〜1000万円：")
        print(list_ )
        q.put(list_)
        time.sleep(0.2)

# 使用例
if __name__ == '__main__':
    bfrt_btc = BfRealtimeTicker('BTC_JPY')
    bfrt_fx = BfRealtimeTicker('FX_BTC_JPY')
    q_btc = Queue()
    q_fx = Queue()
    thread1 = threading.Thread(target=funcbtc, args=(q_btc, bfrt_btc, "asks",[10**4, 10**5, 10**6, 10**7]))
    thread2 = threading.Thread(target=funcfx, args=(q_fx, bfrt_fx, "bids",[10**4, 10**5, 10**6, 10**7]))
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    """
    while True:
        print("現物のシミュレーション価格１〜1000万円：")
        print(q_btc.get())
        print("FXのシミュレーション価格１〜1000万円：")
        print(q_fx.get())
    """
        
