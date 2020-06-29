from signal import signal, SIGCHLD
from os import fork, waitpid

from jobs.KarImport import KarImportJob


class Cronjobs:
    jobs = []

    def wait(self):
        for chhild_pid in self.jobs:
            waitpid(chhild_pid, 0)

    def start(self, signal_func=None):
        self.karImport(signal_func)

    def run(self, signal_func=None):
        self.start(signal_func)
        self.wait()

    def fork(self, signal_func=None):
        child_pid = fork()
        if child_pid > 0:
            if signal_func is not None:
                signal(SIGCHLD, signal_func)
            self.jobs.append(child_pid)
        return child_pid

    def karImport(self, signal_func=None):
        if self.fork(signal_func) > 0:
            return

        import_job = KarImportJob.find()
        if import_job is None:
            return

        import_job.run()


if __name__ == "__main__":
    Cronjobs().run()
