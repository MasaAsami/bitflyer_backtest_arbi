# -*- coding:utf-8 -*-

import json
import requests
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt


def crypto_watch(candle, before, size, ticker="btcfxjpy"):
    url = f"https://api.cryptowat.ch/markets/bitflyer/{ticker}/ohlc?periods="
    candle = candle * 60
    period = "%s" % (candle)
    period = [period]
    beforeurl = "&before="
    afterurl = "&after="
    # The maximum size of datas is 6000 depending on a timing (sometimes you get less than 6000)
    after = before - (candle * size)
    URL = "%s%s%s%s%s%s" % (url, candle, afterurl, after, beforeurl, before)
    # e.g https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc?periods=86400&after=1483196400
    res = json.loads(requests.get(URL).text)["result"]
    data = []
    for i in period:
        row = res[i]
        for column in row:
            if column[4] != 0:
                column = column[0:6]
                data.append(column)
    date = [price[0] for price in data]
    priceOpen = [int(price[1]) for price in data]
    priceHigh = [int(price[2]) for price in data]
    priceLow = [int(price[3]) for price in data]
    priceClose = [int(price[4]) for price in data]
    date_datetime = map(datetime.datetime.fromtimestamp, date)
    dti = pd.DatetimeIndex(date_datetime)
    df_candleStick = pd.DataFrame(
        {"open": priceOpen, "high": priceHigh, "low": priceLow, "close": priceClose},
        index=dti,
    )
    return df_candleStick


def backtest_data(timespan=1, plot_on=False):
    """
    timespan: バックデータのデータ期間　最小単位が１分
    　　　　　　[1, 3, 5, 15, 30, 60, 120, 240, 360]等が選択可能
            　 但し、大きすぎると、荒くなってシミュレーションの意味がない
               https://qiita.com/iw_at_t/items/73e3201aa091a04ff248
    return df
    """
    assert timespan in [1, 3, 5, 15, 30, 60, 120, 240, 360], "timespanは[1, 3, 5, 15, 30, 60, 120, 240, 360](分)から選んでね"

    fx = crypto_watch(timespan, round(time.time()), 5000000)
    re = crypto_watch(timespan, round(time.time()), 5000000, ticker="btcjpy")

    re.columns = ["btc_open", "btc_high", "btc_low", "btc_close"]
    fx.columns = ["fx_open", "fx_high", "fx_low", "fx_close"]
    df = pd.merge(re, fx, left_index=True, right_index=True)

    df["diff_ratio"] = (df["fx_close"] - df["btc_close"]) / df["btc_close"]  # 乖離を計算
    df["date"] = df.index.strftime("%Y/%m/%d")

    if plot_on:
        df["diff_ratio"].plot()
        plt.show()
    
    return df

def backtest_sim(
        df, position_start_cutpoint, position_close_cutpoint
    ):
    """
    input:
    df: pandas DataFrame
    ポジション開始閾値: 前日の乖離中央値 + position_start_cutpoint
    ポジション解消閾値: ポジション開始閾値　- position_close_cutpoint
    retuern:
    シミュレーション結果：何回取引できたの？等のログを確認
    """
    event_count = 0  # これに足していく
    on_position = 0  # 今ポジションしてるの？？
    position_point = 0  # positionしたときの乖離
    day_unique = list(df.date.unique())  # 日付のリスト
    start_list = []
    end_list = []
    
    print(f"{day_unique[1]} ⇨ {day_unique[-1]}のシミュレーション ({len(day_unique)-1}日間）")
    for i in range(len(df)):
        simtime = df.index[i]
        simday = simtime.strftime("%Y/%m/%d")
        if day_unique.index(simday) != 0:  # 初日は取引しない
            th_point = (
                df[
                    df.date == day_unique[day_unique.index(simday) - 1] # 1日前のデータを指定している
                ].diff_ratio.median()
                + position_start_cutpoint
            )  # 前日の乖離中央値 + 指定乖離%の出来上がり

            now_diff_ratio = df.loc[simtime, "diff_ratio"]
            if now_diff_ratio >= th_point and on_position == 0:
                print(f"ポジション開始しました（乖離：{round(100*now_diff_ratio,2)}%) at {simtime}")
                on_position = 1
                position_point = now_diff_ratio
                start_list.append(simtime)

            if (
                on_position == 1 and now_diff_ratio <= position_point - position_close_cutpoint
            ):  # 0.5%の鞘を抜く
                print(f"ポジション解消しました（乖離：{round(100*now_diff_ratio,2)}%) at {simtime}")
                on_position = 0
                position_point = 0
                event_count += 1
                end_list.append(simtime)

    print(f"{event_count} 回取引しました！")
    if position_point > 0:
        print("警告：まだポジションもってますよ")

    return event_count, position_point, len(day_unique)-1, start_list, end_list


if __name__ == "__main__":
    # inputを入力
    start_cutpoint = float(input("ポジション開始閾値を入力してね(ex: 0.01):")) 
    close_cutpoint = float(input("ポジション解消閾値を入力してね(ex: 0.005)："))
    
    df = backtest_data(timespan=1, plot_on=False)
    event_count, position_point, sim_days, start_list, end_list = backtest_sim(df, start_cutpoint, close_cutpoint)
    
    print(f"{round(event_count*close_cutpoint*100,1)} % 鞘を抜けた（注意！！手数料や流動性を考慮してません)")
    print(f"1日当り{event_count/sim_days}回取引していて、{round(event_count*close_cutpoint*100/sim_days,1)}%儲かるかも、、、")
    
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 7), sharex=True,
                         gridspec_kw={'height_ratios': [3, 1]})
    
    axes[0].plot(df.index ,df["diff_ratio"],color='k')#axに折れ線グラフを描画
    axes[1].plot(df.index ,df["btc_close"])
    axes[1].plot(df.index ,df["fx_close"])
    axes[0].grid()
    axes[1].grid()
    if event_count > 0: 
        for i in range(len(start_list)):
            try:
                axes[0].axvspan(start_list[i], end_list[i], alpha=0.5, color='green')
            except:
                axes[0].axvspan(start_list[i], df.index.max(), alpha=0.5, color='red') # 
    plt.show()

    
