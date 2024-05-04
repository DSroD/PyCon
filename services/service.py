"""
This module contains Service contract and a class responsible for.

launching long-running services.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Optional

from dependencies import Dependencies
from utils.exceptions import leaves

logger = logging.getLogger(__name__)


class Service(ABC):
    """Interface for service implementations."""
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the service."""

    @abstractmethod
    async def launch(self):
        """Launches the service."""

    @abstractmethod
    async def stop(self):
        """Stops the service."""


class ServiceLauncher:
    """Launches services."""
    def __init__(self, ioc: Dependencies):
        self._ioc = ioc
        self._services: dict[str, Task] = {}

    def launch(
            self,
            service: Service,
            register_as: Optional[type[Service]] = None,
            retry_on_fail=True,
    ):
        """
        Launch a service as an async task.

        :param service: Service to launch
        :param register_as: Register to IoC as given type
        :param retry_on_fail: Retry on RecoverableException
        :return:
        """

        async def retryable():
            while True:
                try:
                    logger.info("Launching service %s.", service.name)
                    await service.launch()
                except* RecoverableError as e:
                    if retry_on_fail:
                        excs: list[RecoverableError] = leaves(e)
                        delay_ms = max(map(lambda exc: exc.recovery_delay_ms, excs))
                        await asyncio.sleep(delay_ms / 1000)
                    else:
                        raise

        async def handled():
            try:
                await retryable()
            finally:
                await service.stop()
                referenced = self._services.get(service.name, None)
                if referenced == service:
                    self._services.pop(service.name)
                logger.info("Service %s stopped.", service.name)

        task = asyncio.create_task(handled())
        self._services[service.name] = task

        if register_as:
            self._ioc.register(service, register_as)

    def stop(self):
        """Cancels all service tasks."""
        for task in self._services.values():
            task.cancel()

    def is_running(self, name: str) -> bool:
        """
        Checks if a service is running.
        :param name: Name of the service.
        :return: If the service is running.
        """
        return name in self._services

    def stop_service(self, name: str):
        """
        Stops a service.
        :param name: Name of the service.
        """
        task = self._services.pop(name)
        task.cancel()


class RecoverableError(Exception):
    """Error wrapper for exceptions in services that are recoverable."""
    def __init__(self, error: Exception, recovery_delay_ms: int):
        """
        Signifies it is possible to recover from error.

        :param error: Inner exception.
        :param recovery_delay_ms: Recovery delay in milliseconds
        """
        self._error = error
        self.recovery_delay_ms = recovery_delay_ms

    def __str__(self):
        return str(self._error)
