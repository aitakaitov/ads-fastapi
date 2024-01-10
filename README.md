# FastAPI backend for advertisement detection

Download the ad detection model from https://drive.google.com/file/d/1qK2xAY4etLJ8pL6fphSwG77fdDo3VYbL/view?usp=sharing and put it in the root directory of the project

## Build and run

<code>docker compose up</code>

The server inside the container runs on <code>0.0.0.0:8001</code>.

See SwaggerDoc at <code>http://localhost:8001/docs#</code>

## Interface for entity highlighting
Entities are a list of dictionaries:
```python
[
    {
        # type of entity
        'type': str,
        # short text description
        'short_text': str,
        # list of relevant appearances to highlight
        'appearances':
        [
            {
                # which attribute identifies the start and end tags
                'attribute': str,
                # what value does the start tag have as the attribute above 
                'attr_start_value': str,
                # what value does the end tag have as the attribute above 
                'attr_end_value': str,
                # offset in characters from the beginning of the start tag
                'start_offset': int,
                # offset in characters from the beginning of the end tag
                'end_offset': int
            },
            ...
        ]
    },
    ...
]
```

`utils.html_utils.analyze_cookies` returns `(modified_html, entities)`, where the HTML is modified to include additional span tags, and entities is a list, which follows the interface described above.


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

