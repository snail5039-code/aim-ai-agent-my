from vending_machine import VendingMachine
from product import Product
from payment import Payment, CardPayment, CashPayment

cola = Product('콜라', 1500, 3)
cider = Product('사이댜', 2000, 1)
water = Product('물', 500, 0)

vending_machien = VendingMachine()

for product in [cola, cider, water]:
    vending_machien.insert_product(product)


card_payment = CardPayment(30000, 10000)

cash_payment = CashPayment(10000)

while True:
    vending_machien.run(card_payment)
