import unittest

from paths import PathLike, Url, UrlCompatible, UrlListCompatible

from k_runner.multiExecute import MultiExecuteOnFiles, Path


class MultiExecuteCompatibilityTests(unittest.TestCase):
    def test_paths_compatibility_symbols_are_available(self):
        self.assertIs(Path, PathLike)
        self.assertTrue(issubclass(Url, PathLike))
        self.assertIsNotNone(UrlCompatible)
        self.assertIsNotNone(UrlListCompatible)

    def test_file_inputs_are_converted_to_absolute_urls(self):
        executor = MultiExecuteOnFiles(
            "echo $FILE",
            files=None,
            numThreads=1,
        )
        converted_file = executor._filenameConversion("test-input.txt")

        self.assertIsInstance(converted_file, Url)
        self.assertTrue(converted_file.isAbsolute)


if __name__ == "__main__":
    unittest.main()
