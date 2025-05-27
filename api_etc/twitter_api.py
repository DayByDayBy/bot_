import tweepy

# auth
auth = tweepy.OAuthHandler("API_KEY", "API_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")
api = tweepy.API(auth)

def get_posts(api_client):
    # get recent tweets (from TL)
    tweets = api_client.home_timeline(count=10)
    posts = []
    for tweet in tweets:
        posts.append({
            'id': tweet.id,
            'text': tweet.text,
            'user': tweet.user.screen_name
        })
    return posts

def post_reply(api_client, post_id, reply_text):
    api_client.update_status(
        status=reply_text,
        in_reply_to_status_id=post_id,
        auto_populate_reply_metadata=True
    )
    
    
    
    # twitter limting to 25 pcm on free tier (i think?) means this will be 
    # better employed once there are no other bugs to work out, so 
    # mistakes arent as impactful, as i am aware that as is it could easily 
    # be a full power firehose that runs dry in before it's even had a chance