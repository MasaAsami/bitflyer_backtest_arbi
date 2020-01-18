import datetime
import json
import websocket # pip install websocket-client==0.47.0
import time
import datetime 
import pandas as pd
import datetime 

import threading # マルチスレッド


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

lock = threading.Lock()

def funcbtc(bfrt, position_side, invest_money,results):
    list_ = sim_price(bfrt, position_side, invest_money)
    #print("現物のシミュレーション価格１〜1000万円：")
    #print(list_ )
    lock.acquire()
    lock.release()
    results[datetime.datetime.now()] = list_
    if len(results) > 1000000:
        del results[list(results.keys())[0]]


def funcfx(bfrt, position_side, invest_money,results):
    list_ = sim_price(bfrt, position_side, invest_money)
    #print("FXのシミュレーション価格１〜1000万円：")
    #print(list_ )
    lock.acquire()
    lock.release()
    results[datetime.datetime.now()] = list_
    if len(results) > 1000000:
        del results[list(results.keys())[0]]

def funcdiff(results_btc, results_fx, results_diff):
    last_btc = list(results_btc.keys())[-1]
    last_fx = list(results_fx.keys())[-1]
    last_btc_list = results_btc[last_btc]
    last_fx_list = results_fx[last_fx]
    diff_list = [last_fx_list[i] - last_btc_list[i] for i in range(len(last_fx_list))]
    diff_list = [diff_list[i]/last_btc_list[i] for i in range(len(last_btc_list))]
    print("乖離 １〜1000万円：")
    print(diff_list)
    results_diff[datetime.datetime.now()] = diff_list
    # btc_df = pd.DataFrame(results_btc).T
    # fx_df = pd.DataFrame(results_fx).T
    # col_ = ["m_1", "m_2", "m_3", "m_4"]
    # btc_df.columns = col_
    # fx_df.columns = col_
    # btc_df.to_csv("btc_df.csv")
    # fx_df.to_csv("fx_df.csv")

# 使用例
if __name__ == '__main__':
    bfrt_btc = BfRealtimeTicker('BTC_JPY')
    bfrt_fx = BfRealtimeTicker('FX_BTC_JPY')

    results_btc = dict()
    results_fx = dict()
    results_diff = dict()
    for k in range(100000):
        thread1 = threading.Thread(target=funcbtc, args=(bfrt_btc, "asks",[10**4, 10**5, 10**6, 10**7],results_btc))
        thread2 = threading.Thread(target=funcfx, args=(bfrt_fx, "bids",[10**4, 10**5, 10**6, 10**7],results_fx))
        thread3 = threading.Thread(target=funcdiff, args=(results_btc, results_fx,results_diff))
        thread1.start()
        thread2.start()
        thread3.start()
    
        thread1.join()
        thread2.join()
        thread3.join()
        time.sleep(0.2)
    
    #print(results_btc)
    btc_df = pd.DataFrame(results_btc).T
    fx_df = pd.DataFrame(results_fx).T
    diff_df = pd.DataFrame(results_diff).T
    col_ = ["m_1", "m_2", "m_3", "m_4"]
    btc_df.columns = col_
    fx_df.columns = col_
    diff_df.columns = col_
    btc_df.to_csv("btc_df.csv")
    fx_df.to_csv("fx_df.csv")
    diff_df.to_csv("diff_df.csv")

    # print("現物のシミュレーション価格１〜1000万円：")
    # btc = q_btc.get()
    # print(btc)
  
    # print("FXのシミュレーション価格１〜1000万円：")
    # fx = q_fx.get()
    # print(fx)

    # try:
    #     diff_list = [fx[i] - btc[i] for i in range(len(fx))]
    #     diff_list = [diff_list[i]/btc[i] for i in range(len(btc))]
    #     print("乖離 １〜1000万円：")
    #     print(diff_list)
    # except:
    #     print("...")

  
    # while True:
    #     lock.acquire() 
    #     print("現物のシミュレーション価格１〜1000万円：")
    #     btc = q_btc.get()
    #     print(btc)
    #     lock.release()
    #     lock.acquire() 
    #     print("FXのシミュレーション価格１〜1000万円：")
    #     fx = q_fx.get()
    #     print(fx)
    #     lock.release()
    #     try:
    #       diff_list = [fx[i] - btc[i] for i in range(len(fx))]
    #       diff_list = [diff_list[i]/btc[i] for i in range(len(btc))]
    #       print("乖離 １〜1000万円：")
    #       print(diff_list)
    #     except:
    #       print("...")
