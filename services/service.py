"""
This module contains Service contract and a class responsible for.

launching long-running services.
"""
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Optional

from dependencies import Dependencies


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
        self._services: dict[uuid.UUID, Task] = {}

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
        task_id = uuid.uuid4()

        async def handled():
            try:
                await service.launch()
            except asyncio.CancelledError:
                await service.stop()
                self._services.pop(task_id)
                logger.info("Service %s stopped.", service.name)
                raise

        async def retryable():
            while True:
                try:
                    await handled()
                except RecoverableError as e:
                    await asyncio.sleep(e.recovery_delay_ms / 1000)

        coro = retryable() if retry_on_fail else handled()

        task = asyncio.create_task(coro)
        self._services[task_id] = task

        if register_as:
            self._ioc.register(service, register_as)

    def stop(self):
        """Cancels all service tasks."""
        for uid in self._services:
            task = self._services.pop(uid)
            task.cancel()


class RecoverableError(Exception):
    """Error wrapper for exceptions in services that are recoverable."""
    def __init__(self, error: Exception, recovery_delay_ms: int):
        """
        :param error: Inner exception.

        :param recovery_delay_ms: Recovery delay in milliseconds
        """
        self._error = error
        self.recovery_delay_ms = recovery_delay_ms

    def __str__(self):
        return str(self._error)
