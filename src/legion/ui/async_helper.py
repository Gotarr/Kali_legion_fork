"""
Qt + asyncio integration utilities.

Provides helper functions for integrating asyncio with PyQt6.
"""
import asyncio
import sys
from typing import Callable, Coroutine, Any

try:
    import qasync
    from PyQt6.QtWidgets import QApplication
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False


def setup_event_loop(app: 'QApplication') -> asyncio.AbstractEventLoop:
    """
    Setup asyncio event loop integrated with Qt.
    
    Uses qasync to integrate asyncio and Qt event loops.
    This is REQUIRED for scanner integration to work!
    
    Args:
        app: QApplication instance
        
    Returns:
        Event loop (qasync.QEventLoop if available, else default)
        
    Example:
        app = QApplication(sys.argv)
        loop = setup_event_loop(app)
        asyncio.set_event_loop(loop)
        
        # Now asyncio tasks work with Qt!
        loop.run_until_complete(my_async_function())
        loop.run_forever()
    """
    if not QASYNC_AVAILABLE:
        print("WARNING: qasync not available - scanner integration may not work!")
        print("Install with: pip install qasync")
        return asyncio.new_event_loop()
    
    loop = qasync.QEventLoop(app)
    return loop


def run_async_in_qt(coro: Coroutine[Any, Any, Any]) -> None:
    """
    Run an async coroutine in the current Qt event loop.
    
    Args:
        coro: Coroutine to run
        
    Example:
        async def my_scan():
            await scanner.queue_scan("192.168.1.1")
        
        # Call from Qt code:
        run_async_in_qt(my_scan())
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Create task in running loop
        asyncio.ensure_future(coro)
    else:
        # Run until complete
        loop.run_until_complete(coro)


class AsyncHelper:
    """
    Helper class for running async code from Qt signals/slots.
    
    Example:
        class MyWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.async_helper = AsyncHelper()
                
            def on_button_clicked(self):
                # Run async function from slot
                self.async_helper.run(self.do_async_work())
                
            async def do_async_work(self):
                await scanner.queue_scan("192.168.1.1")
    """
    
    def __init__(self):
        """Initialize async helper."""
        self._loop = asyncio.get_event_loop()
    
    def run(self, coro: Coroutine[Any, Any, Any]) -> None:
        """
        Run coroutine in event loop.
        
        Args:
            coro: Coroutine to run
        """
        asyncio.ensure_future(coro, loop=self._loop)
    
    def run_callback(self, callback: Callable[[], Coroutine[Any, Any, Any]]) -> Callable[[], None]:
        """
        Wrap async callback for use with Qt signals.
        
        Args:
            callback: Async callback function
            
        Returns:
            Sync wrapper function
            
        Example:
            # Async function
            async def on_scan_clicked():
                await scanner.queue_scan("192.168.1.1")
            
            # Connect to signal
            button.clicked.connect(
                async_helper.run_callback(on_scan_clicked)
            )
        """
        def wrapper():
            self.run(callback())
        return wrapper
