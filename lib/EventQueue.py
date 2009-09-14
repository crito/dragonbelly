class EventQueue(queue.Queue):
    """
    FIFO Queue qith Priority handling.
    See Python Cookbook, chapter 9, recipe 3 (Priority Queue).
    """
    def _init(self, maxsize):
        """Initializes the array to use for the eventQueue. Called by 
        __init__() of the parent class."""
        self.maxsize = maxsize
        self.queue = [ ]

    def _qsize(self):
        """Return current amount of elements of the EventQueue."""
        return len(self.queue)

    def _empty(self):
        """Check whether the EventQueue is empty."""
        return not self.queue

    def _full(self):
        """Check whether EventQueue is full."""
        return self.maxsize > 0 and len(self.queue) >= self.maxsize

    def _put(self, item):
        """Put a new item onto the queue."""
        heapq.heappush(self.queue, item)

    def _get(self):
        """Retrieve next item from the queue."""
        return heapq.heappop(self.queue)

    def put(self, item, priority=0, block=True, timeout=None):
        """Override Queue.Queue's put function to incorporate the priority
        argument."""
        decorated_item = priority, time.time(), item
        queue.Queue.put(self, decorated_item, block, timeout)

    def get(self, block=True, timeout=None):
        """Override Queue.Queue's get function."""
        priority, time_posted, item = queue.Queue.get(self, block, timeout)
        return item
