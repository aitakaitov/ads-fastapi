# FastAPI backend for advertisement detection

Download the ad detection model from https://drive.google.com/file/d/1qK2xAY4etLJ8pL6fphSwG77fdDo3VYbL/view?usp=sharing and put it in the root directory of the project

## Build and run

<code>docker compose up</code>

The server inside the container runs on <code>0.0.0.0:8001</code>.

See SwaggerDoc at <code>http://localhost:8001/docs#</code>

## API for entity extraction
* `utils.html_utils.analyze_cookies(html: str)` takes HTML code as input.
* it then calls `process_for_extraction(html: str)`, which returns
```python
[
    {
        # element id
        'id': int,
        # element text
        'text': str,
        # element tag - "p", "h1-6"
        'tag': str
    }
]
```
* it passes this array to the extractor and expects a list of entity info
```python
[
    {
        # extracted entity
        'short_text': str,
        # entity context
        'context_tokens': list[str],
        # element id
        'id': 0,
        # what entity
        'type': 'first'
    }
]
```

