import pika, sys, os, json
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import Cart, Dish, Product

def send(response, queue: str):
    body = json.dumps(response)

    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
    channel = connection.channel()

    channel.queue_declare(queue=queue)

    channel.basic_publish(exchange='', routing_key=queue, body=body)
    print(f" [x] Отправлено в '{queue}' {response}")

    connection.close()

def get_cart(db: Session, id: str, sender: str, user_id: str):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if cart:
        print(f" [i] Корзина пользователя {user_id}: {cart.to_dict()}")
        response = {
            'id': id,
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
            'id': id,
            'action': 'cart_response',
            'data':
            {
                'user_id': user_id,
                'status': 'error',
                'error': 'Cart not found'
            }
        }
    
    send(response, sender)

def produce_product(db: Session, id, name, price):
    product = db.query(Product).filter(Product.id == id).first()

    if product is None:
        while product is None:
            try:
                product = Product(
                    id=id,
                    name=(name or ''),
                    price=(price or 0.0)
                )
                
                db.add(product)
                db.commit()
            except IntegrityError:
                db.rollback()
                product = db.query(Product).filter(Product.id == id).first()

                if product is not None:
                    if name is not None:
                        product.name = name
                    if price is not None:
                        product.price = price
                    db.commit()
    else:
        if name is not None:
            product.name = name
        if price is not None:
            product.price = price
        db.commit()

def fill_products(db: Session, dish_data: dict, dish_id: int):
    dish = db.query(Dish).filter(Dish.id == dish_id).first()

    if dish:
        dish_products = dish_data.get('products', [])
        for prod_data in dish_products:
            id = prod_data.get('id')
            name = prod_data.get('name')
            price = prod_data.get('price')

            if id is not None:
                produce_product(db, id, name, price)
                product = db.query(Product).filter(Product.id == id).first()
                
                if product not in dish.dish_products:
                    dish.dish_products.append(product)
                db.commit()

        rem_products = dish_data.get('removed_products', [])
        for prod_data in rem_products:
            id = prod_data.get('id')
            name = prod_data.get('name')
            price = prod_data.get('price')

            if id is not None:
                produce_product(db, id, name, price)
                product = db.query(Product).filter(Product.id == id).first()
                
                if product not in dish.removed_products:
                    dish.removed_products.append(product)
                db.commit()

        add_products = dish_data.get('added_products', [])
        for prod_data in add_products:
            id = prod_data.get('id')
            name = prod_data.get('name')
            price = prod_data.get('price')

            if id is not None:
                produce_product(db, id, name, price)
                product = db.query(Product).filter(Product.id == id).first()
                
                if product not in dish.added_products:
                    dish.added_products.append(product)
                dish.finalPrice += product.price
                db.commit()

def add_dish(db: Session, id: str, user_id: str, dish_data: dict):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    dish = Dish(
        name=dish_data.get('name', ''),
        price=dish_data.get('price', 0.0),
        size=dish_data.get('size'),
        category=dish_data.get('category'),
        description=dish_data.get('description'),
        sauce=dish_data.get('sauce')
    )

    cart.dishes.append(dish)
    cart.totalPrice += dish.price
    db.commit()

    fill_products(db, dish_data, dish.id)

    cart.totalPrice += dish.finalPrice - dish.price
    db.commit()

    print(f" [+] Блюдо '{dish.to_dict()}' добавлено в корзину пользователя {user_id}")
    response = {
        'id': id,
        'action': 'add_response',
        'data':
        {
            'user_id': user_id,
            'status': 'success',
            'dish': dish.to_dict()
        }
    }
    send(response, 'API')

def remove_dish(db: Session, id: str, user_id: str, dish_id: int):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        print(f" [-] Корзина пользователя {user_id} не найдена")
        status = 'error'
        message = 'Cart not found'
    else:
        dish = db.query(Dish).filter(Dish.id == dish_id, Dish.cart_id == cart.id).first()

        if dish:
            cart.totalPrice -= dish.finalPrice
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
        'id': id,
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

