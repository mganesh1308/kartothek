import pytest

from .utils import create_dataset


@pytest.fixture()
def bound_delete_dataset():
    raise NotImplementedError("Must be implemented by backend")


def test_delete_dataset(store_factory, metadata_version, bound_delete_dataset):
    """
    Ensure that a dataset can be deleted
    """
    create_dataset("dataset", store_factory, metadata_version)

    store = store_factory()
    assert len(list(store.keys())) > 0
    bound_delete_dataset("dataset", store_factory)
    assert len(list(store.keys())) == 0


def _test_gc(uuid, store_factory, garbage_collect_callable):
    store = store_factory()

    keys_before = set(store.keys())

    # Add a non-tracked table file
    store.put("{}/core/trash.parquet".format(uuid), b"trash")

    # Add a non-tracked index file
    store.put("{}/indices/trash.parquet".format(uuid), b"trash")

    garbage_collect_callable(uuid, store_factory)

    keys_after = set(store.keys())
    assert keys_before == keys_after


def test_gc_delete_dataset(
    store_factory, metadata_version, bound_delete_dataset, garbage_collect_callable
):
    """
    Ensure that a dataset can be deleted
    """
    create_dataset("dataset", store_factory, metadata_version)

    _test_gc("dataset", store_factory, garbage_collect_callable)

    store = store_factory()
    assert len(list(store.keys())) > 0
    bound_delete_dataset("dataset", store_factory)
    assert len(list(store.keys())) == 0


def test_delete_single_dataset(store_factory, metadata_version, bound_delete_dataset):
    """
    Ensure that only the specified dataset is deleted
    """
    create_dataset("dataset", store_factory, metadata_version)
    create_dataset("another_dataset", store_factory, metadata_version)
    store = store_factory()
    amount_of_keys = len(list(store.keys()))
    assert len(list(store.keys())) > 0
    bound_delete_dataset("dataset", store_factory)
    assert len(list(store.keys())) == amount_of_keys / 2, store.keys()


def test_delete_only_dataset(store_factory, metadata_version, bound_delete_dataset):
    """
    Ensure that files including the UUID but not starting with it
    are not deleted
    """
    create_dataset("UUID", store_factory, metadata_version)

    store = store_factory()
    store.put(key="prefixUUID", data=b"")
    bound_delete_dataset("UUID", store_factory)
    assert "prefixUUID" in store.keys()


def test_delete_missing_dataset(store_factory, store_factory2, bound_delete_dataset):
    """
    Ensure that a dataset can be deleted even though some keys are already removed.
    """
    metadata_version = 4
    create_dataset("dataset", store_factory, metadata_version)

    store = store_factory()
    keys = sorted(store.keys())
    assert len(keys) > 0

    store2 = store_factory2()

    for missing in keys:
        if missing == "dataset.by-dataset-metadata.json":
            continue

        for k in keys:
            if k != missing:
                store2.put(k, store.get(k))

        bound_delete_dataset("dataset", store_factory2)
        assert len(list(store2.keys())) == 0
