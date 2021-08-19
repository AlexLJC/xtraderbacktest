import pandas as pd

class TradeBook():

    def __init__(self,close_trades):
        self.close_trades = close_trades
        self.close_trades_df = pd.DataFrame(self.close_trades)
    

    def summary(self):
        result = {}

        # total number of trades
        result["total_trades"] = int(len(self.close_trades_df))
        result["total_long_trades"] = int(len(self.close_trades_df[self.close_trades_df["direction"] == "long"]))
        result["total_short_trades"] = int(len(self.close_trades_df[self.close_trades_df["direction"] == "short"]))

        result["percentage_of_long_trades"] = result["total_long_trades"]  / result["total_trades"] if result["total_trades"] !=0 else 0
        result["percentage_of_short_trades"] = result["total_short_trades"]  / result["total_trades"] if result["total_trades"] !=0 else 0
        

        long_profit = self.close_trades_df.sort_values("close_date").loc[ self.close_trades_df["direction"] == "long", "profit"]
        short_profit = self.close_trades_df.sort_values("close_date").loc[ self.close_trades_df["direction"] == "short", "profit"]
        overall_profit = self.close_trades_df.sort_values("close_date")["profit"]

        # total profit
        result["total_long_profit"] = long_profit.sum()
        result["total_short_profit"] = short_profit.sum()
        result["total_profit"] =result["total_long_profit"] + result["total_short_profit"]

        # avg
        result["avg_profit"] = result["total_profit"] / result["total_trades"]
        result["avg_win"] = (overall_profit > 0).mean()
        result["avg_loss"] = (overall_profit < 0).mean()
        result["avg_win/avg_loss"] = result["avg_win"]  / result["avg_loss"]

        # win rate
        result["long_win_trades"] = int((long_profit > 0).sum())
        result["short_win_trades"] = int((short_profit > 0).sum())
        result["long_win_rates"] = result["long_win_trades"] / result["total_long_trades"] if result["total_trades"] !=0 else 0
        result["short_win_rates"] = result["short_win_trades"] / result["total_short_trades"] if result["total_trades"] !=0 else 0
        result["win_rate"] = (result["long_win_trades"] + result["short_win_trades"]) / result["total_trades"] if result["total_trades"] !=0 else 0

        # max and min
        result["max_long_loss"] = long_profit.min()
        result["max_short_loss"] = short_profit.min()
        result["max_loss"] = overall_profit.min()

        result["max_long_profit"] = long_profit.max()
        result["max_short_profit"] = short_profit.max()
        result["max_profit"] = overall_profit.max()
        #print(overall_profit,overall_profit.max())
        #exit(0)
        def cct(y):
            return y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1)
        pos_long_cct = cct(long_profit > 0)
        pos_short_cct = cct(short_profit > 0)
        pos_overall_cct = cct(overall_profit > 0)
        neg_long_cct = cct(long_profit < 0)
        neg_short_cct = cct(short_profit < 0)
        neg_overall_cct = cct(overall_profit < 0)

        def max_cons_sum_id(cctr, max_cct=None):
            end_id = cctr.reset_index(drop=True).idxmax() + 1
            if max_cct == None:
                max_cct = cctr.max()
            start_id = end_id - max_cct
            return (start_id, end_id)

        def max_cont_trend(pnl, direc):
            cum_pnl = pnl.cumsum()
            no_eq = cum_pnl[cum_pnl != cum_pnl.shift(1)]
            if direc == "drawdown":
                local_max = no_eq.head(1).append(no_eq[(no_eq > no_eq.shift(1)) & (no_eq > no_eq.shift(-1))]).append(no_eq.tail(1))
                if len(local_max) == 0:
                    return "No enough trade"
                local_max_after_min = {}
                for index, value in local_max.iteritems():
                    local_max_after_min[index] = no_eq[index:].min()
                return (pd.Series(local_max_after_min) - local_max).min()

            elif direc == "riseup":
                local_min = no_eq.head(1).append(no_eq[(no_eq < no_eq.shift(1)) & (no_eq < no_eq.shift(-1))]).append(no_eq.tail(1))
                if len(local_min) == 0:
                    return "No enough trade"
                local_min_after_max = {}
                for index, value in local_min.iteritems():
                    local_min_after_max[index] = no_eq[index:].max()
                return (pd.Series(local_min_after_max) - local_min).max()

        # max rise up
        result["long_max_rise_up"] = max_cont_trend(long_profit, "riseup")
        result["short_max_rise_up"] = max_cont_trend(short_profit, "riseup")
        result["overall_max_rise_up"] = max_cont_trend(overall_profit, "riseup")

        # max draw down
        result["long_max_draw_down"] = max_cont_trend(long_profit, "drawdown")
        result["short_max_draw_down"] = max_cont_trend(short_profit, "drawdown")
        result["max_draw_down"] = max_cont_trend(overall_profit, "drawdown")

        # cost of trade
        commissions = self.close_trades_df["commission"]
        swaps = self.close_trades_df["swap"]
        result["commissions"] = float(commissions.sum())
        result["swaps"] =  float(swaps.sum())

        if type(result["max_draw_down"]) is not str and result["max_draw_down"] < 0:
            result["profit/max_draw_down"] = -result["total_profit"] / result["max_draw_down"]
        return result