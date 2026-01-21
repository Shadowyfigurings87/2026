# ingestion/utils/scheduler.py

def run_weighted(generator, weight):
    for _ in range(weight):
        try:
            yield next(generator)
        except StopIteration:
            return
        except Exception:
            return
