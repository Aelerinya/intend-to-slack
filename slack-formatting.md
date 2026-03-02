# Slack mrkdwn Formatting Reference

Slack uses "mrkdwn" (not markdown). Key differences from standard markdown.

## Text Styles

| Format        | Syntax    | Example              |
|---------------|-----------|----------------------|
| Bold          | `*text*`  | *bold text*          |
| Italic        | `_text_`  | _italic text_        |
| Strikethrough | `~text~`  | ~struck through~     |
| Inline code   | `` `text` `` | `code`            |

## No Headers

Slack does NOT support `#`, `##`, etc. Use bold text instead:
```
*Section Title*
```

## Line Breaks

Use literal `\n` in strings:
```
Line one\nLine two
```

## Lists

No special syntax. Use bullet characters with newlines:
```
• Item one\n• Item two
```

Or dashes:
```
- Item one\n- Item two
```

## Block Quotes

Prefix with `>`:
```
>Quoted text
```

## Code Blocks

Triple backticks:
```
```code here```
```

## Links

```
<https://example.com|Display Text>
```

## Source

https://docs.slack.dev/messaging/formatting-message-text
