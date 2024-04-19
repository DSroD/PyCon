import asyncio
import uuid
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Optional

from dependencies import Dependencies


class Service(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def launch(self):
        pass

    @abstractmethod
    async def stop(self):
        pass


class ServiceLauncher:
    def __init__(self, ioc: Dependencies):
        self._ioc = ioc
        self._services: dict[uuid.UUID, Task] = dict()

    def launch(
            self,
            service: Service,
            register_as: Optional[type[Service]] = None,
            retry_on_fail=True,
    ):
        task_id = uuid.uuid4()

        async def handled():
            try:
                await service.launch()
            except asyncio.CancelledError:
                await service.stop()
                self._services.pop(task_id)
                # TODO: logger
                print(f"Service {service.name} stopped.")
                raise

        async def retryable():
            while True:
                try:
                    await handled()
                except asyncio.CancelledError:
                    raise
                except RecoverableError as e:
                    await asyncio.sleep(e.recovery_delay_ms / 1000)
                    pass

        coro = retryable() if retry_on_fail else handled()

        task = asyncio.create_task(coro)
        self._services[task_id] = task

        if register_as:
            self._ioc.register(service, register_as)

    def stop(self):
        for task in self._services.values():
            task.cancel()


class RecoverableError(Exception):
    def __init__(self, error: Exception, recovery_delay_ms: int):
        self._error = error
        self.recovery_delay_ms = recovery_delay_ms

    def __str__(self):
        return str(self._error)
