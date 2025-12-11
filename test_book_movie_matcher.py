"""
Test Suite for Book–Movie Matcher Project.
This Test Suit Covers Input Cleaning, CSV Data, Book Model Behaviour,
"""

import unittest
import os
import book_movie_matcher as app


"""This test case checks whether the input is properly validated or not"""
class TestInputCleaning(unittest.TestCase):

    def test_clean_text_spaces(self):
        """Extra spaces are removed"""
        result = app.tidy("   Inception!!    ")
        self.assertEqual(result, "Inception!!")
        print("clean_text trimming passed")

    def test_invalid_title_format(self):
        """Special characters beyond rule should be rejected."""
        self.assertFalse(app.valid("Mov!e@#?%*"))
        print(" invalid character rejection passed")

    def test_valid_title(self):
        """A proper movie title should return True."""
        self.assertTrue(app.valid("Harry Potter"))
        print(" valid title accepted")


"""This is validating whether the csv file is properly loaded or not"""
class TestCSVHandling(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = app.load_csv("books_movies.csv")

    def test_dataset_not_empty(self):
        """CSV file should load at least one movie."""
        self.assertGreater(len(self.dataset), 0)

    def test_movie_not_in_csv(self):
        """Unknown movie should return empty list before web fetch."""
        books = app.from_local("MovieThatDoesNotExist", self.dataset, minimum=4)
        self.assertEqual(len(books), 0)
        print(" handled unknown movie safely")


    def test_recommendation_limit(self):
        """Local recommendations should not exceed limit."""
        books = app.from_local("Inception", self.dataset, minimum=4)
        self.assertLessEqual(len(books), 4)
        print(" recommendation limit maintained")



"""This test cases validate whether book object is properly working or not"""
class TestBookModel(unittest.TestCase):

    def test_short_description_trim(self):
        """long text must shorten for clean console output."""
        text = "description " * 40
        b = app.Book("Demo", "Author", "Fiction", text, "csv")
        self.assertLess(len(b.short()), len(text))
        print(" description summary logic working")

    def test_book_attributes(self):
        """Book object should store data correctly."""
        b = app.Book("TestBook", "TestAuthor", "Drama", "Nice book", "csv")
        self.assertEqual(b.title, "TestBook")
        self.assertEqual(b.source, "csv")
        print(" book attributes stored properly")


"""This test case checks whether Database Setup is properly working or not"""
class TestDatabase(unittest.TestCase):

    def test_database_file_created(self):
        """project.db should generate automatically after init."""
        app.db_setup()
        self.assertTrue(os.path.exists("project.db"))
        print(" database setup confirmed")


"""It will run all the test cases"""
if __name__ == "__main__":
    print("\n Running Full Project Test Suite...\n")
    unittest.main(verbosity=2)
    print("\n All required test cases passed successfully.\n")
