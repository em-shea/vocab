# Daily Chinese Vocab

A serverless app that sends a Chinese word and link to example sentences at the user's Chinese level as a daily email message.

Chinese learners can subscribe to daily vocab words to build their vocabulary. The vocabulary by level (1-6) is from the Hanyu Shuiping Kaoshi (HSK), China's standardized Mandarin testing levels. 

To subscribe, visit https://haohaotiantian.com, where you can preview sample words for each level and learn more about the daily emails.

## Example message

![Example message](https://emshea.com/static/images/chinese-vocab-app/haohaotiantian-email-640.PNG)

## Architecture

You can read about the development process and architecture here: https://emshea.com/post/chinese-vocab-app

![Architectural diagram](https://emshea.com/static/images/chinese-vocab-app/vocab-app-v3-640.PNG)

[Frontend repo](https://github.com/em-shea/vocab-frontend)

## Roadmap

| Roadmap item  | Status |
| ------------- | :-------------: |
| Write daily words to DynamoDB table | :heavy_check_mark:  |
| Create API to serve daily word history | :heavy_check_mark:  |
| Refactor homepage to Vue | :soon: |
| Build interface for users to explore and export word history | :heavy_check_mark: |
| Build interface for quizzes | |
| Add links to word history and quizzes to daily email message | |
| Add word audio support for email and website | |
