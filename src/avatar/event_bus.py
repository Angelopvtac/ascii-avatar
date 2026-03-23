"""ZeroMQ PUSH/PULL event bus for avatar IPC."""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

import zmq

log = logging.getLogger(__name__)

DEFAULT_SOCKET_PATH = "/tmp/ascii-avatar.sock"


@dataclass
class AvatarEvent:
    event: str
    state: str = ""
    text: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AvatarEvent:
        if "event" not in d:
            raise ValueError("Event dict must contain 'event' key")
        return cls(
            event=d["event"],
            state=d.get("state", ""),
            text=d.get("text", ""),
            data=d.get("data", {}),
        )


class EventBus:
    """Receives avatar events over a ZeroMQ PULL socket.

    Args:
        socket_path: Path for the Unix domain socket.
    """

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH) -> None:
        self._socket_path = socket_path
        self._context: zmq.Context | None = None
        self._socket: zmq.Socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.on_event: Callable[[AvatarEvent], None] | None = None

    @property
    def socket_path(self) -> str:
        return self._socket_path

    def start(self) -> None:
        self._stop_event.clear()
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.PULL)
        self._socket.bind(f"ipc://{self._socket_path}")

        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _recv_loop(self) -> None:
        assert self._socket is not None
        poller = zmq.Poller()
        poller.register(self._socket, zmq.POLLIN)

        while not self._stop_event.is_set():
            socks = dict(poller.poll(timeout=100))
            if self._socket in socks:
                try:
                    raw = self._socket.recv(zmq.NOBLOCK)
                    data = json.loads(raw)
                    event = AvatarEvent.from_dict(data)
                    if self.on_event:
                        self.on_event(event)
                except (json.JSONDecodeError, ValueError) as e:
                    log.warning("Malformed event: %s", e)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        if self._socket is not None:
            self._socket.close()
        if self._context is not None:
            self._context.term()
        # Clean up socket file
        if os.path.exists(self._socket_path):
            os.unlink(self._socket_path)
