import inspect
import unittest

from cogs.events import message_edit_listener


class MessageEditListenerImportTests(unittest.TestCase):
    def test_quest_listeners_are_async_functions(self):
        for listener in (
            message_edit_listener.pin_timer_listener,
            message_edit_listener.lab_pc_unlock_listener,
        ):
            with self.subTest(listener=listener):
                self.assertTrue(inspect.iscoroutinefunction(listener))


if __name__ == "__main__":
    unittest.main()
