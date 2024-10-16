import os
import logging
from typing import Any, Dict, List, Literal, TYPE_CHECKING

# if TYPE_CHECKING:
from solace.messaging.config.solace_properties import (
    transport_layer_properties,
    service_properties,
    authentication_properties
)

# Constants
SOLBROKER_PROPERTIES_KEY = 'solbrokerProperties'
HOST_SECURED = 'solace.messaging.transport.host.secured'
HOST_COMPRESSED = 'solace.messaging.transport.host.compressed'
SEMP_HOSTNAME_KEY = 'solace.semp.hostname'
SEMP_USERNAME_KEY = 'solace.semp.username'
SEMP_PASSWORD_KEY = 'solace.semp.password'
SEMP_PORT_TO_CONNECT = '1943'
VALID_CERTIFICATE_AUTHORITY = 'public_root_ca'

def configure_logger() -> logging.Logger:
    """Configure and return the logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Configure logger
logger = configure_logger()

class Boot:
    """Class for instantiating the broker properties from environment."""

    @staticmethod
    def read_solbroker_props() -> dict:
        """
        Reads Solbroker properties from environment variables.

        Returns:
            dict: The Solbroker properties.
        """
        broker_properties = {
            transport_layer_properties.HOST: os.getenv('SOLACE_HOST', 'tcp://localhost:55554'),
            HOST_SECURED: os.getenv('SOLACE_HOST_SECURED', 'tcps://localhost:55443'),
            HOST_COMPRESSED: os.getenv('SOLACE_HOST_COMPRESSED', 'tcp://localhost:55003'),
            service_properties.VPN_NAME: os.getenv('SOLACE_VPN_NAME', 'default'),
            authentication_properties.SCHEME_BASIC_USER_NAME: os.getenv('SOLACE_USERNAME', 'default'),
            authentication_properties.SCHEME_BASIC_PASSWORD: os.getenv('SOLACE_PASSWORD', 'default')
        }

        # Validate required properties
        required_keys = [
            transport_layer_properties.HOST,
            HOST_SECURED,
            service_properties.VPN_NAME,
            authentication_properties.SCHEME_BASIC_USER_NAME,
            authentication_properties.SCHEME_BASIC_PASSWORD
        ]

        missing_keys = [key for key in required_keys if broker_properties[key] is None]
        if missing_keys:
            logger.warning(f'Missing required Solbroker properties: {missing_keys}')
            return {}

        logger.info(
            f"\n\n********************************BROKER PROPERTIES**********************************************"
            f"\nHost: {broker_properties.get(transport_layer_properties.HOST)}"
            f"\nSecured Host: {broker_properties.get(HOST_SECURED)}"
            f"\nCompressed Host: {broker_properties.get(HOST_COMPRESSED)}"
            f"\nVPN: {broker_properties.get(service_properties.VPN_NAME)}"
            f"\nUsername: {broker_properties.get(authentication_properties.SCHEME_BASIC_USER_NAME)}"
            f"\nPassword: <hidden>"
            f"\n***********************************************************************************************\n"
        )
        return broker_properties

    @staticmethod
    def read_semp_props() -> dict:
        """
        Reads SEMP properties from environment variables.

        Returns:
            dict: The SEMP properties.
        """
        semp_properties = {
            SEMP_HOSTNAME_KEY: os.getenv('SOLACE_SEMP_HOSTNAME', 'https://localhost:8080'),
            SEMP_USERNAME_KEY: os.getenv('SOLACE_SEMP_USERNAME', 'admin'),
            SEMP_PASSWORD_KEY: os.getenv('SOLACE_SEMP_PASSWORD', 'admin'),
        }

        logger.info(
            f"\n\n********************************SEMP PROPERTIES***********************************************"
            f"\nSEMP Hostname: {semp_properties.get(SEMP_HOSTNAME_KEY)}"
            f"\nSEMP Username: {semp_properties.get(SEMP_USERNAME_KEY)}"
            f"\nPassword: <hidden>"
            f"\n***********************************************************************************************\n"
        )

        return semp_properties

    @staticmethod
    def broker_properties() -> dict:
        """
        Reads the Solbroker properties from environment variables.

        Returns:
            dict: The broker properties.
        """
        try:
            props = Boot.read_solbroker_props()
            return props
        except Exception as exception:
            logger.error(f"Unable to read broker properties. Exception: {exception}")
            raise
