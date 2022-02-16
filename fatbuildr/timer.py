#!/usr/bin/env python3
#
# Copyright (C) 2021 Rackslab
#
# This file is part of Fatbuildr.
#
# Fatbuildr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fatbuildr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fatbuildr.  If not, see <https://www.gnu.org/licenses/>.

import threading
from datetime import datetime

from .log import logr

logger = logr(__name__)


class ServerTimer:
    def __init__(self, timeout=30):
        self.start = datetime.now().timestamp()
        self.timeout = timeout
        self.event = threading.Event()
        # Combine a threading condition and a set for a kind of reverse
        # semaphore to track all running instances threads.
        self._cond = threading.Condition(threading.Lock())
        self._tasks = set()

    def reset(self):
        logger.debug("Reseting timer")
        self.start = datetime.now().timestamp()

    @property
    def remaining(self):
        return max(0, (self.start + self.timeout) - datetime.now().timestamp())

    @property
    def notask(self):
        with self._cond:
            return not self._tasks

    @property
    def over(self):
        return self.notask and self.remaining == 0

    def register_task(self, task):
        with self._cond:
            self._tasks.add(task)

    def unregister_task(self, task):
        with self._cond:
            try:
                self._tasks.remove(task)
            except KeyError:
                pass
            if not self._tasks:
                self._cond.notify()

    def waitnotask(self, timeout):
        with self._cond:
            if not self._tasks:
                return True
            logger.debug("Waiting for timer lock for %f seconds" % (timeout))
            return self._cond.wait(timeout)

    def wait(self, timeout):
        notask = self.waitnotask(timeout=timeout)
        if notask and self.remaining:
            logger.debug("Waiting for %f seconds" % (self.remaining))
            self.event.wait(timeout=self.remaining)
