#include <iostream>
#include <queue>

/*
    A simple queue with an enforced limited size to mimic that of hardware queues.
    The logic to enforce a limited size queue is not complex.
    But moving it to it's own module is easier.
*/

template <typename T>
class LimitedQueue
{
private:
    std::queue<T> queue_;
    size_t max_size_;

public:
    LimitedQueue(size_t max_size) : max_size_(max_size) {}

    bool push(const T &value)
    {
        if (queue_.size() < max_size_)
        {
            queue_.push(value);
            return true;
        }
        else
        {
            return false;
        }
    }

    void pop()
    {
        if (!queue_.empty())
        {
            queue_.pop();
        }
    }

    T front() const
    {
        return queue_.front();
    }

    T back() const
    {
        return queue_.back();
    }

    size_t size() const
    {
        return queue_.size();
    }

    bool empty() const
    {
        return queue_.empty();
    }
};