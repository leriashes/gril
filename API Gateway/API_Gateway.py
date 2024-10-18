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

elif chnl == 'clear':
    message = {
        'action': 'clear_cart',
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
        'action': 'add_dish',
        'data':
        {
            'user_id': user_id,
            'dish': {
                'name': 'Сырная пицца',
                'price': 500.00,
                'dish_products': [
                    {
                        'id': '356',
                        'name': 'Сыр'
                    }
                ],
                'added_products': [
                    {
                        'id': '123',
                        'name': 'Сыр дополнительный',
                        'price': 25.00
                    }
                ],
                'removed_products': [
                    {
                        'id': '36',
                        'name': 'Сыр Бри'
                    }
                ],
            }
        }
    }

    body = json.dumps(message)

    channel.basic_publish(exchange='', routing_key='cart', body=body)
    print(f" [x] Sent 'Hello Cart, it's API Gateway! It's time to add dish to cart {user_id}")

elif chnl == 'del':
    dish_id = int(''.join(sys.argv[3])) or 1

    message = {
        'action': 'remove_dish',
        'data':
        {
            'user_id': user_id,
            'dish_id': dish_id
        }
    }

    body = json.dumps(message)

    channel.basic_publish(exchange='', routing_key='cart', body=body)
    print(f" [x] Sent 'Hello Cart, it's API Gateway! It's time to del dish from cart {user_id}")

else:
    channel.basic_publish(exchange='', routing_key='cart', body='Hello Cart, it\'s API Gateway!')
    print(f" {chnl} [x] Sent 'Hello Cart, it's API Gateway!'")



connection.close()