import os
import uuid
import pathlib
import urllib.parse
from typing import Union

from paramiko.client import SSHClient

from file_queue.core import Queue, JSONSerializer, DummyLock, Job


class SSHQueue(Queue):
    def __init__(
        self,
        directory: Union[str, pathlib.Path],
        job_serializer_class=JSONSerializer,
        result_serializer_class=JSONSerializer,
        lock_class=DummyLock,
        job_class=Job,
    ):
        directory = self._create_client(directory)
        super().__init__(
            directory=directory,
            job_serializer_class=job_serializer_class,
            result_serializer_class=result_serializer_class,
            lock_class=lock_class,
            job_class=job_class,
        )

    def _create_client(self):
        if not self.directory.startswith("ssh://"):
            raise ValueError("directory must start with ssh://")

        p = urllib.parse.urlparse(self.directory)
        params = {
            "hostname": p.hostname,
            "port": int(p.port or 22),
            "username": p.username or os.getlogin(),
            "password": p.password,
            "path": p.path,
        }

        self._ssh_client = SSHClient()
        self._ssh_client.connect(
            hostname=params["hostname"],
            port=params["port"],
            username=params["username"],
            password=params["password"],
        )
        self._sftp_client = self._ssh_client.open_sftp()
        return pathlib.Path(params["path"])

    def ensure_directories(self):
        commands = []
        for directory in [
            self.job_directory,
            self.result_directory,
            self.worker_directory,
            self.queued_directory,
            self.finished_directory,
            self.failed_directory,
            self.started_directory,
        ]:
            commands.append(f"mkdir -p {directory}")
        self._ssh_client.exec_command(" && ".join(commands))

    def enqueue(self, func, *args, **kwargs):
        job_name = str(uuid.uuid4())
        job = Job(queue=self, id=job_name)
        job_message = {
            "module": func.__module__,
            "name": func.__name__,
            "args": args,
            "kwargs": kwargs,
        }
        with self._sftp_client.open(job.job_path, "wb") as f:
            f.write(self.job_serializer.dumps(job_message))

        self._sftp_client.symlink(self.queued_directory / job.id, job.job_path)
        return job

    def dequeue(self, timeout: float = 30, interval: int = 1):
        raise NotImplementedError()

    def stats(self):
        raise NotImplementedError()