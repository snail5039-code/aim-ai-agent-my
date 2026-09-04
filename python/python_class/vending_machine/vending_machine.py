# 물건을 가지고 있습니다.
# 물건을 가지고 뭔갈 할겁니다 -> 판매를 할 것임.
    # 물건이라는 변수에 대해서 변화를 줄 수 있다.
    # 결제라는 과정을 통해야 한다.
    # 결제라는 것과 연관관계를 가져야 한다.

from product import Product
from payment import Payment
from exceptions import NotFoundException, OutOfStockException

class VendingMachine:

    def __init__(self):
        self.products: dict[str, Product] = {}

    def insert_product(self, product: Product):
        self.products[product.name] = product

    def show_products(self):
        """자판기가 가지고 있는 상품들을 보여주는 함수."""

        for product in self.products.values():
            product.show_info()

    def choose_product(self):
        user_input= input()

        if user_input not in self.products:
            # print('없는 상품입니다.')
            raise NotFoundException('없는 상품입니다.')

        product = self.products[user_input]

        if product.stock == 0:
            # print('재고가 없습니다.')

            # 문제상황이 아님. 일어날수도 있음.
            # Exception 문법적인 오류가 아니더라도 정상적이지 않은 상황에 대해서
            # 책임을 상위 함수 등에 넘기는 역할을 한다.
            raise OutOfStockException('재고가 없습니다.')

        return product

    def process_payment(self, product: Product, payment: Payment):
        # prodct의 가격과 payment의 가격을 비교해서 
        # 성공이면 -> 
        # 실패면 ->
        # if product.price < payment.money:
        #     # products의 재고가 줄어듦.
        #     # product.stock -= 1
        #     product.reduce_stock()

        #     # payment의 money가 줄어듦.
        #     payment.pay(product.price)
        # else:
        #     # 돈이 부족합니다.
        #     raise Exception

        # 위의 if문에서는 결제 가능 여부를 vending_machine에서 판단.

        # 아래 코드는 결제 가능 여부를 payment의 함수에서 처리해서 결과만 알려줍니다.
        if payment.pay(product.price): # 성공 / 실패
            product.reduce_stock()
            return True
        else:
            # 실패한 경우
            raise Exception
        # payment에서 pay를 시도해.
        # 성공 -> 스톡 줄여
        # 실패 -> rasie Exception

    def run(self, payment: Payment):
        try:
            # 우리가 자판기를 쓸 때 어떤 흐름으로 쓰느냐

            # 1. 앞에 선다. -> 우리에게 메뉴가 보입니다.
            self.show_products()

            # # 2. 메뉴 선택을 합니다.
            product = self.choose_product()


            # # 3. 결제를 합니다.
            # 결제를 받아서 금액이 충분한지
            is_success = self.process_payment(product, payment)

            if is_success:
                print(f'물건 나옵니다. {product.name}')
            else:
                print('실패')

            # # 4. 결제 성공 여부에 따라서 제품이 나오거나, 나오지 않거나 합니다.
            # products에 영향을 미치는 무언가.
        except NotFoundException as e:
            print('그런 상품 없습니다.')
        except OutOfStockException as e:
            print(e)
            
        except Exception as e:
            print(e)
            