def get_dish(db: Session, id: str, user_id: str, dish_id: int):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        print(f" [i] Корзина пользователя {user_id} не найдена")
        status = 'error'
        error = 'Cart not found'
    else:
        dish = db.query(Dish).filter(Dish.id == dish_id, Dish.cart_id == cart.id).first()

        if dish:
            print(f" [i] Блюдо '{dish.name}' из корзины пользователя {user_id}")
            status = 'success'
        else:
            print(f" [i] Блюдо не найдено в корзине пользователя {user_id}")
            status = 'error'
            error = 'Dish not found'

    response = {
        'id': id,
        'action': 'dish_response',
        'data':
        {
            'user_id': user_id,
            'dish_id': dish_id,
            'status': status,
        }
    }

    if cart and dish:
        response['data']['dish'] = dish.to_dict()
    else:
        response['data']['error'] = error

    send(response, 'API')

def update_dish(db: Session, id: str, user_id: str, dish_id: int, dish_data: dict):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        print(f" [u] Корзина пользователя {user_id} не найдена")
        status = 'error'
        error = 'Cart not found'
    else:
        dish = db.query(Dish).filter(Dish.id == dish_id, Dish.cart_id == cart.id).first()

        if dish:
            cart.totalPrice -= dish.finalPrice 

            dish.name = dish_data.get('name', dish.name)
            dish.category = dish_data.get('category', dish.category)
            dish.size = dish_data.get('size', dish.size)
            dish.price = dish_data.get('price', dish.price)
            dish.sauce = dish_data.get('sauce', dish.sauce)

            cart.totalPrice += dish.price
            dish.finalPrice = dish.price

            new_product_ids = {product_data.get('id') for product_data in dish_data.get('products', [])}

            for product in dish.dish_products:
                if product.id not in new_product_ids:
                    dish.dish_products.remove(product)
            
            new_product_ids = {product_data.get('id') for product_data in dish_data.get('added_products', [])}

            for product in dish.added_products:
                if product.id not in new_product_ids:
                    dish.added_products.remove(product)

            new_product_ids = {product_data.get('id') for product_data in dish_data.get('removed_products', [])}

            for product in dish.removed_products:
                if product.id not in new_product_ids:
                    dish.removed_products.remove(product)

            fill_products(db, dish_data, dish.id)

            cart.totalPrice += dish.finalPrice - dish.price
            db.commit()

            print(f" [u] Блюдо '{dish.name}' из корзины пользователя {user_id} обновлено")
            status = 'success'
        else:
            print(f" [u] Блюдо не найдено в корзине пользователя {user_id}")
            status = 'error'
            error = 'Dish not found'

    response = {
        'id': id,
        'action': 'update_response',
        'data':
        {
            'user_id': user_id,
            'dish_id': dish_id,
            'status': status
        }
    }

    if cart and dish:
        response['data']['dish'] = dish.to_dict()
    else:
        response['data']['error'] = error

    send(response, 'API')

def clear_cart(db: Session, id: str, user_id: str):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if cart:
        for dish in cart.dishes:
            cart.totalPrice -= dish.price
            db.delete(dish)
            db.commit()

        cart.dishes.clear()
        cart.totalPrice = 0.0
        db.commit()

        print(f" [o] Корзина пользователя {user_id} очищена: {cart.to_dict()}")
        response = {
            'action': 'clear_response',
            'data':
            {
                'user_id': user_id,
                'status': 'success',
                'cart': cart.to_dict()
            }
        }
    else:
        print(f" [o] Корзина пользователя {user_id} не найдена")
        response = {
            'id': id,
            'action': 'clear_response',
            'data':
            {
                'user_id': user_id,
                'status': 'error',
                'error': 'Cart not found'
            }
        }
    
    send(response, 'API')

def process_message(ch, method, properties, body):
    message = json.loads(body)
    id = str(message.get('id'))
    action = message.get('action')
    sender = message.get('sender')
    data = message.get('data')
    user_id = str(data.get('user_id'))

    db = next(get_db())

    print(f" [x] Recieved {message}")

    if action == 'get_cart':
        get_cart(db, id, sender, user_id)
    elif action == 'clear_cart':
        clear_cart(db, id, user_id)
    elif action == 'add_dish':
        dish = data.get('dish')
        add_dish(db, id, user_id, dish)
    elif action == 'remove_dish':
        dish_id = data.get('dish_id')
        remove_dish(db, id, user_id, dish_id)
    elif action == 'get_dish':
        dish_id = data.get('dish_id')
        get_dish(db, id, user_id, dish_id)
    elif action == 'update_dish':
        dish_id = data.get('dish_id')
        dish = data.get('dish')
        update_dish(db, id, user_id, dish_id, dish)
    

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