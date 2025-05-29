import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile
from reddit_mono import SafeRedditBot


# never sure about the exact value of testing, but it def makes more sense when there are 
# rate limits involved, and having the tests will be handy when it comes to write the 
# twitter etc ones and can just refactor and work to the tests - TDD, etc

# finally giving in and using doc strings as if they aren't annoying; that may also change


class TestSafeRedditBot(unittest.TestCase):
    
    def setUp(self):
        """set up test fixtures before each test method"""
        # use temp file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        
        # mockup of the Reddit API
        with patch('reddit_mono.praw.Reddit'):
            self.bot = SafeRedditBot("test_id", "test_secret", "test_user", "test_pass")
            self.bot.replied_posts_file = self.temp_file.name
            self.bot.replied_posts = set()
    
    def tearDown(self):
        """tidy up after test"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_compose_reply(self):
        """test reply composer works correctly."""
        word = "algorithm"
        reply = self.bot.compose_reply(word)
        
        # should contain word in quotes
        self.assertIn('"algorithm"', reply)
        
        # should be an expected variation
        expected_starts = ['define', 'first define', 'well, how do you define', 
                          'how are you defining', 'that depends on your definition of']
        self.assertTrue(any(reply.startswith(start) for start in expected_starts))
    
    def test_load_save_replied_posts(self):
        """test loading and saving replied posts"""
        # starts empty
        self.assertEqual(len(self.bot.replied_posts), 0)
        
        # add posts and save
        self.bot.replied_posts.add("post1")
        self.bot.replied_posts.add("post2")
        self.bot.save_replied_posts()
        
        # new bot instance to check if data persists
        with patch('reddit_mono.praw.Reddit'):
            new_bot = SafeRedditBot("test_id", "test_secret", "test_user", "test_pass")
            new_bot.replied_posts_file = self.temp_file.name
            new_bot.replied_posts = new_bot.load_replied_posts()
        
        self.assertEqual(len(new_bot.replied_posts), 2)
        self.assertIn("post1", new_bot.replied_posts)
        self.assertIn("post2", new_bot.replied_posts)
    
    def test_has_negative_sentiment(self):
        """testing sentiment analysis."""
        positive_text = "I love this amazing wonderful day!"
        negative_text = "I hate this terrible awful situation."
        neutral_text = "The weather is okay today."
        
        self.assertFalse(self.bot.has_negative_sentiment(positive_text))
        self.assertTrue(self.bot.has_negative_sentiment(negative_text))
        self.assertFalse(self.bot.has_negative_sentiment(neutral_text))
    
    def test_contains_keywords(self):
        """testing keyword detection."""
        text = "Can someone please define algorithm for me?"
        keywords = ["define", "explain", "help"]
        
        self.assertTrue(self.bot.contains_keywords(text, keywords))
        self.assertFalse(self.bot.contains_keywords(text, ["random", "unrelated"]))
        
        # testing case-insensitivity 
        self.assertTrue(self.bot.contains_keywords("DEFINE this", ["define"]))
    
    def test_should_reply_to_post_basic(self):
        """Test basic post filtering."""
        # normal post should be accepted
        post = {
            'id': 'test123',
            'author': 'other_user',
            'text': 'What does algorithm mean?',
            'subreddit': 'AskReddit'
        }
        self.assertTrue(self.bot.should_reply_to_post(post))
        
        # self-post should be rejected
        own_post = {
            'id': 'test456',
            'author': 'test_user',
            'text': 'My own post',
            'subreddit': 'AskReddit'
        }
        self.assertFalse(self.bot.should_reply_to_post(own_post))
        
        # prev replied post should be rejected
        self.bot.replied_posts.add('test123')
        self.assertFalse(self.bot.should_reply_to_post(post))
    
    def test_should_reply_to_post_conditions(self):
        """Test conditional post filtering."""
        post = {
            'id': 'test789',
            'author': 'other_user',
            'text': 'Can you define justice please?',
            'subreddit': 'AskReddit'
        }
        
        # testing keyword filtering
        conditions = {'required_keywords': ['define', 'explain']}
        self.assertTrue(self.bot.should_reply_to_post(post, conditions))
        
        conditions = {'required_keywords': ['unrelated', 'keywords']}
        self.assertFalse(self.bot.should_reply_to_post(post, conditions))
        
        # testing subreddit filtering
        conditions = {'allowed_subreddits': ['AskReddit', 'explainlikeimfive']}
        self.assertTrue(self.bot.should_reply_to_post(post, conditions))
        
        conditions = {'allowed_subreddits': ['science', 'technology']}
        self.assertFalse(self.bot.should_reply_to_post(post, conditions))
    
    @patch('reddit_mono.word_selection')
    def test_get_posts_integration(self, mock_word_selection):
        """Test the get_posts method with mocked Reddit data."""
        # mock Reddit submission:
        mock_submission = Mock()
        mock_submission.id = 'test_post_1'
        mock_submission.title = 'What is machine learning?'
        mock_submission.selftext = 'I keep hearing about ML but don\'t understand it.'
        mock_submission.subreddit.display_name = 'AskReddit'
        mock_submission.author.name = 'curious_user'
        mock_submission.score = 10
        mock_submission.num_comments = 5
        mock_submission.permalink = '/r/AskReddit/comments/test/'
        
        # mock sub:
        mock_subreddit = Mock()
        mock_subreddit.new.return_value = [mock_submission]
        self.bot.reddit.subreddit.return_value = mock_subreddit
        
        posts = self.bot.get_posts(limit=1)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['id'], 'test_post_1')
        self.assertEqual(posts[0]['author'], 'curious_user')
        self.assertIn('machine learning', posts[0]['text'])
    
    def test_post_reply_dry_run(self):
        """testing dry run mode"""
        success = self.bot.post_reply('test_post', 'define "test"', dry_run=True)
        self.assertTrue(success)
        
        # shouldn't add to replied posts in dry run
        self.assertNotIn('test_post', self.bot.replied_posts)

class TestWordSelection(unittest.TestCase):
    """testing word selection functionality."""
    
    @patch('reddit_mono.word_selection')
    def test_word_selection_called(self, mock_word_selection):
        """testing word selection is called with post text."""
        mock_word_selection.return_value = "algorithm"
        
        with patch('reddit_mono.praw.Reddit'):
            bot = SafeRedditBot("test_id", "test_secret", "test_user", "test_pass")
        
        text = "what is an algorithm in programming?"
        result = mock_word_selection(text)
        
        self.assertEqual(result, "algorithm")

if __name__ == '__main__':
    unittest.main(verbosity=2)
    
    
    


    
    
    
# for not-main running, ie using it as a module, etc:

# suite = unittest.TestLoader().loadTestsFromTestCase(TestSafeRedditBot)
# unittest.TextTestRunner(verbosity=2).run(suite)