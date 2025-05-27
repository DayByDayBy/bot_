import praw

# reddit instance (this is how praw does it)
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="DefinitionBot v1.0 by /u/yourusername",
    username="your_bot_username",
    password="your_bot_password"
)

def get_posts(api_client):
    # specific subreddits (not final list, just using big/popular ones as placeholders)
    subreddit = api_client.subreddit("AskReddit+explainlikeimfive")  # string can basically be endless
    posts = []
    
    for submission in subreddit.new(limit=10):
        posts.append({
            'id': submission.id,
            'text': submission.title + " " + submission.selftext,
            'subreddit': submission.subreddit.display_name,
            'url': submission.url
        })
    return posts

def post_reply(api_client, post_id, reply_text):
    submission = api_client.submission(id=post_id)
    submission.reply(reply_text)
    
    
# cobbled together from boilerplate etc and looks fine, but i think it needs some 
# work to be interesting
# 
# a better selection of subs, yes, but also i think i neeed to add a more nuanced 
# logic for selecting/filtering posts, and maybe a selection of trigger phrases without 
# which no replies will be posted