# -*- coding: utf-8 -*-

from logging import getLogger
from os import getenv
from google.protobuf.empty_pb2 import Empty
from pika import BlockingConnection, URLParameters, BasicProperties

PB_CONTENT_TYPE = 'application/vnd.google.protobuf'

_LOGGER = getLogger(__name__)

class PubSub(object):
    @staticmethod
    def _build_ampq_url():
        return 'amqp://{user}:{password}@{host}:5672/%2F?connection_attempts=3&heartbeat_interval=3600'.format(
            user=getenv('RABBITMQ_USER', 'guest'),
            password=getenv('RABBITMQ_PASS', 'guest'),
            host=getenv('RABBITMQ_HOST', 'localhost'))

    def __init__(self, app_id, ampq_url=None):
        self.app_id = app_id
        if not ampq_url:
            ampq_url = self._build_ampq_url()

        parameters = URLParameters(ampq_url)
        self.channel = BlockingConnection(parameters).channel()
        self.channel.confirm_delivery()

        self.process_functions = {}

    def publish(self, event_name, event=None):
        if event is None:
            event = Empty()

        # from google.protobuf.message import Message
        # assert parent class is Message
        exchange = f'{event_name}.{event.__class__.__name__}'

        self.channel.exchange_declare(exchange_type='fanout', exchange=event_name)

        properties = BasicProperties(app_id=self.app_id, content_type=PB_CONTENT_TYPE)
        self.channel.basic_publish(
            exchange=event_name,
            routing_key='ALL', # routing key is ignored for 'fanout' exchange
            body=event.SerializeToString(),
            properties=properties)

    def on_message_callback(self, channel, method_frame, header_frame, body):
        # print("on_message_callback", channel, method_frame, header_frame, body)
        # TODO: if content_type !== PB_CONTENT_TYPE

        # TODO: maybe use google.protobuf.reflection ?
        # https://developers.google.com/protocol-buffers/docs/reference/python/google.protobuf.reflection-module#MakeClass

        event_name = method_frame.exchange
        func, EventClass = self.process_functions[event_name]
        
        event = EventClass()
        event.ParseFromString(body)

        func(event)

        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def listen(self, event_name, EventClass):
        """A decorator that is used to register events listener function for a
        given channel.
        """

        def decorator(func):
            queue_name = f"{self.app_id}.{event_name}"
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                exclusive=False,
                auto_delete=False)

            self.channel.exchange_declare(exchange_type='fanout', exchange=event_name)
            self.channel.queue_bind(queue=queue_name, exchange=event_name)

            self.process_functions[event_name] = (func, EventClass)
            self.channel.basic_consume(self.on_message_callback, queue=queue_name)

            return func

        return decorator

    def run(self):
        self.channel.start_consuming()
