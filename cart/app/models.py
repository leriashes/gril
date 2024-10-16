from sqlalchemy import Column, ForeignKey, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, nullable=False, primary_key=True, index=True)

class Cart(BaseModel):
    __tablename__ = 'carts'

    user_id = Column(String, unique=True, nullable=False)
    totalPrice = Column(Float)

    dishes = relationship("Dish", back_populates="cart")

    def __init__(self, user_id):
        self.user_id = str(user_id)
        self.totalPrice = 0.0

class Dish(BaseModel):
    __tablename__ = 'dishes'

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

    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
        self.finalPrice = price

class Product(BaseModel):
    __tablename__ = 'products'

    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

    dishes = relationship("Dish", secondary="dish_products", back_populates="dish_products")
    dishes_added = relationship("Dish", secondary="added_products", back_populates="added_products")
    dishes_removed = relationship("Dish", secondary="removed_products", back_populates="removed_products")

class AddedProduct(Base):
    __tablename__ = 'added_products'

    dish_id = Column(Integer, ForeignKey('dishes.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)

class RemovedProduct(Base):
    __tablename__ = 'removed_products'

    dish_id = Column(Integer, ForeignKey('dishes.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)

class DishProduct(Base):
    __tablename__ = 'dish_products'

    dish_id = Column(Integer, ForeignKey('dishes.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)