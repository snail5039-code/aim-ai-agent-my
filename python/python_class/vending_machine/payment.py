from abc import ABC, abstractmethod

class Payment:

    @abstractmethod
    def pay(self, price: int):

        pass




class CashPayment:

    def __init__(self, cash: int):
        # 현금을 가집니다.
        self.cash = cash

    def pay(self, price: int) -> bool:

        if self.cash >= price:
            self.cash -= price
            return True

        return False


class CardPayment:

    def __init__(self, card_limit, card_usage):
        self.card_limit = card_limit
        self.card_usage = card_usage

        
    def pay(self, price: int) -> bool:
        '''성공하면 True, 실패하면 False를 반환하는 함수'''
        if self.card_usage + price <= self.card_limit:
            self.card_usage += price
            return True

        return False
