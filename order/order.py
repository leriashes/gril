import pika, sys, json, os

def process_message(ch, method, properties, body):
    message = json.loads(body)
    action = message.get('action')

    if action == 'get_cart':
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue='cart')

        channel.basic_publish(exchange='', routing_key='cart', body=body)
        print(f" [x] Recieved and sent {message}")

        connection.close()

    elif action == 'cart_response':
        print(f" [x] Recieved {message}")
    


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='order')

    channel.basic_consume(queue='order', auto_ack=True, on_message_callback=process_message)

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