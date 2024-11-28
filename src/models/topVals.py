import heapq

class TopValues:
    def __init__(self, capacity):
        self.capacity = capacity
        self.heap = []

    def add(self, value):
        if value[0] in [t[1] for t in self.heap]:
            return

        if len(self.heap) < self.capacity:
            heapq.heappush(self.heap, (value[1], value[0]))
        else:
            heapq.heappushpop(self.heap, (value[1], value[0]))

    def get_top_values(self):
        return sorted(self.heap, reverse=True)

    def remove_from_heap(self, value):
        try:
            index = self.heap.index(value)
            self.heap[index] = self.heap[-1]
            self.heap.pop()
            if index < len(self.heap):
                heapq._siftup(self.heap, index)
                heapq._siftdown(self.heap, 0, index)
        except ValueError:
            pass

    def pop_highest(self):
        if self.heap:
            to_return = heapq.nlargest(1, self.heap).pop()
            self.remove_from_heap(to_return)   
        return to_return
