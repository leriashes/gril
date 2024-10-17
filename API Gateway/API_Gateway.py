import pika, sys, json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='cart')

channel.queue_declare(queue='order')

chnl = ''.join(sys.argv[1]) or 'order'
user_id = int(''.join(sys.argv[2])) or 1

if chnl == 'order':
    message = {
        'action': 'get_cart',
        'sender': 'order',
        'data' :
        {
            'user_id': user_id
        }
    }

    body = json.dumps(message)

    channel.basic_publish(exchange='', routing_key='order', body=body)
    print(f" [x] Sent {body}")

elif chnl == 'cart':
    message = {
        'action': 'get_cart',
        'sender': 'API',
        'data' :
        {
            'user_id': user_id
        }
    }

    body = json.dumps(message)

    channel.basic_publish(exchange='', routing_key='cart', body=body)
    print(f" [x] Sent {body}")

elif chnl == 'add':
    message = {
        'action': 'add_to_cart',
        'data':
        {
            'user_id': user_id
        }
    }

    body = json.dumps(message)

    channel.basic_publish(exchange='', routing_key='cart', body=body)
    print(f" [x] Sent 'Hello Cart, it's API Gateway! It's time to add dish to cart {user_id}")

elif chnl == 'del':
    message = {
        'action': 'remove_from_cart',
        'data':
        {
            'user_id': user_id
        }
    }

    body = json.dumps(message)

    channel.basic_publish(exchange='', routing_key='cart', body=body)
    print(f" [x] Sent 'Hello Cart, it's API Gateway! It's time to del dish from cart {user_id}")

else:
    channel.basic_publish(exchange='', routing_key='cart', body='Hello Cart, it\'s API Gateway!')
    print(f" {chnl} [x] Sent 'Hello Cart, it's API Gateway!'")



connection.close()