

class Product:
    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


    def show_info(self):
        print(f'이름 : {self.name}')
        print(f'가격 : {self.price}')
        if not self.stock:
            print(f'재고 없음')
        print('--------------------')


    def reduce_stock(self):
        self.stock -= 1

# reduce_stock 이라는 함수를 쓰는 이유 -> 나중에 있을 확장성을 고려해서.
# class OtherProduct(Product):

#     def reduce_stock(self):
#         self.stock -= 뭔가의 나의 단위로 조절