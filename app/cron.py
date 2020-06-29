from os import fork, waitpid
from signal import signal, SIGCHLD
from sys import exit as sys_exit
from typing import Callable, Optional

from jobs.KarImport import KarImportJob


class Cronjobs:
    jobs = []

    def wait(self) -> None:
        for chhild_pid in self.jobs:
            waitpid(chhild_pid, 0)

    def start(self, signal_func: Optional[Callable] = None) -> None:
        self.karImport(signal_func)

    def run(self, signal_func: Optional[Callable] = None) -> None:
        self.start(signal_func)
        self.wait()

    def fork(self, signal_func: Optional[Callable] = None) -> int:
        child_pid = fork()
        if child_pid > 0:
            if signal_func is not None:
                signal(SIGCHLD, signal_func)
            self.jobs.append(child_pid)
        return child_pid

    def karImport(self, signal_func: Optional[Callable] = None) -> None:
        if self.fork(signal_func) > 0:
            return

        import_job = KarImportJob.find()
        if import_job is None:
            sys_exit(0)

        import_job.run()
        sys_exit(0)


if __name__ == "__main__":
    Cronjobs().run()
