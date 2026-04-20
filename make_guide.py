import json
from pathlib import Path

replies = json.loads(Path('samples/reddit_replies.json').read_text())

lines = [
    '# Reddit Manual Posting Guide',
    '',
    'For each reply below: open the post link, click Add a comment, paste the reply, submit, then save your comment URL.',
    '',
    '---',
    '',
]

for i, r in enumerate(replies, 1):
    subreddit = r.get('subreddit', '')
    title = r.get('post_title', '')
    url = r.get('post_url', '')
    score = r.get('relevance_score', 0)
    reply_text = r.get('reply_text', '')

    lines += [
        f'## Reply {i} — r/{subreddit}',
        '',
        f'**Post title:** {title}',
        f'**Post URL:** {url}',
        f'**Relevance score:** {score}/10',
        '',
        '**Copy and paste this reply:**',
        '',
        reply_text,
        '',
        'Your comment URL after posting: ___________________________',
        '',
        '---',
        '',
    ]

lines += [
    '## Submission notes',
    '',
    'Include all 5 comment URLs in your email to gilad@crowdwisdomtrading.com',
    'A comment URL looks like: https://www.reddit.com/r/Daytrading/comments/abc123/title/xyz789/',
]

output = '\n'.join(lines)
Path('output/manual_posting_guide.md').write_text(output, encoding='utf-8')
print(f'Done! Created output/manual_posting_guide.md with {len(replies)} replies')