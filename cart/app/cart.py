import pika, sys, os, json
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart, Dish

def send(response, queue: str):
    body = json.dumps(response)

    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    channel.queue_declare(queue=queue)

    channel.basic_publish(exchange='', routing_key=queue, body=body)
    print(f" [x] Отправлено в '{queue}' {response}")

    connection.close()

def get_cart(db: Session, sender: str, user_id: str):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if cart:
        print(f" [i] Корзина пользователя {user_id}: {cart.to_dict()}")
        response = {
            'action': 'cart_response',
            'data':
            {
                'user_id': user_id,
                'status': 'success',
                'cart': cart.to_dict()
            }
        }
    else:
        print(f" [i] Корзина пользователя {user_id} не найдена")
        response = {
            'action': 'cart_response',
            'data':
            {
                'user_id': user_id,
                'status': 'error',
                'error': 'Cart not found'
            }
        }
    
    send(response, sender)

def add_to_cart(db: Session, user_id: str, dish_name: str, dish_price: float):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    dish = Dish(name=dish_name, price=dish_price)
    cart.dishes.append(dish)
    cart.totalPrice += dish.finalPrice
    db.commit()

    print(f" [+] Блюдо '{dish_name}' добавлено в корзину пользователя {user_id}")

def remove_from_cart(db: Session, user_id: str, dish_id: int):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        print(f" [-] Корзина пользователя {user_id} не найдена")
        status = 'error'
        message = 'Cart not found'
    else:
        dish = db.query(Dish).filter(Dish.id == dish_id, Dish.cart_id == cart.id).first()

        if dish:
            cart.totalPrice -= dish.price
            db.delete(dish)
            db.commit()
            print(f" [-] Блюдо '{dish.name}' удалено из корзины пользователя {user_id}")
            status = 'success'
            message = 'Dish removed'
        else:
            print(f" [-] Блюдо не найдено в корзине пользователя {user_id}")
            status = 'error'
            message = 'Dish not found'

    response = {
        'action': 'remove_response',
        'data':
        {
            'user_id': user_id,
            'dish_id': dish_id,
            'status': status,
            'message': message
        }
    }

    send(response, 'API')


def process_message(ch, method, properties, body):
    message = json.loads(body)
    action = message.get('action')
    sender = message.get('sender')
    data = message.get('data')
    user_id = str(data.get('user_id'))

    db = next(get_db())

    print(f" [x] Recieved {message}")

    if action == 'get_cart':
        get_cart(db, sender, user_id)
    elif action == 'add_to_cart':
        add_to_cart(db, user_id, "Пицца пепперони", 528.00)
    elif action == 'remove_from_cart':
        dish_id = data.get('dish_id')
        remove_from_cart(db, user_id, dish_id)
    

def main():
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')

    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    channel.queue_declare(queue='cart')

    channel.basic_consume(queue='cart', auto_ack=True, on_message_callback=process_message)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)