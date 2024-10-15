"""Solace Message Queue."""

import asyncio
import json
import logging
import time
from logging import getLogger
from typing import Any, Dict, List, Literal, TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from llama_deploy.message_queues.base import BaseMessageQueue
from llama_deploy.messages.base import QueueMessage
from llama_deploy.message_consumers.base import BaseMessageQueueConsumer, StartConsumingCallable

from .boot import Boot
# if TYPE_CHECKING:
#     from solace.messaging.resources.message import InboundMessage
#     from solace.messaging.resources.topic_subscription import TopicSubscription
#     from solace.messaging.messaging_service import MessagingService
#     from solace.messaging.resources.topic import Topic
#     from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.messaging_service import MessagingService
from solace.messaging.errors.pubsubplus_client_error import PubSubPlusClientError, IllegalStateError
from solace.messaging.resources.topic_subscription import TopicSubscription
from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.resources.topic import Topic

# Constants
MAX_SLEEP = 10

def configure_logger() -> logging.Logger:
    """Configure and return the logger."""
    logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Configure logger
logger = configure_logger()

class MessageHandlerImpl(MessageHandler):
    """Callback handler to receive messages."""

    def __init__(self, consumer: BaseMessageQueueConsumer):
        """
        Initialize the message handler with a consumer.

        Args:
            consumer (BaseMessageQueueConsumer): The consumer to process the messages.
        """
        self.consumer = consumer

    def on_message(self, message: 'InboundMessage'):
        """
        Message receive callback.

        Args:
            message (InboundMessage): The received message.
        """
        topic = message.get_destination_name()
        payload_as_string = message.get_payload_as_string()
        correlation_id = message.get_correlation_id()

        message_details = {
            "topic": topic,
            "payload": payload_as_string,
            "correlation_id": correlation_id
        }

        # Log the consumed message in JSON format
        logger.debug(f"Consumed message: {json.dumps(message_details, indent=2)}")

        # Parse the payload and validate the queue message
        queue_message_data = json.loads(payload_as_string)
        queue_message = QueueMessage.model_validate(queue_message_data)

        # Process the message using the consumer
        asyncio.run(self.consumer.process_message(queue_message))

class SolaceMessageQueueConfig(BaseSettings):
    """Solace PubSub+ message queue configuration."""
    model_config = SettingsConfigDict(env_prefix="SOLACE_")
    type: Literal["solace"] = Field(default="solace", exclude=True)

class SolaceMessageQueue(BaseMessageQueue):
    """Solace PubSub+ Message Queue."""
    messaging_service: MessagingService = None

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Solace message queue."""
        super().__init__()
        broker_props = Boot.broker_properties()
        self.messaging_service = MessagingService.builder().from_properties(broker_props).build()

    async def _establish_connection(self) -> "Connection":
        """Establish and return a new connection to the Solace server."""
        try:
            return self.messaging_service.connect()
        except PubSubPlusClientError as exception:
            logger.error(f"Failed to establish connection: {exception}")
            raise

    async def _publish(self, message: QueueMessage) -> None:
        """Publish message to the queue."""
        if not self.messaging_service.is_connected:
            await self._establish_connection()

        logger.debug(f"Publishing message: {message}")
        topic = Topic.of(message.type)
        message_body = json.dumps(message.model_dump())

        try:
            direct_publish_service = self.messaging_service.create_direct_message_publisher_builder() \
                .on_back_pressure_reject(buffer_capacity=0).build()
            pub_start = direct_publish_service.start_async()
            pub_start.result()
            direct_publish_service.publish(destination=topic, message=message_body)
            logger.info(f"Published message: {message.id_}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise
        finally:
            direct_publish_service.terminate()

    async def register_consumer(self, consumer: BaseMessageQueueConsumer) -> StartConsumingCallable:
        """
        Register a new consumer.

        Args:
            consumer (BaseMessageQueueConsumer): The consumer to register.
        
        Returns:
            StartConsumingCallable: A callable to start consuming messages.
        """
        consumer_subscription = consumer.message_type
        topics = [TopicSubscription.of(consumer_subscription)]
        logger.debug(f"Consumer subscription: {topics}")

        try:
            if not self.messaging_service.is_connected:
                await self._establish_connection()

            direct_receive_service = self.messaging_service.create_direct_message_receiver_builder() \
                .with_subscriptions(topics).build()
            direct_receive_service.start()
            direct_receive_service.receive_async(MessageHandlerImpl(consumer))

            for topic in topics:
                direct_receive_service.add_subscription(topic)

            logger.debug(f"Consumer subscribed to: {consumer_subscription}")
            await asyncio.sleep(MAX_SLEEP)

            async def start_consuming_callable() -> None:
                await asyncio.Future()

            return start_consuming_callable
        except (PubSubPlusClientError, IllegalStateError) as e:
            logger.error(f"Failed to register consumer: {e}")
            raise

    async def deregister_consumer(self, consumer: BaseMessageQueueConsumer) -> None:
        """
        Deregister a consumer.

        Args:
            consumer (BaseMessageQueueConsumer): The consumer to deregister.
        """
        consumer_subscription = consumer.message_type
        topics = [TopicSubscription.of(consumer_subscription)]

        try:
            direct_receive_service = self.messaging_service.create_direct_message_receiver_builder() \
                .with_subscriptions(topics).build()
            direct_receive_service.start()
            direct_receive_service.receive_async(MessageHandlerImpl(consumer))

            for topic in topics:
                direct_receive_service.remove_subscription(topic)

            logger.info(f"Consumer deregistered from: {consumer_subscription}")
            time.sleep(MAX_SLEEP)
        except Exception as e:
            logger.error(f"Failed to deregister consumer: {e}")
            raise
        finally:
            direct_receive_service.terminate()

    async def processing_loop(self) -> None:
        """A loop for getting messages from queues and sending to consumer."""
        pass

    async def launch_local(self) -> asyncio.Task:
        """Launch the message queue locally, in-process."""
        return asyncio.create_task(self.processing_loop())

    async def launch_server(self) -> None:
        """Launch the message queue server."""
        pass

    async def cleanup_local(self, message_types: List[str], *args: Any, **kwargs: Dict[str, Any]) -> None:
        """Perform any clean up of queues and exchanges."""
        pass

    def as_config(self) -> BaseModel:
        """Return the configuration of the Solace message queue."""
        return SolaceMessageQueueConfig()