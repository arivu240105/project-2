# FastAPI Documentation - Introduction & Basics

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints.

## Key Features

- **Fast**: Very high performance, on par with NodeJS and Go (thanks to Starlette and Pydantic). One of the fastest Python frameworks available.
- **Fast to code**: Increase the speed to develop features by about 200% to 300%.
- **Fewer bugs**: Reduce about 40% of developer induced errors.
- **Intuitive**: Great editor support. Completion everywhere. Less time debugging.
- **Easy**: Designed to be easy to use and learn. Less time reading documentation.
- **Short**: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.
- **Robust**: Get production-ready code. With automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible with) the open standards for APIs: OpenAPI (previously known as Swagger) and JSON Schema.

## Simple Example

Create a file `main.py` with:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

Run the live server using Uvicorn:

```bash
uvicorn main:app --reload
```

## Dependency Injection (DI)

FastAPI has a very powerful and intuitive **Dependency Injection** system. It is designed to be very easy to use, and make it easy for any developer to integrate other components.

In FastAPI, a dependency is simply a callable (like a function or a class) that FastAPI knows how to execute and inject results into your path operations.

Example:

```python
from fastapi import Depends, FastAPI

app = FastAPI()


async def common_parameters(q: str = None, skip: int = 0, limit: int = 10):
    return {"q": q, "skip": skip, "limit": limit}


@st.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons
```
 **Fast**: Very high performance, on par with NodeJS and Go (thanks to Starlette and Pydantic). One of the fastest Python frameworks available.
- **Fast to code**: Increase the speed to develop features by about 200% to 300%.
- **Fewer bugs**: Reduce about 40% of developer induced errors.
- **Intuitive**: Great editor support. Completion everywhere. Less time debugging.
- **Easy**: Designed to be easy to use and learn. Less time reading documentation.
- **Short**: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.
- **Robust**: Get production-ready code. With automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible w
Using `Depends(common_parameters)` tells FastAPI to execute `common_parameters` and inject its return value into the `commons` parameter of the path operation.
This reduces code duplication and makes database connection sessions or authentication checks easy to write and share.
