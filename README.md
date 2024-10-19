# Project overview
this project owns simple FASTApi app serves as a proxy to elevenlabs.

## Important notes
- this api has rating limit for 20 requests per minute
- only three synchronous requests per user can be handled

## Project structure
- main.py in root directory serves as api (view) layer
- package core obtains core (controller) layer
- package store obtains database layer
- package exceptions obtains special case exceptions

## Tools
- poetry is used for dependency management and mypy for code checks. Black was used for formatting

## How to run
- run `poetry run python main.py` for api to start
- run `poetry run pytest --verbose` for tests

## Limitations
- Although using mypy this method fails on main.py. This could be handled with project restructuralization
- There is only one test that covers three synchronous requests per user functionality. More tests should be written for better coverage.
- `store` layer contains only in memory and very unsafe database. 
- Api includes only basic auth. More secure ways should be used.
- `main.py` is just ok for this small app, but for bigger api it should be decomposed into `api` layer and main function
- `store` lock locks all users for any operation. For bigger app the lock should be per user or replaced by more sophisticated solution
- Holding multiple semaphores could be memory hungry. For bigger project this logic should be reworked. Ideally rewritten into Go that is best tool for such cases.