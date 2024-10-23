# How to...

## Build this package

```bash
python -m build
```

Running this command will generate new `.whl` and `.tar.gz` files in the `dist` directory.

## Install this package

```bash
pip install pip install dist/ib_async_trader-0.0.1-py3-none-any.whl --force-reinstall
```

Running this command in the desired installation location will install the updated wheel.

## Run the tests

This package uses `pytest` for testing.  Running this command will run all tests in the `tests` directory.

```bash
pytest tests/
```