WIP: miPubSub
=============

Publish/Subscribe pattern build with RabbitMQ and Protocol Buffers.

Installation
------------

.. code-block:: bash

    pip install -e git@github.com:azylinski/miPubSub.git@master#egg=miPubSub


Run RabbitMQ
------------

In order to use miPubSub, you need to have access to RabbitMQ server.
To setup locally with `docker <https://docs.docker.com/engine/installation/>`_:

.. code-block:: bash

    docker run -d \
      --name demo-rabbit \
      -p 5672:5672 \
      -p 15672:15672 \
      rabbitmq:3.6.15-management-alpine


Define events structure
-----------------------

.. code-block::

    # schemas/events/user.proto

    syntax = "proto3";

    package events;


    message User {
      string name = 1;
      string email = 2;
    }


.. code-block:: bash

    # compile proto files
    protoc -I=schemas/events/ --python_out=proto/ schemas/events/*.proto


Example
-------

.. code-block:: python

    # producer.py

    from miPubSub import PubSub
    from proto.user_pb2 import User


    ps = PubSub('user_management')

    u = User(name='Adam West', email='adam.west@mail.com')

    ps.publish('signup_completed', u)


.. code-block:: python

    # consumer.py

    from miPubSub import PubSub
    from proto.user_pb2 import User


    ps = PubSub('mailer')

    @ps.listen('signup_completed', User)
    def on_signup_completed(user):
        # Send welcome email to: user.email
        pass

    ps.run()


How it works
------------

TBD

More details on rabbitmq pub/sub: https://www.rabbitmq.com/tutorials/tutorial-three-python.html


Authors
-------

- `@ArturZylinski <https://twitter.com/ArturZylinski>`_


License
-------

This project is licensed under the MIT License - see the `LICENSE <LICENSE>`_ file for details
