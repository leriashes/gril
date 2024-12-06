import pytest
import pika, json, uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cart.app.models import *

class CartAPI:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='API')
        self.channel.queue_declare(queue='cart')

        self.response = None
        self.correlation_id = None


    def get_message(self):
        while (True):
            method, properties, body = self.channel.basic_get(queue='API', auto_ack=False)
            if method is not None:
                if self.correlation_id == json.loads(body).get('id'):
                    self.response = json.loads(body)
                    self.channel.basic_ack(delivery_tag=method.delivery_tag)
                    break
                else:
                    self.channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        return self.response
            

    def send_message(self, action, data):
        self.correlation_id = str(uuid.uuid4())

        message = {
            'id': self.correlation_id,
            'action': action,
            'data': data
        }

        body = json.dumps(message)
        self.channel.basic_publish(exchange='', routing_key='cart', body=body)


    def clear_cart(self, db_session):
        cart = db_session.query(Cart).filter(Cart.user_id == 'test').first()

        if cart:
            for dish in cart.dishes:
                cart.totalPrice -= dish.price
                db_session.delete(dish)
                db_session.commit()

            cart.dishes.clear()
            cart.totalPrice = 0.0
            db_session.commit()


    def add_dish(self, db_session):
        cart = db_session.query(Cart).filter(Cart.user_id == 'test').first()
        if not cart:
            cart = Cart(user_id='test')
            db_session.add(cart)
            db_session.commit()
            db_session.refresh(cart)
        dish = Dish(name="Пицца", price=700)
        cart.dishes.append(dish)
        cart.totalPrice += dish.price
        db_session.commit()


@pytest.fixture(scope="function")
def cartAPI():
    return CartAPI()

@pytest.fixture(scope="function")
def db_session():
    DATABASE_URL = "postgresql://user:mypassword@localhost:5432/cartdb"
    engine = create_engine(DATABASE_URL, echo=False)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
