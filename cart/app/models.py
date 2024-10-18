from sqlalchemy import Column, ForeignKey, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base

class BaseModel(Base):
    __abstract__ = True

    def to_dict(self, ordered_keys=None):
        if ordered_keys:
            return {key: getattr(self, key) for key in ordered_keys if hasattr(self, key)}
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Cart(BaseModel):
    __tablename__ = 'carts'

    id = Column(Integer, nullable=False, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)
    totalPrice = Column(Float)

    dishes = relationship("Dish", back_populates="cart")

    def __init__(self, user_id):
        self.user_id = str(user_id)
        self.totalPrice = 0.0

    def to_dict(self):
        ordered_keys = ['id', 'user_id', 'totalPrice']
        cart_dict = super().to_dict(ordered_keys)
        cart_dict['dishes'] = [dish.to_dict() for dish in self.dishes]
        return cart_dict

class Dish(BaseModel):
    __tablename__ = 'dishes'

    id = Column(Integer, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=False)
    size = Column(String, nullable=True)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    price = Column(Float, nullable=False)
    finalPrice = Column(Float, nullable=False)

    sauce = Column(Integer, nullable=True)

    cart_id = Column(Integer, ForeignKey('carts.id'))


    cart = relationship("Cart", back_populates="dishes")

    dish_products = relationship("Product", secondary="dish_products", back_populates="dishes")
    added_products = relationship("Product", secondary="added_products", back_populates="dishes_added")
    removed_products = relationship("Product", secondary="removed_products", back_populates="dishes_removed")

    def __init__(self, name: str, price: float, size = None, category = None, description = None, sauce = None):
        self.name = name
        self.price = price
        self.finalPrice = price
        self.size = size
        self.category = category
        self.description = description
        self.sauce = sauce

    def to_dict(self):
        ordered_keys = ['id', 'name', 'category', 'size', 'price', 'finalPrice', 'sauce']
        dish_dict = super().to_dict(ordered_keys)
        dish_dict['dish_products'] = [product.to_dict() for product in self.dish_products]
        dish_dict['added_products'] = [product.to_dict() for product in self.added_products]
        dish_dict['removed_products'] = [product.to_dict() for product in self.removed_products]
        return dish_dict

class Product(BaseModel):
    __tablename__ = 'products'

    id = Column(String, nullable=False, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

    dishes = relationship("Dish", secondary="dish_products", back_populates="dish_products")
    dishes_added = relationship("Dish", secondary="added_products", back_populates="added_products")
    dishes_removed = relationship("Dish", secondary="removed_products", back_populates="removed_products")

    def __init__(self, id: str, name: str, price: float = 0.0):
        self.id = id
        self.name = name
        self.price = price

    def to_dict(self):
        ordered_keys = ['id', 'name', 'price']
        return super().to_dict(ordered_keys)

class AddedProduct(Base):
    __tablename__ = 'added_products'

    dish_id = Column(Integer, ForeignKey('dishes.id', ondelete='CASCADE'), primary_key=True)
    product_id = Column(String, ForeignKey('products.id'), primary_key=True)

class RemovedProduct(Base):
    __tablename__ = 'removed_products'

    dish_id = Column(Integer, ForeignKey('dishes.id', ondelete='CASCADE'), primary_key=True)
    product_id = Column(String, ForeignKey('products.id'), primary_key=True)

class DishProduct(Base):
    __tablename__ = 'dish_products'

    dish_id = Column(Integer, ForeignKey('dishes.id', ondelete='CASCADE'), primary_key=True)
    product_id = Column(String, ForeignKey('products.id'), primary_key=True)