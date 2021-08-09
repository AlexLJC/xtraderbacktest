import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 

class Position():
    def __init__(self,cash):
        self.cash = cash
        self.margin = 0
        self.position_current = []
        self.position_history = []
        self.closed_fund = {}
        self.float_fund = {}
