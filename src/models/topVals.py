import heapq

class TopValues:
    '''
    Object to keep track of the top scoring URLS.
    Note is not thread safe and will need semaphores to
    use correctly if trying to multi on this object struct. 
    '''
    def __init__(self, capacity):
        self.capacity = capacity
        self.heap = []

    def add(self, value):
        if len(self.heap) < self.capacity:
            heapq.heappush(self.heap, (value[1], value[0]))
        else:
            # Push new value and pop the smallest value
            heapq.heappushpop(self.heap, (value[1], value[0]))

    def get_top_values(self):
        return sorted(self.heap, reverse=True)  # Return values in descending order

    def remove_from_heap(self, value):
        """Remove a value from the heap."""
        try:
            index = self.heap.index(value)
            self.heap[index] = self.heap[-1]  # Replace with last element
            self.heap.pop()  # Remove last element
            if index < len(self.heap):
                heapq._siftup(self.heap, index)  # Restore heap property
                heapq._siftdown(self.heap, 0, index)
        except ValueError:
            pass  # Value not found in heap

    def pop_highest(self):
        if self.heap:
            # Remove and return the largest element
            to_return = heapq.nlargest(1, self.heap).pop()
            self.remove_from_heap(to_return)   
        return to_return