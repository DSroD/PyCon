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

    def launch(self, service: Service, register_as: Optional[type[Service]] = None):
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

        task = asyncio.create_task(handled())
        self._services[task_id] = task

        if register_as:
            self._ioc.register(service, register_as)

    def stop(self):
        for task in self._services.values():
            task.cancel()

