# aurorafimpro/aurorafimpro/gui/widgets/worker.py
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool
import traceback
import sys


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished: No data
    error: tuple (exctype, value, traceback.format_exc())
    result: object data returned from processing
    progress: int indicating % progress (optional)
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    # progress = Signal(int) # Example for progress reporting


class Worker(QRunnable):
    """
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to callback function
    :param kwargs: Keywords to pass to callback function
    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for thread pool)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress # Example for progress

    @Slot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # Return the result of the processing
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()  # Done

# Example usage (not part of the class, just for understanding):
# def some_long_function(arg1, arg2):
#     import time
#     time.sleep(5) # Simulate work
#     return f"Result: {arg1}, {arg2}"

# def handle_result(result):
#     print("Got result:", result)

# def handle_error(error_tuple):
#     print("Error:", error_tuple)

# def handle_finished():
#     print("Worker finished.")

# if __name__ == '__main__':
#     from PySide6.QtWidgets import QApplication
#     app = QApplication([]) # QApplication instance is needed for QThreadPool with signals/slots

#     threadpool = QThreadPool.globalInstance()
#     print(f"Max SThreads: {threadpool.maxThreadCount()}")

#     worker = Worker(some_long_function, "hello", "world")
#     worker.signals.result.connect(handle_result)
#     worker.signals.error.connect(handle_error)
#     worker.signals.finished.connect(handle_finished)

#     threadpool.start(worker)

#     app.exec() # Keep event loop running for signals
