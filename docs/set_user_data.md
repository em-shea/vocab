# Set user data API

The set user data function is a POST method at api.haohaotiantian.com/update_user.
This endpoint updates user metadata (user alias, character set preference) for a user authenticated through Cognito.

Example payload:
````
{
    'user_alias': '小王',
    'user_alias_pinyin': 'xiǎo wáng',
    'user_alias_emoji': '📙',
    'character_set_preference': 'traditional'
}
````