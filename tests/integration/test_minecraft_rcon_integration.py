"""Minecraft RCON integration tests."""
# pylint: disable=missing-class-docstring,attribute-defined-outside-init
import asyncio
import unittest

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from messages.rcon import RconCommand
from models.server import Server
from rcon.rcon_client import RconClientManager
from rcon.request_id import IntRequestIdProvider


class MinecraftRconIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def run(self, result=None):
        with (DockerContainer("itzg/minecraft-server")
              .with_env("EULA", "TRUE")
              .with_env("RCON_PASSWORD", "test")
              .with_env("RCON_PORT", "25575")
              .with_bind_ports(25575, 25575)
                as container):
            self.container = container
            wait_for_logs(container, "Thread RCON Listener started")
            super().run(result)

    async def test_command(self):
        """
        Sends command to the testcontainer minecraft server.

        Expects to receive a response from the server.
        """
        async with RconClientManager(
            request_id_provider=IntRequestIdProvider(),
            server=Server(
                type=Server.Type.MINECRAFT_SERVER,
                name="test",
                host=self.container.get_container_host_ip(),
                port=25565,
                rcon_port=25575,
                rcon_password="test",
                description="integration test server",
            )
        ) as client:
            command = RconCommand(
                issuing_user="test",
                command="time set day",
            )

            responses = []

            def on_response(packet):
                responses.append(packet)
                read_task.cancel()
            try:
                read_task = asyncio.create_task(client.read(on_response))
                write_task = asyncio.create_task(client.send_command(command))

                await asyncio.wait([read_task, write_task])
            except asyncio.IncompleteReadError:
                # Cancelling the task can fire this error in read coroutine, failing the test
                pass

            self.assertEqual(1, len(responses))
            self.assertEqual("Set the time to 1000", responses[0].response)