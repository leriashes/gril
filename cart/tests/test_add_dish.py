import pytest
from cart.app.models import Cart
from cart.tests.conftest import cartAPI

def test_addDishReturnsSameDishNameAndPrice(cartAPI):

    data = {
        'user_id': '7',
        'dish': {
            'name': 'Сырная пицца',
            'price': 500.00
        }
    }

    cartAPI.send_message('add_dish', data)
    response = cartAPI.get_message()

    assert response.get('data').get('dish').get('name') == data['dish']['name'] and response.get('data').get('dish').get('price') == data['dish']['price']


def test_addDishReturnsSameUser(cartAPI):

    data = {
        'user_id': '9',
        'dish': {
            'name': 'Сырная пицца',
            'price': 500.00
        }
    }

    cartAPI.send_message('add_dish', data)
    response = cartAPI.get_message()

    assert response.get('data').get('user_id') == data['user_id']


def test_addDishUpdatesTotalPriceWhenCartIsEmpty(cartAPI, db_session):
    user_id = 'test'
    dish_price = 500
    totalPrice = 0

    cartAPI.clear_cart(db_session)

    cartAPI.send_message('add_dish', data={'user_id': user_id, 'dish': {'name': 'Сырная пицца', 'price': dish_price}})
    cartAPI.get_message()

    cart = db_session.query(Cart).filter(Cart.user_id == user_id).first()

    assert cart.totalPrice == totalPrice + dish_price

    cartAPI.clear_cart(db_session)


def test_addDishUpdatesTotalPriceWhenCartIsNotEmpty(cartAPI, db_session):
    user_id = 'test'
    dish_price = 500

    cartAPI.add_dish(db_session)

    cart = db_session.query(Cart).filter(Cart.user_id == user_id).first()
    totalPrice = cart.totalPrice

    cartAPI.send_message('add_dish', data={'user_id': user_id, 'dish': {'name': 'Сырная пицца', 'price': dish_price}})
    cartAPI.get_message()
    db_session.refresh(cart)

    assert cart.totalPrice == totalPrice + dish_price

    cartAPI.clear_cart(db_session)


def test_addDishAddAddedProductsCost(cartAPI, db_session):
    user_id = 'test'
    dish_price = 500
    added_price = 25

    cart = db_session.query(Cart).filter(Cart.user_id == user_id).first()
    totalPrice = cart.totalPrice

    cartAPI.send_message('add_dish', data={'user_id': user_id, 'dish': {'name': 'Сырная пицца', 'price': dish_price, 'added_products': [{
            'id': '123',
            'name': 'Сыр дополнительный',
            'price': added_price
        }]}})
    
    cartAPI.get_message()
    db_session.refresh(cart)

    assert cart.totalPrice == totalPrice + dish_price + added_price

    cartAPI.clear_cart(db_session)