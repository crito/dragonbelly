import threading
from time import sleep

class ThreadPool(object):
    """
    Flexible thread pool class.  Creates a pool of threads, then
    accepts tasks that will be dispatched to the next available
    thread.
    """
    def __init__(self, num_threads):
        """Initialize the thread pool with num_threads workers."""
        self._threads = []
        self._resize_lock = threading.Condition(threading.Lock())
        self._task_lock = threading.Condition(threading.Lock())
        self._tasks = []
        self._is_joining = False
        self.set_thread_count(num_threads)

    def set_thread_count(self, new_num_threads):
        """ External method to set the current pool size.  Acquires
        the resizing lock, then calls the internal version to do real
        work."""
        # Can't change the thread count if we're shutting down the pool!
        if self._is_joining:
            return False

        self._resize_lock.acquire()
        try:
            self._set_thread_count_no_lock(new_num_threads)
        finally:
            self._resize_lock.release()
        return True

    def _set_thread_count_no_lock(self, new_num_threads):
        """Set the current pool size, spawning or terminating threads
        if necessary. Internal use only; assumes the resizing lock is
        held."""
        # If we need to grow the pool, do so
        while new_num_threads > len(self._threads):
            new_thread = ThreadPoolThread(self)
            self._threads.append(new_thread)
            new_thread.start()
        # If we need to shrink the pool, do so
        while new_num_threads < len(self._threads):
            self._threads[0].go_away()
            del self._threads[0]

    def get_thread_count(self):
        """Return the number of threads in the pool."""
        self._resize_lock.acquire()
        try:
            return len(self._threads)
        finally:
            self._resize_lock.release()

    def queue_task(self, task, args=None, task_callback=None):
        """Insert a task into the queue. task must be callable;
        args and task_callback can be None."""
        if self._is_joining == True:
            return False
        if not callable(task):
            return False

        self._task_lock.acquire()
        try:
            self._tasks.append((task, args, task_callback))
            return True
        finally:
            self._task_lock.release()

    def get_next_task(self):
        """Retrieve the next task from the task queue. For use
        only by ThreadPoolThread objects contained in the pool."""
        self._task_lock.acquire()
        try:
            if self._tasks == []:
                return (None, None, None)
            else:
                return self._tasks.pop(0)
        finally:
            self._task_lock.release()

    def join_all(self, wait_for_tasks = True, wait_for_threads = True):
        """Clear the task queue and terminate all pooled threads,
        optionally allowing the tasks and threads to finish."""
        # Mark the pool as joining to prevent any more task queueing
        self._is_joining = True

        # Wait for tasks to finish
        if wait_for_tasks:
            while self._tasks != []:
                sleep(.1)

        # Tell all the threads to quit
        self._resize_lock.acquire()
        try:
            self._set_thread_count_no_lock(0)
            self._is_joining = True

            # Wait until all threads have exited
            if wait_for_threads:
                for t in self._threads:
                    t.join()
                    del t

            # Reset the pool for potential reuse
            self._is_joining = False
        finally:
            self._resize_lock.release()

class ThreadPoolThread(threading.Thread):
    """
    Pooled thread class.
    """
    thread_sleep_time = 0.1

    def __init__(self, pool):
        """Initialize the thread and remember the pool."""
        threading.Thread.__init__(self)
        self._pool = pool
        self._is_dying = False

    def run(self):
        """Until told to quit, retrieve the next task and execute
        it, calling the callback if any."""
        while self._is_dying == False:
            cmd, args, callback = self._pool.get_next_task()
            # If there's nothing to do, just sleep a bit
            if cmd is None:
                sleep(ThreadPoolThread.thread_sleep_time)
            elif args is None:
                cmd(args)
            elif callback is None:
                cmd()
            else:
                callback(cmd(args))

    def go_away(self):
        """Exit the run loop next time through."""
        self.__isDying = True
