import praw
import json
import os
from datetime import datetime, timedelta
import word_selection
from textblob import TextBlob  # sentiment analysis lib, still on the fence about that 
import time


import os
print(os.path.abspath(__file__))

class SafeRedditBot:
    def __init__(self, client_id, client_secret, username, password):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=f"DefinitionBot v1.0 by /u/{username}",
            username=username,
            password=password
        )
        self.bot_username = username
        
        # load or create tracking files 
        self.replied_posts_file = "replied_posts.json"
        self.replied_posts = self.load_replied_posts()
    
    # handy for avoiding duplicates as well as keeping a record 
        
    def load_replied_posts(self):
        if os.path.exists(self.replied_posts_file):
            with open(self.replied_posts_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_replied_posts(self):
        with open(self.replied_posts_file, 'w') as f:
            json.dump(list(self.replied_posts), f)
    
    # not sure about this one, may change/get rid:
    def has_negative_sentiment(self, text):
        blob = TextBlob(text)
        return blob.sentiment.polarity < -0.1  #  <--- threshold control
    
    def contains_keywords(self, text, keywords):
        """Check if text contains any of the specified keywords"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def should_reply_to_post(self, post, conditions=None):
        """Determine if we should reply to this post based on conditions"""
        
        # no self-replies plz
        if post['author'] == self.bot_username:
            print(f"Skipping own post: {post['id']}")
            return False
        
        # no double replies plz
        if post['id'] in self.replied_posts:
            print(f"Already replied to post: {post['id']}")
            return False
        
        # conditional filters (if/when provided)
        
        if conditions:
            # keywords:
            if 'required_keywords' in conditions:
                if not self.contains_keywords(post['text'], conditions['required_keywords']):
                    print(f"Post {post['id']} doesn't contain required keywords")
                    return False
            
            # sentiment:
            if conditions.get('only_negative_sentiment', False):
                if not self.has_negative_sentiment(post['text']):
                    print(f"Post {post['id']} doesn't have negative sentiment")
                    return False
            
            # sub:
            if 'allowed_subreddits' in conditions:
                if post['subreddit'] not in conditions['allowed_subreddits']:
                    print(f"Post {post['id']} not in allowed subreddits")
                    return False
        
        return True
    
    
    def get_posts(self, subreddit_names="AskReddit+explainlikeimfive", limit=10):
        subreddit = self.reddit.subreddit(subreddit_names)
        posts = []
        
        for submission in subreddit.new(limit=limit):
            # skipping empties
            if submission.selftext == '[deleted]' or submission.selftext == '[removed]':
                continue
                
            posts.append({
                'id': submission.id,
                'text': submission.title + " " + (submission.selftext or ""),
                'subreddit': submission.subreddit.display_name,
                'author': submission.author.name if submission.author else '[deleted]',
                'url': f"https://reddit.com{submission.permalink}",
                'score': submission.score,
                'num_comments': submission.num_comments
            })
        return posts
    
    def post_reply(self, post_id, reply_text, dry_run=False):
        
        if dry_run:
            print(f"DRY RUN - Would reply to {post_id}: {reply_text}")
            return True
        try:
            submission = self.reddit.submission(id=post_id)
            comment = submission.reply(reply_text)
            
            # track reply (to avoid dupes, etc)
            self.replied_posts.add(post_id)
            self.save_replied_posts()
            
            print(f"successfully replied to {post_id}")
            print(f"reply: {reply_text}")
            print(f"comment URL: https://reddit.com{comment.permalink}")
            return True
          
        except Exception as e:
            print(f"error posting reply to {post_id}: {e}")
            return False
    
    def run_one_shot(self, conditions=None, dry_run=True, max_replies=3):
        """runs the bot once, verbosely """
        print("=== REDDIT BOT ONE-SHOT RUN ===")
        print(f"Dry Run: {dry_run}")
        print(f"Max Replies: {max_replies}")
        
        if conditions:
            print(f"Conditions: {conditions}")
        
        posts = self.get_posts()
        print(f"\nFound {len(posts)} posts")
        
        replies_made = 0
        
        for i, post in enumerate(posts):
            if replies_made >= max_replies:
                print(f"\nReached max replies limit ({max_replies})")
                break
                
            print(f"\n--- Post {i+1}/{len(posts)} ---")
            print(f"Subreddit: r/{post['subreddit']}")
            print(f"Author: {post['author']}")
            print(f"Score: {post['score']}, Comments: {post['num_comments']}")
            print(f"Text: {post['text'][:200]}...")
            
            if not self.should_reply_to_post(post, conditions):
                continue
            
            word = word_selection(post['text'])
            if not word:
                print("No suitable word found")
                continue
            
            reply = self.compose_reply(word)
            print(f"\nProposed reply: {reply}")
            
            # confirmation for safety (not sure about this solution, but i think maybe it's better than nothing)
            if not dry_run:
                confirm = input("Post this reply? (y/n/q to quit): ").lower()
                if confirm == 'q':
                    break
                elif confirm != 'y':
                    continue
            
            success = self.post_reply(post['id'], reply, dry_run=dry_run)
            if success:
                replies_made += 1
                
                # rate limiting (30s wait between posts is nothing really, i reckon i might up that once it's tested so it's not too manic)
                if not dry_run and replies_made < max_replies:
                    print("waiting 30 seconds before next reply...")
                    time.sleep(30)
        
        print(f"\n=== RUN COMPLETE ===")
        print(f"Replies made: {replies_made}")
    
    def compose_reply(self, word):
        
        import random
        
        variations = {
            0: 'define ',
            1: 'first define ',
            2: 'well, how do you define ',
            3: 'how are you defining ',
            4: 'that depends on your definition of '
        }
        rando = random.choice(list(variations.keys()))
        return variations[rando] + f'"{word}"'



if __name__ == "__main__":
    # gotta initialize the bot first
    bot = SafeRedditBot(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET", 
        username="YOUR_BOT_USERNAME",
        password="YOUR_BOT_PASSWORD"
    )
    
    #  conditions (placeholder, will probably update/tweak)
    conditions = {
        'required_keywords': ['define', 'meaning', 'what is', 'explain'],
        'only_negative_sentiment': False,
        'allowed_subreddits': ['AskReddit', 'explainlikeimfive', 'NoStupidQuestions']
    }
    
    # run in dry-run mode first:
    bot.run_one_shot(conditions=conditions, dry_run=True, max_replies=3)
    
    # when ready, uncom and run 'for real':
    # bot.run_one_shot(conditions=conditions, dry_run=False, max_replies=1)