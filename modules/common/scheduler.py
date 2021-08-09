from abc import ABC, abstractmethod
 

'''
This is the abstract class of scheduler for live and backtest.
'''
class Scheduler(object):

    @abstractmethod
    def __init__(self,mode):
        pass

    @abstractmethod
    def register_strategy(self,strategy):
        pass

    @abstractmethod
    def start(self):
        pass