from os import waitpid
from time import sleep
from cron import Cronjobs

cronjob = Cronjobs()


def child_done() -> None:
    waitpid(-1, 0)


while True:
    sleep(300)
    cronjob.start(child_done)
