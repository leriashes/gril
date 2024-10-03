import pika, sys, os, json

def get_cart(user_id):
    print(f" [+] Корзина пользователя {user_id}")

def add_to_cart(user_id):
    print(f" [+] Добавление блюда в корзину пользователя {user_id}")

def remove_from_cart(user_id):
    print(f" [+] Удаление блюда из корзины пользователя {user_id}")

def process_message(ch, method, properties, body):
    message = json.loads(body)
    action = message.get('action')
    data = message.get('data')

    print(f" [x] Recieved {body}")

    if action == 'get_cart':
        get_cart(data['user_id'])
    elif action == 'add_to_cart':
        add_to_cart(data['user_id'])
    elif action == 'remove_from_cart':
        remove_from_cart(data['user_id'])
    

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
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