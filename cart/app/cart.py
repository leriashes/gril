import pika, sys, os, json
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart

def get_cart(db: Session, user_id: str):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if cart:
        print(f" [i] Корзина пользователя {user_id}: {cart}")
    else:
        print(f" [i] Корзина пользователя {user_id} не найдена")


def add_to_cart(user_id):
    print(f" [+] Добавление блюда в корзину пользователя {user_id}")

def remove_from_cart(user_id):
    print(f" [-] Удаление блюда из корзины пользователя {user_id}")

def process_message(ch, method, properties, body):
    message = json.loads(body)
    action = message.get('action')
    data = message.get('data')
    user_id = str(data.get('user_id'))

    db = next(get_db())

    print(f" [x] Recieved {message}")

    if action == 'get_cart':
        get_cart(db, user_id)
    elif action == 'add_to_cart':
        add_to_cart(data['user_id'])
    elif action == 'remove_from_cart':
        remove_from_cart(data['user_id'])
    

def main():
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    print(rabbitmq_host)

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