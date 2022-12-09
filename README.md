# File Queue

A task queue using the filesystem as the message queue. This project
was motivated by the use case where it is hard or near impossible to
run a persistent service like redis, rabbitmq, or database. Initial
motivation was a way to submit tasks to an HPC cluster and process the
tasks in HPC worker nodes without a running service on the login node.

This project uses [filelock](https://pypi.org/project/filelock/). With
this library I think it is safe to say that if the underlying
filesystem obeys [flock](https://linux.die.net/man/2/flock) calls then
each task is guaranteed to be executed once. For non-conforming
filesystems at least once execution is guaranteed.

Keep in mind that NFS v2 and v3 have an external file lock system via
`rpc.lockd`. The current NFS v4 has built in support for file locks
but the problem is that many HPC centers still use v3. Otherwise it is
safe these days to assume your filesystem supports locks. If you have
the ability to run persistent services then running Redis, RabbitMQ,
or using a database is highly encouraged instead of using
`file-queue`.

Keep in mind that task state is managed on the filesystem. So do not
use this if you have an enormous amount of tasks. Think of possibly
chunking them.

# API

Creating a queue is as simple as supplying a directory where the queue
will reside.

```python
from file_queue import Queue

queue = Queue("path/to/queue")
```

Submitting jobs and monitoring over SSH is also supported via the same
interface. Workers currently cannot connect over SSH.

```python
from file_queue.plugins import SSHQueue

queue = SSHQueue("ssh://<username>:<password>@<hostname>:<port>/<path>")
```

Next we can submit/enqueue jobs to the queue.

```python
import operator

job = queue.enqueue(operator.add, 1, 2)
```

You can immediately try and fetch the result of the job or get its
status.

```python
print(job.get_status())
print(job.result)
```

You can wait on the job to finish

```python
result = job.wait()
```

# Worker

Starting a worker is as simple as giving a filesystem directory where
the queue will reside.

```shell
file-queue-worker --path ./path/to/queue
```

A `dask` worker is supported via `file_queue.plugin.dask.DaskWorker`
for sending jobs to the dask cluster instead of executing locally.

A worker runs a continuous loop gathering tasks in the task queue. The
worker creates a file `path/to/queue/workers/<worker-id>` where it
will:
 - continuously touch the file every 30 seconds
 - check that the file exists and if not stop the worker

# License

[BSD-3]()
