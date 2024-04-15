# Tutorial on async

- sources: 
  - https://realpython.com/async-io-python/
  - https://realpython.com/python-async-features/
    
- concurrency
- threading
- multiprocessing

## concurrency vs parallelism vs threading

### parallelism

multiple operations at the same time. achieved by multiprocessing. using multiple CPUs

### concurrency

handles concurrent events hiding latency. context switching.
multiple tasks at the same time but not necessarily simultaneously.

Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at once.

Multiprocessing is a form of parallelism, with parallelism being a specific type (subset) of concurrency.

### asyncio

a library to write concurrent code. is a single-threaded, single process design.
it uses cooperative multitasking.
runs in a single thread of execution.

- asyncronous routines are able to pause while waiting on their result and let other routines in the meantime.

#### asyncio syntax

- async def: introduces a native coroutine or an asynchronous generator
- await: passes function control back to the event loop