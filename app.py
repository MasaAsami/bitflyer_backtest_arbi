# -*- coding: utf-8 -*-
#app用
# -*- coding: utf-8 -*-
import matplotlib      # Macの場合、これがないとエラーになることも python 3.6の場合　3.7では不要？
matplotlib.use('tkagg') # Macの場合、これがないとエラーになることも python 3.6の場合　3.7では不要？
import numpy as np
import tkinter as tk
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg  import FigureCanvasTkAgg
from bitflyer_backtest import backtest_data, backtest_sim
from functools import partial
# チャートつくるため
import matplotlib.pyplot as plt


class Application(tk.Frame):
  def __init__(self,master):
    super().__init__(master)
    self.pack()
    self.df = None

    master.geometry("800x900")
    master.title("bitflyer_backtest")
    #エントリー
    self.fig, self.axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 7), sharex=True,
                          gridspec_kw={'height_ratios': [3, 1]})
    self.canvas = FigureCanvasTkAgg(self.fig, master=master)
    self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    self.canvas.draw()
    # ラベル
    self.lbl = tk.Label(text='ポジション開始閾値:')
    self.lbl.place(x=30, y=45)
    # テキストボックス
    self.box0 = tk.Entry(width=5)
    self.box0.place(x=170, y=45)
    self.box0.insert(tk.END,"0.01") # 
    # ラベル2
    self.lbl2 = tk.Label(text='ポジション解消閾値:')
    self.lbl2.place(x=250, y=45)
    # テキストボックス
    self.box1 = tk.Entry(width=5)
    self.box1.place(x=380, y=45)
    self.box1.insert(tk.END,"0.005") # 
     # ラベル3
    self.lbl3 = tk.Label(text='データ取得期間(分):')
    self.lbl3.place(x=450, y=45)
    # テキストボックス
    self.box2 = tk.Entry(width=5)
    self.box2.place(x=580, y=45)
    self.box2.insert(tk.END,"1") # 
  

    #グラフ作成ボタン    
    self.button = tk.Button(master, text=u'グラフ作成', width=50)    
    self.button.bind("<Button-1>",self.button_clicked)
    self.button.pack(expand=1)
    
    self.table_button = tk.Button(master=master, text="データを見る",command = self.table_open ,width=50)
    self.table_button.pack(expand=1)
    
    self.quit_button = tk.Button(master=master, text="終了", command=self._quit, width=10)
    self.quit_button.pack(anchor=tk.E,expand=1)
      
  def plot_price(self, span, start_cutpoint, close_cutpoint):
      self.df = backtest_data(timespan=span, plot_on=False) 
      event_count, position_point, sim_days, start_list, end_list = backtest_sim(self.df, start_cutpoint, close_cutpoint)
      #画像作成
      df = self.df.copy()
      
      #fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 7), sharex=True,
      #                      gridspec_kw={'height_ratios': [3, 1]})
      self.axes[0].plot(df.index ,df["diff_ratio"],color='k')#axに折れ線グラフを描画
      self.axes[1].plot(df.index ,df["btc_close"])
      self.axes[1].plot(df.index ,df["fx_close"])
      #self.axes[0].text(sim_days[0], df["diff_ratio"].max()*0.8, f"{event_count}回取引したよ")
      
      self.axes[0].grid()
      self.axes[1].grid()
      if event_count > 0: 
        for i in range(len(start_list)):
            try:
                self.axes[0].axvspan(start_list[i], end_list[i], alpha=0.5, color='green')
            except:
                self.axes[0].axvspan(start_list[i], df.index.max(), alpha=0.5, color='red') #
      #appに表示
      self.canvas.draw()
        
  # button1クリック時の処理
  def button_clicked(self,event):
      self.axes[0].clear()  # figをクリア
      self.axes[1].clear() # figをクリア
      start_cutpoint = float(self.box0.get())# ボタンの内容を反映
      close_cutpoint = float(self.box1.get())
      span = int(self.box2.get())
      #グラフ描画
      self.plot_price(span, start_cutpoint,close_cutpoint)
      
  def table_open(self):
    #ウィンドウ立ち上げ
    win2 = tk.Toplevel(master = self.master)
    win2.geometry("900x300")
    win2.title("詳細データ")
    #表を作る
    tree = ttk.Treeview(win2)
    
    #taking all the columns heading in a variable"df_col".
    df = self.df.reset_index()
    df.head(100)
    df_col = df.columns.values

    #all the column name are generated dynamically.
    tree["columns"]=(df_col)
    counter = len(df)
    #generating for loop to create columns and give heading to them through df_col var.
    
    for x in range(len(df_col)):
      tree.column(x, width=100 )
      tree.heading(x, text=df_col[x])
    #generating for loop to print values of dataframe in treeview column. 
    for i in range(counter):
      tree.insert('', 0, values=[df.loc[i,[df_col_]].values[0] for df_col_ in df_col])
        
    tree.pack(fill=tk.BOTH, side=tk.LEFT, expand=1)
    win2.mainloop()
  
  def _quit(self):
    win = tk.Tk() # 一回上書き
    win.quit()     # stops mainloop
    win.destroy()  # this is necessary on Windows to prevent
                      # Fatal Python Error: PyEval_RestoreThread: NULL tstate

def main():
  win = tk.Tk()
  app = Application(master=win)
  app.mainloop()


if __name__ == "__main__":
    main()