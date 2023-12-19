import unittest

from text_processor import TextProcessor

class TextProcessorTest(unittest.TestCase):
    def test_get_heading_for_token(self):
        filename = "RegularExtractor/data/alza.html.processed"

        with open(filename, "r", encoding="utf8") as file:
            text = file.read()

        text_processor = TextProcessor(filename)
        text_processor.process(text)

        heading = text_processor.get_heading_for_token(5222)

        print(text_processor._conlu_to_text(text_processor.flattened_tokens[heading[0]:heading[1]]))

        self.assertEqual(heading, (5202,5256))
        
if __name__ == '__main__':
    unittest.main()